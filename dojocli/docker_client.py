

import docker
import json

from docker import client

class DockerClient(object):

    def __init__(self, user, pwd):
        self.client = docker.from_env()
        self.auth_config = { "username": user, "password": pwd}
        self.container = None

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
        for line in self.client.api.pull(repo, tag, True, self.auth_config, decode=True):
            print(json.dumps(line, indent=4))
            # TODO: Progress Bar
               

    def create_container(self, image_name):
        self.container = self.client.containers.run(image_name, command='bash', stdin_open=True, detach=True)
        return self.container.name








