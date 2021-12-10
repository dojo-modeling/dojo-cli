"""
  Dojo-cli client for dojo api.
"""

from dojocli.docker_client import DockerClient
from datetime import datetime
from jinja2 import Template
import json
import os
import re
import requests

# Image query parameter for /models e.g. "jataware/dojo" below
# url = f'{self.dojo_url}/models?query=image:"jataware/dojo" AND NOT _exists_:"next_version"&size=1000'
IMAGE_QUERY_NAME = "jataware" #"jataware/dojo"

class DojoClient(object):

    def __init__(self, config_filename):
        self.set_config(config_filename)

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

    def get_metadata(self, model_id: str):
        """
        Description
        -----------
        Calls /dojo endpoints to download model metadata e.g. directive, config, 
        outputfiles, and accessory files.

        Process
        -------
        (1) use the model_id to call GET /dojo/ endpoints to get the directive,
        outputfiles, accessories and config.

        (2) return these as a dict.

        Parameters
        ----------
        model_id: str
            The id of the model of interest.

        Returns
        -------
            dict: metadata as JSON

        """

        # Get "dojo_stuff", i.e. the four types of information available by GET
        # /dojo/, and add to the metadata.
        metadata = {}
        dojo_stuff = ['accessories', 'config', 'directive', 'outputfile']
        for stuff in dojo_stuff:
            metadata[stuff] = self.get_dojo_stuff(stuff, model_id)
        
        return metadata

    def get_model_info(self, model_name: str):
        """
        Description
        -----------
        Return model JSON for a model_name. 
        
        Parameters
        ---------
        
        model_name: str
            The name of the model.
            
        Returns
        -------
            
        dict
        
        """

        url = f'{self.dojo_url}/models?query=name:"{model_name}" AND image:"{IMAGE_QUERY_NAME}" AND NOT _exists_:"next_version"'
        response = self.generic_dojo_get_request(url)
        try:
            resp = response.json()

            for r in resp["results"]:
                if r["name"] == model_name:
                    return r

        except Exception as e:
            if hasattr(e, 'message'):
                print(e.message)
            else:
                print(e)
            exit
        
    def get_outputfiles(self, model_id: str):
        """
        Description
        -----------
        Call dojo endpoint /outputfile to get model outputfile metadata.

        Returns
        -------
        dict of JSON payload of api call.

        """

        return self.get_dojo_stuff('outputfile', model_id)
        
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
        datetimestamp = datetime.today().strftime("%Y%m%d%H%M%S")
        if local_output_folder == None:
            local_output_folder = f'{os.getcwd()}/runs/{model_name}/{datetimestamp}'
        
        # Create directory structure.
        os.makedirs(local_output_folder)

        # Get the model_id from the model_name
        model_dict = self.get_model_info(model_name)
        model_id = model_dict["id"]
        image_name = model_dict["image"]

        # Get the metadata for this model. 
        metadata = self.get_metadata(model_id)
        
        ### Begin building the array of volume mounts.
        volume_array = []

        # We have to be careful since we cannot mount the same directory (within the model container) more than once
        # so if multiple output files reside in the same directory (which is common), we need to re-use that volume mount
        output_dirs = set()

        # Process output file locations.
        outputfiles = metadata["outputfile"]
        for output in outputfiles:
            # Build a volume mount for this output file's directory.
            output_dir = output['output_directory']
            #output_id = output['id']

            if output_dir not in output_dirs:
                #output_dirs[output_dir] = output_id
                output_dirs.add(output_dir)
                # Use the lookup to build the path.
                #output_dir_volume = local_output_folder + f"/{output_dirs[output_dir]}:{output_dir}"
                output_dir_volume = local_output_folder + f"/output:{output_dir}"               
                # Add it to the volume_array
                volume_array.append(output_dir_volume)

        # Process accessory file locations.
        accessory_files = metadata["accessories"]
        accessory_dirs = {}
        accessory_captions = {}
        for accessory_file in accessory_files:
            # Build a volume mount for this accessory file's directory.
            accessory_dir, accesssory_filename = os.path.split(accessory_file['path'])

            # Capture accessory file captions so they can be written to file.
            if "caption" in accessory_file:
                accessory_captions[accesssory_filename] = accessory_file["caption"]
            
            accessory_id = accessory_file['id']

            if accessory_dir not in accessory_dirs:
                accessory_dirs[accessory_dir] = accessory_id
                # Use the lookup to build the path.
                accessory_dir_volume = local_output_folder + f"/accessories:{accessory_dir}"
                volume_array.append(accessory_dir_volume)

        # Set run command from metadata["directive"]["command"] and substitute params.
        if params == None:
            # If params json not passed then read from file.
            with open(params_filename, "r") as fh:
                params = json.load(fh)
        elif isinstance(params, str):
            # If params was passed in the command line it is a str; convert to dict.
            params = json.loads(params)

        # Write the parameters used out to the run result directory.
        with open(f'{local_output_folder}/run-parameters.json', 'w') as fh:
            json.dump(params, fh, indent=4)

        # Write accessory file captions to the run result directory.
        if len(accessory_captions) > 0:
            with open(f'{local_output_folder}/accessories-captions.json', 'w') as fh:
                json.dump(accessory_captions, fh, indent=4)

        model_command = Template(metadata["directive"]["command"])
        model_command = model_command.render(params)

        dc = DockerClient()
        
        # Pull the image
        print(f'Getting model image ...\n')
        dc.pull_image(image_name)

        # create the container
        container_name = re.sub("[ ]", '', model_name.lower() ).strip() + datetimestamp

        print(f"Creating container {container_name} with volume_array {volume_array}\n")
        
        container_name = dc.create_container(image_name, volume_array, container_name)
        
        # Work around for following:
        # the volume_array output folders in the docker container are owned by root, not clouseau.
        for v in volume_array:
            sa = v.split(":")
            folder = sa[1]
            dc.execute_command(f'sudo chown clouseau:clouseau {folder}')

        # Execute the model_command.
        dc.execute_command(model_command)

        print(f"\nCreated container {container_name}.")
        print(f"\nModel output and run-parameters files are located in {local_output_folder}.")

        
    def set_config(self, config_filename):
        with open(config_filename) as f:
            config = json.load(f)

            # Set dojo url and authentication credentials.
            self.dojo_auth = (config["DOJO_USER"], config["DOJO_PWD"]) 
            self.dojo_url = config["DOJO_URL"]
            

