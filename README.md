# dojo-cli

A command-line interface library for black box domain model execution. This library enables uses to execute domain models locally.

The library has 6 key methods:

- List the latest versions of models.
- Get parameter metadata for a selected model.
- Run a model via the Docker Python SDK.
- Check model container status.
- Get model (docker container) logs.
- Get results path.


## Setup

The CLI requires a configuration file with Docker Hub and DOJO credentials. This filename can be passed with each CLI command, or the default file `.config` will be used.

See `example.config` for guidance:
```
{
    "DOCKERHUB_USER": "",
    "DOCKERHUB_PWD": "",
    "DOJO_URL": "https://dojo-test.com",
    "DOJO_USER": "",
    "DOJO_PWD": ""
}
```

## Running the CLI from source


### CLI help:
```
python dojocli/cli.py --help
python dojocli/cli.py get-model-params --help
python dojocli/cli.py list-models --help
python dojocli/cli.py run-model --help
```

### List models

$ `python dojocli/cli.py list-models` lists the available models e.g.: 
```
(1) APSIM
(2) APSIM-Cropping
(3) APSIM-Rangelands
(4) Accessibility Model
(5) AgMIP Seasonal Crop Emulator
(6) CHIRPS - Climate Hazards Center Infrared Precipitation with Stations
(7) CHIRPS-GEFS
(8) CHIRPS-GEFS Monthly
(9) CHIRPS-Monthly
...
```

### Get the run parameters of a model

$ `python dojocli/cli.py get-model-params --model_name=CHIRPS-Monthly`

This is required before running a model. It will write the parameters for the model CHIRPS-Monthly to `CHIRPS-Monthly_params.txt`:

```
# Lines starting with # are comments.
# Model run parameters for CHIRPS-Monthly
# Example parameters:
# month: 01
# year: 2021
# bbox: [[33.512234, 2.719907], [49.98171,16.501768]]
#
# Set run parameter values here:
name: 
month: 
year: 
bbox: 
```

To run a model, the parameter values above need to be set, and the parameters filename passed to `run_model`.

### Run a model

$ `python dojocli/cli.py run-model --model_name=CHIRPS-Monthly --params=CHIRPS-Monthly_params.txt`

This command will download and run the model docker image.
