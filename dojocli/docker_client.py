
import docker
import json
from tqdm import tqdm

DOCKER_SERVER_URL = 'unix://var/run/docker.sock'

class DockerClient(object):

    def __init__(self, user, pwd):
        self.api_client = docker.APIClient(base_url=DOCKER_SERVER_URL)
        self.client = docker.from_env()
        self.auth_config = { "username": user, "password": pwd}
        self.container = None

    def execute_command(self, model_command):
        print(f'Executing {model_command} in {self.container.name}.')
        exe = self.api_client.exec_create(container=self.container.name, cmd=model_command)
        self.api_client.exec_start(exe)

    def list_system_images(self):
        for i in self.client.images.list(name='jataware/dojo-publish'):
            print(i)
            
    def pull_image(self, image_name):
        """
        Description
        -----------
        Pull the image from hub.docker.com to the local docker system.
        
        Parameters
        ----------
            imagename: str
                format repo:tag
                e.g. jataware/dojo-publish:CHIRPS-Monthly-latest
        """

        sa = image_name.split(":")
        repo = sa[0]
        tag = sa[1]
        #tqdm(self.client.api.pull(repo, tag, True, self.auth_config, decode=True))
        for line in tqdm(self.client.api.pull(repo, tag, True, self.auth_config, decode=True)):
           print(json.dumps(line, indent=4))
            # TODO: Progress Bar
               
    def create_container(self, image_name, volume_array):
        self.container = self.client.containers.run(image_name, command='bash', stdin_open=True, detach=True, volumes=volume_array)
        return self.container.name
