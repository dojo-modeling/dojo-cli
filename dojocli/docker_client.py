
import docker
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
