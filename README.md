# dojo-cli

A command-line interface library for black box domain model execution. This library enables users to execute domain models locally.

The library has 6 key methods:

- List the latest versions of all available models.
- Print parameter metadata for a selected model.
- Print a summary of the output and accessory files of a selected model.
- Print a desription of a selected model.
- Run a model.
- List all versions of a model.

## Installation

Ensure you have a working installation of [Docker](https://docs.docker.com/engine/install/).


Once Docker is installed on Linux or Mac you can add the current user to the Docker group with:
```
sudo groupadd docker
sudo gpasswd -a $USER docker
```
then log out/back in so changes can take effect. This should be done after installing Docker.

## Setup

The CLI requires a configuration file with [DOJO API](https://github.com/dojo-modeling) credentials. This filename can be passed with each CLI command via the `--config` option, or the default file *.config* will be used.

See *example.config* for guidance:
```
{
    "DOJO_URL": "https://dojo-test.com",
    "DOJO_USER": "",
    "DOJO_PWD": ""
}
```

If running the library locally from source, the following libraries are required to be installed:
```
Click>=7.0,<8
docker>=5.0.3
Jinja2>=2.11.3
```

## CLI help

The following commands will provide details of each available dojo command:

```
dojo --help
dojo describe --help
dojo listmodels --help
dojo outputs --help
dojo parameters --help
dojo runmodel --help
dojo versions --help
```

## Available commands

-  [describe](#describe): Print a description of the model.
-  [listmodels](#listmodels): List available models.
-  [outputs](#outputs): Print descriptions of the output and accessory files produced by a model.
-  [parameters](#parameters): Print the parameters required to run a model.
-  [runmodel](#runmodel): Run a model.
-  [versions](#versions): List all versions of a model.


## *describe*

Print a description of the model.

### Parameters
- `--model` : name of the model
- `--config` : name of configuation file; defaults to *.config*
- `--version` : version of the model if `--model` is not passed
### Example

`dojo describe --model="Population Model"`
```
NAME
----
Population Model

MODEL FAMILY
------------
Kimetrica

DESCRIPTION
-----------
The population model serves as an ancillary tool to distribute, disaggregate yearly population projections onto a geospatial representation. Occasionally, the output of this model is required as an independent variable for downstream models.y
...
```

## *listmodels*

### Description

List available models.

### Parameters
- `--config` : name of configuation file; defaults to *.config*

### Example

$ `dojo listmodels`
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

## *outputs*

### Description

Prints a summary of the output and accessory files produced by a model.

### Parameters
- `--model` : name of the model
- `--config` : name of configuation file; defaults to *.config*
- `--version` : version of the model if `--model` is not passed

### Example

`dojo outputs --model=Topoflow`

```
Getting output file information for Topoflow ...

Topoflow writes 4 output file(s):

(1) Test1_2D-d-flood.nc: Land Surface Water Depth in netcdf format with the following labeled data:
    Y: Y
    X: longitude
    datetime: Datetime
    d_flood: Land Surface Water Depth

(2) Test1_2D-Q.nc: Volumetric Discharge in netcdf format with the following labeled data:
    Y: Y
    X: longitude
    datetime: Datetime
    Q: Volumetric Discharge [m^3/s]

(3) Test1_2D-d.nc: Max Channel Flow Depth in netcdf format with the following labeled data:
    Y: Y
    X: longitude
    datetime: Datetime
    d: Max Channel Flow Depth

(4) Test1_2D-u.nc: Mean Channel Flow Velocity in netcdf format with the following labeled data:
    Y: Y
    X: longitude
    datetime: Datetime
    u: Mean Channel Flow Velocity

"Topoflow" version 2ddd2cbe-364b-4520-a28e-a5691227db39 writes 8 accessory file(s):

(1) Test1_0D-Q.png
(2) Test1_0D-d-flood.png
(3) Test1_0D-d.png
(4) Test1_0D-u.png
(5) Test1_2D-Q.mp4
(6) Test1_2D-d-flood.mp4
(7) Test1_2D-d.mp4
(8) Test1_2D-u.mp4
```

## *parameters*

### Description

Prints a description of model parameters and writes an example to file.

### Parameters
- `--model` : name of the model
- `--config` : name of configuation file; defaults to *.config*
- `--version` : version of the model if `--model` is not passed
### Example

`dojo parameters --model=CHIRPS-Monthly`

```
Getting parameters for CHIRPS-Monthly ...

Model run parameters for CHIRPS-Monthly:

Parameter 1     : month
Description     : 2-digit month
Type            : int
Unit            : month
Unit Description: month

Parameter 2     : year
Description     : 4-digit year
Type            : int
Unit            : years
Unit Description: years

Parameter 3     : bounding box
Description     : geographical bounding box of x,y min/max values. format: [ [xmin, ymin], [xmax, ymax] ] example: [[33.512234, 2.719907], [49.98171,16.501768]]
Type            : float
Unit            : longitude, latitude values
Unit Description: longitude, latitude values


Example parameters:

month: 01
year: 2021
bounding_box: '[[33.512234, 2.719907], [49.98171,16.501768]]'

Template CHIRPS-Monthly parameters file written to params_template.json.
```

Additionally, `parameters` will write *params_template.json* with example model parameters:
```
{
    "month": 1,
    "year": 2021,
    "bounding_box": "[[33.512234, 2.719907], [49.98171,16.501768]]"
}
``` 

## *runmodel*

### Description

Runs the selected model used the specified model parameters.

### Parameters
- `--model` : name of the model
- `--config` : name of configuation file; defaults to *.config*
- `--params` : model parameters in JSON format
- `--paramsfile` : name of file of model parameters in JSON format; defaults to *params_template.json*.
- `--outputdir` : folder specified for model output files; defaults to  */runs/{model}/{version}/{datetime}* e.g. */dojo-cli/runs/CHIRTSmax-Monthly/17bf37e3-3785-43be-a2a3-fec6add03376/20210403110420*
- `--version` : version of the model if `--model` is not passed
- `--attached` : True or False, defaults to True. 
  - If `attached`=`True` or is not passed, the cli will wait for the model to run in the container and then remove the container. 
  - If `attached`=`False` the model will run in the container in background. The user will need to monitor the output folder or container to determine when the run is completed. 

To run a model, the parameter values should either be assigned via the `--params` option , or a json file specified via the `--paramsfile` option. If neither parameter option is set, the --paramsfile filename *params_template.json* will be used.

After processing `runmodel` will print the local directory where the model output and accessory (e.g. .mp4, .webm, .jpg) files are available. The local directory tree structure will consist of the model name, the model version, and a datetime stamp of the model run (unless specified by the `--outputdir` option) e.g.:
```
/runs
 | - Stochastic Gridded Conflict Model
    |-17bf37e3-3785-43be-a2a3-fec6add03376
        |- 20211209160543
        |- output
            |- conflict_IDs.rti
            |- ...
        |- acessorries
            |- conflict_IDs_2D.mp4
            - ...
        |- accessories-captions.json
        |- run-parameters.json
        |- logs.txt
```

In addition to the model's output and accessory files, `runmodel` will write three other files:
- accessories-captions.json : descriptions of the files in *accessories* 
- logs.txt : the log output produced by this run
- run-parameters.json : the model parameters used for this run

### Examples

(1) Run the CHIRPS-Monthly model using the default configuration settings in *.config* and model parameters in *params_template.json*:

```dojo runmodel --model="CHIRPS-Monthly"```

(2) Run the CHIRPS-Monthly model using the default configuration settings in *.config* and model parameters in *chirps-monthly.json*:

```dojo runmodel --model="CHIRPS-Monthly" --paramsfile=chirps-monthly.json```

(3) Run the CHIRPS-Monthly model using the default configuration settings in *.config* and specified model parameters:

```dojo runmodel --model="CHIRPS-Monthly" --params='{"month": "09", "year": "2016", "bounding_box": "[[33.512234, 2.719907], [49.98171,16.501768]]"}'```

(4) Run a specific version of CHIRPS-Monthly:

```dojo runmodel --version="a14ccbdf-c8d5-4816-af52-8b2ef3da9d22"```

(5) Run a specific version of CHIRPS-Monthly detached:

```dojo runmodel --version="a14ccbdf-c8d5-4816-af52-8b2ef3da9d22" --attached=False```

### Models missing Docker images

In some instances a user may attempt to run a model version that does not have a docker image associated with it. If this occurs *dojo-cli* will list available model versions (most recent first). The user can then choose to run one of versions listed.

```
$ dojo runmodel --version="9d077a11-9db3-441c-a2ae-0ecacd1381f0"
APSIM-Cropping version 9d077a11-9db3-441c-a2ae-0ecacd1381f0 does not have a Docker image associated with it and therefore cannot be run.

The following versions of APSIM-Cropping are available to run:
created date: 2021-12-14 16:14:44  version: ce2fc539-c734-4077-8b9c-2f82cd032049
created date: 2021-12-08 19:41:17  version: c635fe68-9526-4719-8a15-9f6577bd9067
created date: 2021-12-08 19:38:14  version: 53934f4c-04d8-4e02-920e-888208d68782
created date: 2021-12-08 19:32:37  version: 90a77965-15b8-48f9-bf1e-6b25b29c44de
created date: 2021-12-08 19:18:19  version: 229132d2-ad92-49d6-8639-7b240a05508b
created date: 2021-12-07 20:28:52  version: 40efd965-0c5d-4ab0-8e88-c416a41c04df
created date: 2021-12-01 15:45:33  version: 73560c5a-58a7-46a7-be0e-047c267d315e
created date: 2021-11-28 16:23:12  version: a24b4539-15f3-4ee2-b802-4c7e092d19f2
created date: 2021-11-28 16:20:40  version: 1b71a950-7580-49e5-a0f1-ecf9511fb1a7
created date: 2021-11-28 16:20:11  version: 0e66a9c2-dbe3-4add-ab81-2e7502a7ad45
created date: 2021-11-17 19:38:20  version: b99c87bd-cd0f-41d9-9bf7-2c93004c5e6b
created date: 2021-11-17 19:33:39  version: 252b4f0a-ba15-4825-a155-1a3ca348da3b
created date: 2021-11-17 17:30:58  version: e57e85cf-3a44-4a55-b63c-efb19af2527f
created date: 2021-11-17 16:27:58  version: 32a238b9-5f16-4f6b-a085-b3e471be3dce
created date: 2021-11-17 16:07:42  version: 915251a7-96eb-49ee-ac36-1a7db1e684bd
created date: 2021-11-17 16:06:19  version: bb2793f1-526a-4796-b1b2-1006610e1d9e
created date: 2021-11-17 16:05:13  version: 2ea95b10-f1dc-48b2-a675-82ca27fc03e6
created date: 2021-11-17 16:00:43  version: 849d824c-a662-4da3-a131-d41c73afc42a
created date: 2021-11-16 07:10:14  version: 2ff8502b-831e-4684-96cc-80f08da45f28
```

## *versions*

### Description

List all versions of a model.

### Parameters
- `--model` : name of the model 
- `--config` : name of configuation file; defaults to *.config*

### Example

`dojo versions --model=CHIRPS-Monthly`
```
Getting versions of "CHIRPS-Monthly" ...

Available versions of "CHIRPS-Monthly":

Current Version
"17bf37e3-3785-43be-a2a3-fec6add03376"

Previous Versions
"a14ccbdf-c8d5-4816-af52-8b2ef3da9d22"

Later Versions

```