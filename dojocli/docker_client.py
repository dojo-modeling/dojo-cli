
import docker
import json
from tqdm import tqdm

class DockerClient(object):

    def __init__(self):
        self.api_client = docker.APIClient() #base_url='unix://var/run/docker.sock')
        self.client = docker.from_env()
        self.container = None

    def execute_command(self, model_command):
        print(f'\nExecuting {model_command} in {self.container.name}.')
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
        #for line in tqdm(self.client.api.pull(repo, tag, True, self.auth_config, decode=True)):
        for line in tqdm(self.client.api.pull(repo, tag, True,  decode=True)):
           print(json.dumps(line, indent=4))
            # TODO: Progress Bar
               
    def create_container(self, image_name, volume_array, container_name):
        """
        Description
        -----------
            Create and run a container from the image identified by the image_name
            parameter with the following settings:
            
            (1) Run container in the background and return a Container object. (detach=True)
            (2) Keep STDIN open even if not attached. (stdin_open=True)
            (3) command='bash'; passing None does not seem to work.

        Parameters
        ----------
            image_name: str
                The name of the model docker image pulled from Docker Hub.
            
            volume_array: list/array
                Array of dictionary pairs of local_volume:container volume for volume mounts.

            container_name:
                An informative name for the container instead of gibberish like "stinky_goiter".
        
        """
        self.container = self.client.containers.run(image_name, command='bash', stdin_open=True, detach=True, volumes=volume_array, name=container_name)
        return self.container.name
