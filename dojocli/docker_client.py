
"""

docker-py (https://pypi.org/project/docker-py/) client for dojo-api

"""

from sys import float_repr_style, stderr
import docker
import click
from docker.api.volume import VolumeApiMixin
from tqdm import tqdm

class DockerClient(object):

    def __init__(self):
        self.api_client = docker.APIClient() #base_url='unix://var/run/docker.sock')
        self.client = docker.from_env()
        self.container = None

    def execute_command(self, model_command):
        click.echo(f'\nExecuting {model_command} in {self.container.name}.')
        exe = self.api_client.exec_create(container=self.container.name, cmd=model_command)
        self.api_client.exec_start(exe)

    def get_logs(self, container_name):
        """
        Description
        -----------
        Returns the container logs from start.

        """

        return self.api_client.logs(container_name, timestamps=True)

    def pull_image(self, image_name):
        """
        Description
        -----------
        Pull the image from hub.docker.com to the local docker system.
        Implements tqdm for download progress bar.
        
        Parameters
        ----------
            imagename: str
                format repo:tag
                e.g. jataware/dojo-publish:CHIRPS-Monthly-latest
        """

        # Bulid the Docker Hub repo and tag from the image name.
        sa = image_name.split(":")
        repo = sa[0]
        tag = sa[1]

        # Use tqdm for progress bar handling. client.api.pull streams JSON
        # strings in line below e.g.:
        # {'status': 'Pulling from jataware/dojo-publish', 'id': 'AgMIPSeasonalCropEmulator-latest'}
        # {'status': 'Already exists', 'progressDetail': {}, 'id': '16ec32c2132b'}
        # {'status': 'Pulling fs layer', 'progressDetail': {}, 'id': '2a7e5d7d51a6'}
        # {'status': 'Waiting', 'progressDetail': {}, 'id': '360694784144'}
        # {'status': 'Downloading', 'progressDetail': {'current': 2724336, 'total': 7717464}, 
        #       'progress': '[=================>                                 ]  2.724MB/7.717MB', 'id': 'a473cbaea391'}
        
        # Create a tqdm object for each line id.
        t_lookup = {}
        position_counter = -1
        for line in self.client.api.pull(repo, tag, True,  decode=True): 
            status = line["status"]
            lineid = line["id"] if "id" in line else None
            progress = line["progress"] if "progress" in line else None    

            # Set the tqdm instance t based on the line id if present.
            # The position parameter dictates the line offest of the tqdm object.
            if lineid is None:
                position_counter += 1
                t = tqdm(position = position_counter, bar_format='{desc}')
            elif not lineid in t_lookup:
                position_counter += 1
                t = tqdm(position = position_counter, bar_format='{desc}')
                t_lookup[lineid] = t
            else:
                t = t_lookup[lineid]

            # Set the progress message text.
            if (progress == None):
                if lineid == None:
                    text = status
                else:
                    text = f'{lineid:<} {status}  '
            else:
                text = f'{lineid:<} {status} {progress}'

            # Set the description str referred by bar_format-'{desc}' in t.
            t.set_description_str(text)
   
    def create_container(self, image_name, volume_array, container_name, container_command, run_attached: bool = True):
        """
        Description
        -----------
            Create a container from the image identified by the image_name
            parameter and run the container_command. 

        Parameters
        ----------
            image_name: str
                The name of the model docker image pulled from Docker Hub.
            
            volume_array: list/array
                Array of dictionary pairs of local_volume:container volume for volume mounts.

            container_name: str
                An informative name for the container instead of gibberish like "stinky_goiter".

            container_command: str
                The str to pass to command. Consists of the chown output file commands and the model command.
                e.g.: "bash -c 'sudo chown clouseau:clouseau outputdir && python3 mymodel.py'"

            run_attached: bool = True
                Option to run detached (in background.)
        
        """

       
        if run_attached:
            # The low-level API client requires formatting for volumes, and volumes_array to be passed in host_config.
            # volume_array example:
            # ['/home/user/source/repos/dojo-cli/runs/CHIRPS-Monthly/17bf37e3-3785-43be-a2a3-fec6add03376/20211217135801/output:/home/clouseau/results']
            # volumes should be ['/home/clouseau/results']
            volumes = [v.split(':')[1] for v in volume_array]
            
            # Create the container detached.
            c = self.api_client.create_container(image_name, command=container_command, volumes=volumes, name=container_name, detach=False,
                host_config=self.api_client.create_host_config(binds=volume_array, auto_remove=True))
        
            # Start the container.
            self.api_client.start(c)

            # Attach to the container and stream the logs.
            log_header = False
            logs=[]
            for b in self.api_client.logs(c, stream=True, stderr=True, stdout=True):
                if not log_header:
                    click.echo('\nModel run logs:\n')
                    log_header = True
                line = b.decode("utf-8")
                logs.append(line)
                click.echo(line.strip())
            return logs
        else:
            # If running detached, client.containers.run returns the container object.
            self.container = self.client.containers.run(image_name, command=container_command, stdin_open=True, stdout=True, detach=True, 
                volumes=volume_array, name=container_name)
            return self.container

    def remove_container(self, container_name):
        """
        Description
        -----------
        Remove the Docker container from the system.
        """

        self.api_client.remove_container(container_name)
    