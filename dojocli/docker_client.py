"""

docker-py (https://pypi.org/project/docker-py/) client for dojo-api

"""

from sys import float_repr_style, stderr
import docker
import click
from docker.api.volume import VolumeApiMixin
from tqdm import tqdm
import fnmatch


class DockerClient(object):
    def __init__(self):
        self.api_client = docker.APIClient()  # base_url='unix://var/run/docker.sock')
        self.client = docker.from_env()
        self.container = None

    def create_container(
        self,
        image_name,
        container_name,
        container_command,
        config_files,
        run_attached: bool = True,
    ):
        """
        Description
        -----------
            Create a container from the image identified by the image_name
            parameter and run the container_command.

        Parameters
        ----------
            image_name: str
                The name of the model docker image pulled from Docker Hub.

            container_name: str
                An informative name for the container instead of gibberish like "stinky_goiter".

            container_command: str
                The model command to pass to command e.g."python3 mymodel.py".

            run_attached: bool = True
                Option to run detached (in background.)

        Returns
        -------
            The created container either stopped or detached and running.
        """

        if run_attached:
            # attached volumes
            volumes_list = []
            binds = []
            for key in config_files:
                binds.append(f"{key}:{config_files[key]}")
                if config_files[key] not in volumes_list:
                    volumes_list.append(f"{config_files[key]}")
            # Create the container detached.
            self.container = self.api_client.create_container(
                image_name,
                command=container_command,
                name=container_name,
                detach=False,
                host_config=self.api_client.create_host_config(
                    auto_remove=False, binds=binds
                ),
                volumes=volumes_list,
            )

            # Start the container.
            self.api_client.start(self.container)

            # Attach to the container and stream the logs.
            log_header = False
            logs = []
            for b in self.api_client.logs(
                self.container, stream=True, stderr=True, stdout=True
            ):
                if not log_header:
                    click.echo("\nModel run logs:\n")
                    log_header = True
                line = b.decode("utf-8")
                logs.append(line)
                click.echo(line.strip())
            return self.container
        else:
            # volumes for detached
            detached_volume_array = []
            for key in config_files:
                if config_files[key] not in detached_volume_array:
                    detached_volume_array.append(f"{key}:{config_files[key]}")

            # If running detached, client.containers.run returns the container object.
            self.container = self.client.containers.run(
                image_name,
                command=container_command,
                stdin_open=True,
                stdout=True,
                volumes=detached_volume_array,
                detach=True,
                name=container_name,
            )
            return self.container

    def execute_command(self, model_command):
        # click.echo(f'\nExecuting {model_command} in {self.container.name}.\n')
        exe = self.api_client.exec_create(
            container=self.container.name, cmd=model_command, stdin=True
        )
        self.api_client.exec_start(exe)

        # For testing:
        # print(self.api_client.exec_inspect(exe))
        # for l in self.api_client.exec_start(exe, stream=True):
        #    print(l)

    def get_logs(self, container_name):
        """
        Description
        -----------
        Returns the container logs from start.

        """

        return self.api_client.logs(container_name, timestamps=True)

    def is_running(self, container_id: str = None, container_name: str = None):
        if container_id is not None:
            try:
                result = self.api_client.inspect_container(container_id)
                if "State" in result:
                    if "Running" in result["State"]:
                        return result["State"]["Running"]
                raise docker.errors.NotFound
            except docker.errors.NotFound:
                click.echo(
                    f"No information found for a docker container with id {container_id}."
                )
                return None
        elif container_name is not None:
            try:
                result = self.api_client.inspect_container(container_name)
                if "State" in result:
                    if "Running" in result["State"]:
                        return result["State"]["Running"]
                raise docker.errors.NotFound
            except docker.errors.NotFound:
                click.echo(
                    f"No information found for a docker container {container_name}."
                )
                return None

    def list_containers(self, model: str):
        """
        Description
        -----------
            Returns a list of container ids based on the model name.

        Parameters
        ----------
            model: str
            The name of the model.

        Returns
        -------
            List of container ids.

        """
        containers = self.client.containers.list(all=True, filters={"name": model})
        return [c.id for c in containers]

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
        for line in self.client.api.pull(repo, tag, True, decode=True):
            status = line["status"]
            lineid = line["id"] if "id" in line else None
            progress = line["progress"] if "progress" in line else None

            # Set the tqdm instance t based on the line id if present.
            # The position parameter dictates the line offest of the tqdm object.
            if lineid is None:
                position_counter += 1
                t = tqdm(position=position_counter, bar_format="{desc}")
            elif not lineid in t_lookup:
                position_counter += 1
                t = tqdm(position=position_counter, bar_format="{desc}")
                t_lookup[lineid] = t
            else:
                t = t_lookup[lineid]

            # Set the progress message text.
            if progress == None:
                if lineid == None:
                    text = status
                else:
                    text = f"{lineid:<} {status}  "
            else:
                text = f"{lineid:<} {status} {progress}"

            # Set the description str referred by bar_format-'{desc}' in t.
            t.set_description_str(text)

    def remove_container(self, container_name):
        """
        Description
        -----------
        Remove the Docker container from the system.
        """

        self.api_client.remove_container(container_name)

    def container_diff(self, container_name):
        """
        Description
        -----------
        Return files changed in container from model run
        """
        return self.api_client.diff(container_name)

    def match_pattern_output_path(self, container_name, outputs):
        """
        Description
        -----------
        Return new output paths accounting for wildcards
        """
        array_of_files = self.container_diff(container_name)
        new_outputs = []
        for output in outputs:
            for file_changed in array_of_files:
                if fnmatch.fnmatch(file_changed.get("Path", ""), output):
                    new_outputs.append(file_changed.get("Path"))

        return new_outputs
