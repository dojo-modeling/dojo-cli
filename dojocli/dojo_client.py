"""
  Dojo-cli client for dojo api.
"""

from docker_client import DockerClient
from datetime import datetime
from jinja2 import Template
import json
import os
import requests

# Image query parameter for /models e.g. "jataware/dojo" below
# url = f'{self.dojo_url}/models?query=image:"jataware/dojo" AND NOT _exists_:"next_version"&size=1000'
IMAGE_QUERY_NAME = "jataware" #"jataware/dojo"

class DojoClient(object):

    def __init__(self, config_filename):
        self.set_config(config_filename)
        self.image_name = None
        self.model_id = None

    def generic_dojo_get_request(self, url):
        try:
            response = requests.get(url, auth=(self.dojo_auth))
            return response
        except Exception as e:
            if hasattr(e, 'message'):
                print(e.message)
            else:
                print(e)
            exit

    def get_available_models(self):
        """
        Description
        -----------

            Get latest models with images from dojo api.

            Use /models and not models/latest so that images can be restricted to 
            jataware/dojo-publish.

        """
        url = f'{self.dojo_url}/models?query=image:"{IMAGE_QUERY_NAME}" AND NOT _exists_:"next_version"&size=1000'
        response = self.generic_dojo_get_request(url)
        try:
            resp = response.json()
            models = set()
            for r in resp["results"]:
                if r['image'] != '' and r['next_version'] == None:
                    models.add(r['name'])

            models = list(models)
            models.sort()
            return models
        except Exception as e:
            if hasattr(e, 'message'):
                print(e.message + '\n' + response.text)
            else:
                print(response.text)
            exit

    def get_dojo_stuff(self, stuff, model_id):
        """
            Get stuff(config, directive, accessories, outputfiles) based on model_id.
        """

        url = f'{self.dojo_url}/dojo/{stuff}/{model_id}'
        response = self.generic_dojo_get_request(url)
        try:
            return response.json()
        except Exception as e:
            if hasattr(e, 'message'):
                print(e.message)
            else:
                print(e)
            exit

    def get_metadata(self, model_name: str):
        """
        Description
        -----------
        Calls /dojo endpoints to download model metadata e.g. directive, config, 
        outputfiles, and accessory files.

        Process
        -------
        (1) take the model name and calls GET /models/latest to 
        find the model_id.

        (2) use the model_id to call GET /dojo/ endpoints to get the directive,
        outputfiles, accessories and config.

        (3) return these as json.

        Parameters
        ----------
        model_name: str
            The name of the model of interest.

        Returns
        -------
            dict: metadata as JSON

        """

        # Get the model_id from the model_name
        self.model_id, self.image_name = self.get_model_info(model_name)
        print(f"Model id for {model_name} is {self.model_id}")

        # Get "dojo_stuff", i.e. the four types of information available by GET
        # /dojo/, and add to the metadata.
        metadata = {}
        dojo_stuff = ['accessories', 'config', 'directive', 'outputfile']
        for stuff in dojo_stuff:
            metadata[stuff] = self.get_dojo_stuff(stuff, self.model_id)
        
        return metadata

    def get_model_info(self, model_name: str):
        """
            Get the model_id and image_name based on the model_name. 
            Restrict query to models with a jataware image and "next_version":null.

        Returns
        -------
            tuple: (model_id, image_name)
        """

        url = f'{self.dojo_url}/models?query=name:"{model_name}" AND image:"{IMAGE_QUERY_NAME}" AND NOT _exists_:"next_version"'
        response = self.generic_dojo_get_request(url)
        try:
            resp = response.json()

            # TODO: multiple hits for the latest model_name: the image appears to be same, though.
            print(resp["hits"], ' get_model_id() hits')
            for r in resp["results"]:
                print(r["image"])

            for r in resp["results"]:
                if r["name"] == model_name:
                    return (r["id"], r["image"])

        except Exception as e:
            if hasattr(e, 'message'):
                print(e.message)
            else:
                print(e)
            exit
        
    def run_model(self, model_name: str, params: str = None, params_filename: str = None, local_output_folder: str = None):
        """
        Description
        -----------
            Runs the selected model. Gets metadata from the dojo api, builds
            the volume mounts, and uses docker_client.py to download and run
            the image. Finally, it executes the model directive.

        Parameters
        ----------
            model_name: str
                Name of the model to run e.g. CHIRPS-Monthly
            
            params: str
                JSON of model parameters.

            params_filename: str
                If params if not passed, model parameters JSON is loaded from this file.

            local_output_folder: str
                Local folder where model output is written.

        """

        # Use default folder if not specified.
        if local_output_folder == None:
            local_output_folder = f'{os.getcwd()}/runs/{model_name}/{datetime.today().strftime("%Y%M%d%H%M%S")}'
        
        # Create directory structure.
        os.makedirs(local_output_folder)

        # Get the metadata for this model. This sets self.image_name.
        metadata = self.get_metadata(model_name)
        
        ### Begin building the array of volume mounts.
        volume_array = []

        # we have to be careful since we cannot mount the same directory (within the model container) more than once
        # so if multiple output files reside in the same directory (which is common), we need to re-use that volume mount
        output_dirs = {}

        # Process output file locations.
        outputfiles = metadata["outputfile"]
        for output in outputfiles:
            # build a volume mount for this output file's directory
            output_dir = output['output_directory']
            output_id = output['id']

            
            if output_dir not in output_dirs:
                output_dirs[output_dir] = output_id

            # use the lookup to build the path
            output_dir_volume = local_output_folder + f"/{output_dirs[output_dir]}:{output_dir}"               
            #print('output_dir_volume:' + output_dir_volume)

            # add it to the volume_array
            volume_array.append(output_dir_volume)

        # Process accessory file locations.
        accessory_files = metadata["accessories"]
        accessory_dirs = {}
        for accessory_file in accessory_files:
            # build a volume mount for this accessory file's directory
            accessory_dir = os.path.split(accessory_file['path'])[0] #exclude file name
            accessory_id = accessory_file['id']

            if accessory_dir not in accessory_dirs:
                accessory_dirs[accessory_dir] = accessory_id

                # use the lookup to build the path
                accessory_dir_volume = local_output_folder + f"/accessories:{accessory_dir}"
                volume_array.append(accessory_dir_volume)

        # Set run command from metadata["directive"]["command"] and substitute params.
        if params == None:
            # If params json not passed then read from file.
            with open(params_filename, "r") as fh:
                params = json.load(fh)

        model_command = Template(metadata["directive"]["command"])
        model_command = model_command.render(params)

        dc = DockerClient(self.dockerhub_user, self.dockerhub_pwd)
        
        # Pull the image
        dc.pull_image(self.image_name)

        # create the container
        container_name = dc.create_container(self.image_name, volume_array)
        print(f"Created container {container_name} with volumne_array {volume_array}")

        # Work around for following:
        # the volume_array output folders in the docker container are owned by root, not clouseau.
        for v in volume_array:
            sa = v.split(":")
            folder = sa[1]
            dc.execute_command(f'sudo chown clouseau:clouseau {folder}')

        # Execute the model_command.
        dc.execute_command(model_command)
        
    def set_config(self, config_filename):
        with open(config_filename) as f:
            config = json.load(f)

            # Set dojo url and authentication credentials.
            self.dojo_auth = (config["DOJO_USER"], config["DOJO_PWD"]) 
            self.dojo_url = config["DOJO_URL"]
            
            # Set DockerHub url and credentials.
            self.dockerhub_pwd = config["DOCKERHUB_PWD"]
            self.dockerhub_user = config["DOCKERHUB_USER"]

    def test_docker(self):
        dc = DockerClient(self.dockerhub_user, self.dockerhub_pwd)
        #dc.pull_image('jataware/dojo-publish', 'CHIRPS-Monthly-latest')
        dc.list_system_images()