# dojo-cli

A command-line interface library for black box domain model execution. This library enables uses to execute domain models locally.

The library has 6 key methods:

- List the latest versions of models.
- Print parameter metadata for a selected model.
- Run a model via the Docker Python SDK.
- Check model container status.
- Get model (docker container) logs.
- Get results path.


## Setup

The CLI requires a configuration file with Docker Hub and DOJO credentials. This filename can be passed with each CLI command via the `--config` option, or the default file *.config* will be used.

See *example.config* for guidance:
```
{
    "DOCKERHUB_USER": "",
    "DOCKERHUB_PWD": "",
    "DOJO_URL": "https://dojo-test.com",
    "DOJO_USER": "",
    "DOJO_PWD": ""
}
```

## CLI help
```
python dojocli/cli.py --help
python dojocli/cli.py listmodels --help
python dojocli/cli.py printparams --help
python dojocli/cli.py runmodel --help
```

## Available commands
- [listmodels](#listmodels):   List available models.
- [printparams](#printparams):  Print the parameters required to run a model.
- [runmodel](#runmodel):     Run a model.




## listmodels

### Description

List available models.

### Parameters
- `--config` : name of configuation file; defaults to *.config*

### Example

$ `python dojocli/cli.py listmodels`
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

## printparams

### Description

Prints model run parameters and writes them as JSON to file.

### Parameters
- `--model` : name of the model
- `--config` : name of configuation file; defaults to *.config*

### Example

$ `python dojocli/cli.py printparams --model=CHIRPS-Monthly`

This will print the parameters necessary to run the model CHIRPS-Monthly:

```
Model run parameters for CHIRPS-Monthly
#  month  : 01
#  year  : 2021
#  bounding_box : [[33.512234, 2.719907], [49.98171,16.501768]]
```

Additionally, `printparams` will write *params_template.json* with example model parameters:
```
{" month  ": "01", " year  ": "2021", " bounding_box ": "[[33.512234, 2.719907], [49.98171,16.501768]]"}
``` 

## runmodel

### Description

Runs the selected model used the specified model parameters.

### Parameters
- `--model` : name of the model
- `--config` : name of configuation file; defaults to *.config*
- `--params` : model parameters in JSON format
- `--paramsfile` : name of file of model parameters in JSON format; defaults to *params_template.json*.
- `--outputdir` : folder specified for model output files; defaults to  */runs/{model}/{datetime}* e.g. */dojo-cli/runs/CHIRTSmax-Monthly/20210403110420*.

To run a model, the parameter values should either be assigned via the `--params` option , or a json file specified via the `--paramsfile` option. If neither parameter option is set, the --paramsfile filename *params_template.json* will be used.

### Examples

(1) Run the CHIRPS-Monthly model using the default configuration settings in *.config* and model parameters in *params_template.json*:

- ```python dojocli/cli.py runmodel --model=CHIRPS-Monthly```

(2) Run the CHIRPS-Monthly model using the default configuration settings in *.config* and model parameters in *chirps-monthly.json*:
- ```python dojocli/cli.py runmodel --model=CHIRPS-Monthly --paramsfile=chirps-monthly.json```

(3) Run the CHIRPS-Monthly model using the default configuration settings in *.config* and specified model parameters:
- ```python dojocli/cli.py runmodel --model=CHIRPS-Monthly --params='{"month": "09", "year": "2016", "bounding_box": "[[33.512234, 2.719907], [49.98171,16.501768]]"}'```

