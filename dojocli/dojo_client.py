"""
  Dojo-cli client for dojo api.
"""

from docker_client import DockerClient
import json
import requests

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

        url = f'{self.dojo_url}/models?query=image:"jataware/dojo" AND NOT _exists_:"next_version"&size=1000'
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
                print(e + '\n' + response.text)
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

    def get_model_info(self, model_name):
        """
            Get the model_id and image_name based on the model_name. 
            Restrict query to models with a jataware image and "next_version":null.

        Returns
        -------
            tuple: (model_id, image_name)
        """

        url = f'{self.dojo_url}/models?query=name:"{model_name}" AND image:"jataware/dojo" AND NOT _exists_:"next_version"'
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

    def run_model(self, model_name, params_filename):

        # Get the metadata for this model. This sets self.image_name.
        metadata = self.get_metadata(model_name)
        params = self.set_run_params(params_filename)

        # set run command from metadata["directive"]["command"] and substitute params.

        dc = DockerClient(self.dockerhub_user, self.dockerhub_pwd)
        
        # pull the image
        dc.pull_image(self.image_name)

        # create the container
        container_name = dc.create_container(self.image_name)
        print(f"Created container {container_name}")

        


        

    def set_config(self, config_filename):
        with open(config_filename) as f:
            config = json.load(f)

            # Set dojo url and authentication credentials.
            self.dojo_auth = (config["DOJO_USER"], config["DOJO_PWD"]) 
            self.dojo_url = config["DOJO_URL"]
            
            # Set DockerHub url and credentials.
            self.dockerhub_pwd = config["DOCKERHUB_PWD"]
            self.dockerhub_user = config["DOCKERHUB_USER"]

    def set_run_params(self, params_filename):
        params = {}
        with open(params_filename, 'r') as f:
            for l in f.readlines():
                if not l.startswith("#"):
                    sa = l.split(":")
                    params[sa[0]] = str(sa[1]).strip()
        return params

    def test_docker(self):
        dc = DockerClient(self.dockerhub_user, self.dockerhub_pwd)
        #dc.pull_image('jataware/dojo-publish', 'CHIRPS-Monthly-latest')
        dc.list_system_images()