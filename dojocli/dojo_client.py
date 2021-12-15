"""
  Dojo-cli client for dojo api.
"""

from datetime import datetime
from dojocli.docker_client import DockerClient
from jinja2 import Template
import json
import os
import re
import requests

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
        #url = f'{self.dojo_url}/models?query=image:"{IMAGE_QUERY_NAME}" AND NOT _exists_:"next_version"&size=1000'
        url = f'{self.dojo_url}/models/latest?size=1000'
        response = self.generic_dojo_get_request(url)

        try:
            resp = response.json()
            print(resp["hits"])
            models = set()
            for r in resp["results"]:
                if r['image'] != '' and r['next_version'] == None:
                    models.add(f"\"{r['name']}\"")
                #elif r["image"] == '':
                #    pass#print(f"\"{r['name']}\"", r["image"], r["id"])
                #else:
                #    print(f"\"{r['name']}\"", r["image"], r["id"])  
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

    def get_model_info(self, model_name: str, model_id: str = None):
        """
        Description
        -----------
        Return model JSON for a model_name. 
        
        Parameters
        ---------
        
        model_name: str
            The name of the model.
        model_id: str
            The optional model_id of the model passed as version. This overrides
            the search by model_name.
            
        Returns
        -------
            
        dict
        
        """

        #url = f'{self.dojo_url}/models?query=name:"{model_name}" AND image:"{IMAGE_QUERY_NAME}" AND NOT _exists_:"next_version"'
        if model_id == None:
            url = f'{self.dojo_url}/models/latest?query=name:"{model_name}"'
        else:
            url = f'{self.dojo_url}/models/{model_id}'
        
        response = self.generic_dojo_get_request(url)

        try:
            resp = response.json()

            if "results" in resp:
                # /models/latest returns a list of model objects in "results"
                for r in resp["results"]:
                    if (r["name"] == model_name or r["id"] == model_id):
                        return r
            elif ("name" in resp and "id" in resp):
                # models/{model_id} returns a single model object
                if (resp["name"] == model_name or resp["id"] == model_id):
                    return resp

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
        
    def get_versions(self, model_name: str):
        """
        Description
        -----------
        Return a versions info for the model.
        
        Parameters
        ---------
        
        model_name: str
            The name of the model.
            
        Returns
        -------
            
        JSON Response Body
            {
                "current_version": "21fe6a15-f0a5-4ea3-a813-1e33d37f948d",
                "prev_versions": [],
                "later_versions": []
            }
        
        """

        # (1) Get the model_id of the latest version.
        model_dict = self.get_model_info(model_name)
        model_id = model_dict["id"]

        # (2) Call dojo /models/{model_id}/versions
        url = f'{self.dojo_url}/models/{model_id}/versions'
        response = self.generic_dojo_get_request(url)
        try:
            return response.json()

        except Exception as e:
            if hasattr(e, 'message'):
                print(e.message)
            else:
                print(e)
            exit

    def run_model(self, model_name: str, params: str = None, params_filename: str = None, version: str = None, 
        local_output_folder: str = None, run_attached: bool = True):
        """
        Description
        -----------
            Runs the selected model or model_id. Gets metadata from the dojo api, builds
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

            version: str = None
                The specific model_id (or "version") to run. Overrides model_name.

            local_output_folder: str
                Local folder where model output is written.

            run_attached: bool = True
                Option to run the model detached (in background.)

        """

        # Use default folder if not specified.
        datetimestamp = datetime.today().strftime("%Y%m%d%H%M%S")
        if local_output_folder == None:

            local_output_folder = f'{os.getcwd()}/runs/{model_name if model_name is not None else version}/{datetimestamp}'
        
        # Create directory structure.
        os.makedirs(local_output_folder)

        # Get the model_id and image from the model_name or version.
        model_dict = self.get_model_info(model_name, model_id=version)
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

        
        # Instantiate the Docker Client.
        dc = DockerClient()
        
        # Pull the image
        print(f'Getting model image ...\n')
        dc.pull_image(image_name)

        # Begin constructing the command to pass when running the container.
        container_command = 'bash -c "'

        # Work around for following:
        # the volume_array output folders in the docker container are owned by root, not clouseau.
        # Add these chown commands to the container_command.
        for v in volume_array:
            sa = v.split(":")
            folder = sa[1]
            container_command = container_command + f'sudo chown clouseau:clouseau {folder} && '

        # Add the model_command with a trailing quote (") to the container command.
        model_command = Template(metadata["directive"]["command"])
        model_command = model_command.render(params)
        container_command = container_command + f'{model_command}"'
        
        # Create the container name.
        if model_name is None:
            container_name = version[-12:] + datetimestamp
        else:
            container_name = re.sub("[ \]\[,()_]", '', model_name.lower() ).strip() + datetimestamp

        # TODO: better explanations here.
        if run_attached:
            print(f"\nRunning model in Docker container {container_name} ... \n")
            print(f"the model is running attached ... ")

            # Run the container.
            logs = dc.create_container(image_name, volume_array, container_name, container_command)
            
            # Write the logs returned from the attached container.
            with open(f'{local_output_folder}/logs.txt', 'w') as fh:
                fh.writelines(logs)

        else:
            print(f"the model is running deattached ... ")
        
            # Run the container.
            dc.create_container(image_name, volume_array, container_name, container_command, runattached=False)
            
            # Write the logs, but these will probably be incomplete for the detached container.
            logs = dc.get_logs(container_name)
            with open(f'{local_output_folder}/logs.txt', 'wb') as fh:
                fh.write(logs)

        # Remove the container if running attached. Autoremove = False because 
        # the logs aren't streaming.
        #if run_attached:
        #    dc.remove_container(container_name)

        print(f"\nModel output, run-parameters, and log files are located in {local_output_folder}.")

    def set_config(self, config_filename):
        with open(config_filename) as f:
            config = json.load(f)

            if ("DOJO_USER" not in config or 
                "DOJO_URL" not in config or
                "DOJO_PWD" not in config):
                print(f'{config_filename} is missing a required field of DOJO_USER, DOJO_URL, and/or DOJO_PWD.')
                return

            # Set dojo url and authentication credentials.
            self.dojo_auth = (config["DOJO_USER"], config["DOJO_PWD"]) 
            self.dojo_url = config["DOJO_URL"]
            

