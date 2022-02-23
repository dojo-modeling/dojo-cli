"""
  Dojo-cli client for dojo api.
"""

import click
from datetime import datetime
from docker.api import container

from docker.api.volume import VolumeApiMixin

# from requests.models import stream_decode_response_unicode
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
            if hasattr(e, "message"):
                click.echo(e.message)
            else:
                click.echo(e)

    def get_accessories(self, model_id: str):
        """
        Description
        -----------
        Call dojo endpoint dojo/accessories to get model accessory file metadata.

        Returns
        -------
        dict of JSON payload of api call.

        """

        return self.get_dojo_stuff("accessories", model_id)

    def get_available_models(self):
        """
        Description
        -----------

            Get latest models with images from dojo api.

            Use /models and not models/latest so that images can be restricted to
            jataware/dojo-publish.

        """
        # url = f'{self.dojo_url}/models?query=image:"{IMAGE_QUERY_NAME}" AND NOT _exists_:"next_version"&size=1000'
        url = f"{self.dojo_url}/models/latest?size=1000"
        response = self.generic_dojo_get_request(url)

        try:
            resp = response.json()
            models = set()

            # for r in resp["results"]:
            #    if r['image'] != '' and r['next_version'] == None:
            #        models.add(f"\"{r['name']}\"")

            # List the latest versions of models even if it does not have an image.
            models = {f"\"{r['name']}\"" for r in resp["results"]}
            models = list(models)
            models.sort()
            return models
        except Exception as e:
            if hasattr(e, "message"):
                click.echo(f"{e.message}\n{response.text}")
            else:
                click.echo(response.text)
            exit

    def get_dojo_stuff(self, stuff, model_id):
        """
        Get stuff(config, directive, accessories, outputfiles) based on model_id.
        """

        url = f"{self.dojo_url}/dojo/{stuff}/{model_id}"
        response = self.generic_dojo_get_request(url)
        try:
            return response.json()
        except Exception as e:
            if hasattr(e, "message"):
                click.echo(e.message)
            else:
                click.echo(e)
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
        dojo_stuff = ["accessories", "config", "directive", "outputfile"]
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

        # url = f'{self.dojo_url}/models?query=name:"{model_name}" AND image:"{IMAGE_QUERY_NAME}" AND NOT _exists_:"next_version"'
        if model_id == None:
            url = f'{self.dojo_url}/models/latest?query=name:"{model_name}"'
        else:
            url = f"{self.dojo_url}/models/{model_id}"

        response = self.generic_dojo_get_request(url)

        try:
            resp = response.json()

            if "results" in resp:
                # /models/latest returns a list of model objects in "results"
                for r in resp["results"]:
                    if r["name"] == model_name or r["id"] == model_id:
                        return r
            elif "name" in resp and "id" in resp:
                # models/{model_id} returns a single model object
                if resp["name"] == model_name or resp["id"] == model_id:
                    return resp

        except Exception as e:
            if hasattr(e, "message"):
                click.echo(e.message)
            else:
                click.echo(e)
            exit

    def get_model_versions_with_images(self, model_name: str):
        """
        Description
        -----------
        Called from cli.py when the user attempts to run a model lacking an image.
        This will return a list of versions and creation dates with associated images.

        Parameters
        ----------
        model_name: str
            The name of the model.

        Returns
        -------
        Sorted (reverse=true) list of (created_at, version) tuples.
        """

        url = f'{self.dojo_url}/models?query=name:"{model_name}"&size=100'
        response = self.generic_dojo_get_request(url)
        resp = response.json()
        versions = []
        try:
            for r in resp["results"]:
                if len(r["image"].strip()) > 0:
                    created_at = datetime.fromtimestamp(
                        r["created_at"] / 1000
                    ).strftime("%Y-%m-%d %H:%M:%S")
                    versions.append((created_at, r["id"]))

            versions.sort(reverse=True)
            return versions
        except Exception as e:
            if hasattr(e, "message"):
                click.echo(e.message)
            else:
                click.echo(e)
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

        return self.get_dojo_stuff("outputfile", model_id)

    def get_results(self, id: str, name: str):
        """
        Description
        -----------
            Checks whether the container is still running. If the container has
            stopped, the details for processing are gathered and passed to
            process_finished_model().

            One of the parameters id and name is requried.

        Parameters
        ----------
            id: str
                The container id.
            name: str
                The container name.
        """
        # Instantiate the Docker Client.
        dc = DockerClient()

        is_running = dc.is_running(container_id=id, container_name=name)
        if is_running is None:
            return
        if is_running:
            click.echo(
                f"Results for {name if name is not None else id} are not yet ready."
            )
        else:
            # Docker commands accept either name or id.
            container = name if name is not None else id

            # Copy the local_output_folder.txt file from the stopped container.
            os.system(
                f"docker cp {container}:/home/clouseau/local_output_folder.txt {os.getcwd()}/runs/local_output_folder.txt"
            )

            # Read the local_output_folder location.
            with open(f"{os.getcwd()}/runs/local_output_folder.txt", "r") as fh:
                local_output_folder = fh.readline()

            # Read and process the run info.
            with open(f"{local_output_folder}/run-info.txt", "r") as fh:
                for l in fh.readlines():
                    if l.startswith("output:"):
                        output_paths = l.split("output:")[1].strip().split("\t")
                    elif l.startswith("accessories:"):
                        accessory_paths = l.split("accessories:")[1].strip().split("\t")

            # Move all the model stuff.
            self.process_finished_model(
                container_id=id,
                container_name=name,
                local_output_folder=local_output_folder,
                output_paths=output_paths,
                accessory_paths=accessory_paths,
            )

            # Clean up.
            os.system(f"rm {os.getcwd()}/runs/local_output_folder.txt")

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
        url = f"{self.dojo_url}/models/{model_id}/versions"
        response = self.generic_dojo_get_request(url)
        try:
            return response.json()

        except Exception as e:
            if hasattr(e, "message"):
                click.echo(e.message)
            else:
                click.echo(e)
            exit

    def process_finished_model(
        self,
        container_id: str,
        container_name: str,
        local_output_folder: str,
        output_paths,
        accessory_paths,
    ):
        """
        Description
        -----------
            Process the finished model:
            (1) copy logs
            (2) write output and accessory files
            (3) remove container

        Parameters
        ----------
            container_id: str
                Docker container id e.g. e76880c24933
                Either this or container_name are required.
            container_name: str
                Docker container name e.g. dojo-stochasticgriddedconflictmodel20211227133418
                Etiher this or container_id are required.
            local_output_fodler: str
                Path to the model output directory.
            output_paths:
                Docker container paths for output files.
            accessory_paths:
                Docker container paths for accessory files.


        """
        # The docker commands will take either id or name.
        container = container_id if container_id is not None else container_name

        # Capture the container logs to file.
        os.system(f"docker logs {container} > '{local_output_folder}/logs.txt'")

        # Copy output files from the container to the local folder.
        if len(output_paths) > 0:
            os.makedirs(f"{local_output_folder}/output")
        for path in output_paths:
            os.system(
                f"docker cp {container}:'{path}' '{local_output_folder}/output/{os.path.basename(path)}'"
            )

        # Copy accessory files from the container to the local folder.
        if len(accessory_paths) > 0:
            os.makedirs(f"{local_output_folder}/accessories")
        for path in accessory_paths:
            os.system(
                f"docker cp {container}:'{path}' '{local_output_folder}/accessories/{os.path.basename(path)}'"
            )

        # Nuke the container from orbit.
        os.system(f"docker container rm {container}")

        # A miracle occurred.
        click.echo(
            f'\n\nRun completed.\nModel output, run-parameters, and log files are located in "{local_output_folder}".'
        )

    def run_model(
        self,
        model_name: str,
        params: str = None,
        params_filename: str = None,
        version: str = None,
        local_output_folder: str = None,
        run_attached: bool = True,
    ):
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

        # Get the model_id and image from the model_name or version.
        model_dict = self.get_model_info(model_name, model_id=version)
        model_id = model_dict["id"]
        image_name = model_dict["image"]

        # Use default directory if not specified.
        datetimestamp = datetime.today().strftime("%Y%m%d%H%M%S")
        if local_output_folder == None:
            local_output_folder = (
                f"{os.getcwd()}/runs/{model_name}/{model_id}/{datetimestamp}"
            )

        # Create main directory structure.
        os.makedirs(local_output_folder)

        # Get the metadata for this model.
        metadata = self.get_metadata(model_id)

        # Process output file locations.
        outputfiles = metadata["outputfile"]
        output_paths = []
        for output in outputfiles:
            # Build list of output file paths.
            output_dir = output["output_directory"]
            output_path = output["path"]
            output_paths.append(f"{output_dir}/{output_path}")

        # Process accessory file locations and captions.
        accessory_files = metadata["accessories"]
        accessory_captions = {}
        accessory_paths = []
        for accessory_file in accessory_files:
            # Build a list of accessory file locations.
            accessory_file_path = accessory_file["path"]
            accessory_paths.append(accessory_file_path)

            # Capture accessory file captions so they can be written to file.
            if "caption" in accessory_file:
                accessory_captions[
                    os.path.basename(accessory_file_path)
                ] = accessory_file["caption"]

        # Load parameters.
        if params == None:
            # If params json not passed then read from file.
            with open(params_filename, "r") as fh:
                params = json.load(fh)
        elif isinstance(params, str):
            # If params was passed in the command line it is a str; convert to dict.
            params = json.loads(params)

        # get config files and hydrate them
        config_dict = {}
        for configFile in metadata["config"]:
            try:
                s3_url = configFile["s3_url"]
                response = requests.get(s3_url)
                config_file_template = Template(response.text)
                config_rehydrated = config_file_template.render(params)
                if not os.path.isdir("temp"):
                    os.mkdir("temp")

                temp_file_name = (
                    os.getcwd() + "/temp/temp_" + configFile["path"].split("/")[-1]
                )
                config_dict.update({temp_file_name: configFile["path"]})
                with open(temp_file_name, "w") as f:
                    f.write(config_rehydrated)

            except Exception as e:
                print(f"error getting config files {e}")

        # Write the parameters used out to the run result directory.
        with open(f"{local_output_folder}/run-parameters.json", "w") as fh:
            json.dump(params, fh, indent=4)

        # Write accessory file captions to the run result directory.
        if len(accessory_captions) > 0:
            with open(f"{local_output_folder}/accessories-captions.json", "w") as fh:
                json.dump(accessory_captions, fh, indent=4)

        # Instantiate the Docker Client.
        dc = DockerClient()

        # Pull the image
        click.echo(f"Getting model image ...\n")
        dc.pull_image(image_name)

        # Set run command from metadata["directive"]["command"] and substitute params.
        model_command = Template(metadata["directive"]["command"])
        model_command = model_command.render(params)

        # Create the container name.
        if model_name is None:
            container_name = f"dojo-{version[-12:]}{datetimestamp}"
        else:
            container_name = re.sub("[ \]\[,()_]", "", model_name.lower()).strip()
            container_name = f"dojo-{container_name}{datetimestamp}"

        click.echo(
            f"\n\nRunning {model_name} version {model_id} in Docker container {container_name} ... \n"
        )
        if run_attached:
            click.echo(
                f"The model is running attached; this process will wait until the run is completed."
            )

            # Run the container attached.
            dc.create_container(image_name, container_name, model_command, config_dict)

            # account for wildcard output files
            wildcard_outputs = dc.match_pattern_output_path(
                container_name, output_paths
            )

            # Perform the finishing steps e.g. logging.
            self.process_finished_model(
                container_id=None,
                container_name=container_name,
                local_output_folder=local_output_folder,
                output_paths=wildcard_outputs,
                accessory_paths=accessory_paths,
            )

        else:
            click.echo(f"The model is running detached in background.")
            click.echo(
                f'\nModel progress can be monitored by the following command: "dojo results --name={container_name}"\n'
            )

            # Run the container detached.
            container = dc.create_container(
                image_name,
                container_name,
                model_command,
                config_dict,
                run_attached=False,
            )

            # Write the output folder path to the container or we won't know it.
            dc.execute_command(
                f"bash -c 'printf \"{local_output_folder}\" > /home/clouseau/local_output_folder.txt'"
            )

            # Write the run information to the output folder to be read when
            # processing the finished model run.
            with open(f"{local_output_folder}/run-info.txt", "w") as fh:
                fh.write(f"Docker container name: {container_name}\n")
                fh.write(f"Docker container id: {container.id}\n")
                fh.write(f"Model ID: {model_id}\n")
                fh.write(f"local_output_folder: {local_output_folder}\n")
                outputs = "\t".join(output_paths)
                fh.write(f"output: {outputs}\n")
                accessories = "\t".join(accessory_paths)
                fh.write(f"accessories: {accessories}\n")

    def set_config(self, config_filename):
        with open(config_filename) as f:
            config = json.load(f)

            if (
                "DOJO_USER" not in config
                or "DOJO_URL" not in config
                or "DOJO_PWD" not in config
            ):
                click.echo(
                    f"{config_filename} is missing a required field of DOJO_USER, DOJO_URL, and/or DOJO_PWD."
                )
                return

            # Set dojo url and authentication credentials.
            self.dojo_auth = (config["DOJO_USER"], config["DOJO_PWD"])
            self.dojo_url = config["DOJO_URL"]
