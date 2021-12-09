# dojo-cli

A command-line interface library for black box domain model execution. This library enables users to execute domain models locally.

The library has 5 key methods:

- List the latest versions of models.
- Print parameter metadata for a selected model.
- Print a summary of the output files of a selected model.
- Print a desription of a selected model.
- Run a model.

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
```

## CLI help

The following commands will provide details of each available dojocli command:

```
dojocli --help
dojocli describe --help
dojocli listmodels --help
dojocli printoutputs --help
dojocli printparams --help
dojocli runmodel --help
```

## Available commands

-  [describe](#describe): Print a description of the model.
-  [listmodels](#listmodels): List available models.
-  [printoutputs](#printoutputs): Print descriptions of the output files produced by a model.
-  [printparams](#printparams): Print the parameters required to run a model.
-  [runmodel](#runmodel): Run a model.


## *describe*

Print a description of the model.

### Parameters
- `--model` : name of the model
- `--config` : name of configuation file; defaults to *.config*

### Example

`python dojocli/cli.py describe --model="Population Model"`
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

## *printoutputs*

### Description

Prints a summary of the output files produced by a model.

### Parameters
- `--model` : name of the model
- `--config` : name of configuation file; defaults to *.config*

### Example

`dojocli printouputs --model=Topoflow`

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
```

## *printparams*

### Description

Prints a description of model parameters and writes an example to file.

### Parameters
- `--model` : name of the model
- `--config` : name of configuation file; defaults to *.config*

### Example

`dojocli printparams --model=CHIRPS-Monthly`

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

Additionally, `printparams` will write *params_template.json* with example model parameters:
```
{
    "month": 1,
    "year": 2021,
    "bounding_box": "'[[33.512234, 2.719907], [49.98171,16.501768]]'"
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
- `--outputdir` : folder specified for model output files; defaults to  */runs/{model}/{datetime}* e.g. */dojo-cli/runs/CHIRTSmax-Monthly/20210403110420*.

To run a model, the parameter values should either be assigned via the `--params` option , or a json file specified via the `--paramsfile` option. If neither parameter option is set, the --paramsfile filename *params_template.json* will be used.

After processing `runmodel` will print the local directory where the model output and accessory (e.g. .mp4, .webm, .jpg) files are available. The local directory tree structure will consist of the model name and a datetime stamp of the model run (unless specified by the `--outputdir` option)e.g.
```
/runs
 | - Stochastic Gridded Conflict Model
    |- 20211209160543
       |- output
          |- conflict_IDs.rti
          |- ...
       |- acessorries
          |- conflict_IDs_2D.mp4
           - ...
       |- accessories-captions.json
       |- run-parameters.json
```

In addition to the model's output and accessory files, `runmodel` will write two other files:
- run-parameters.json : the model parameters used for this run
- accessories-captions.json : descriptions of the files in *accessories* 

### Examples

(1) Run the CHIRPS-Monthly model using the default configuration settings in *.config* and model parameters in *params_template.json*:

- ```dojocli runmodel --model=CHIRPS-Monthly```

(2) Run the CHIRPS-Monthly model using the default configuration settings in *.config* and model parameters in *chirps-monthly.json*:
- ```dojocli runmodel --model=CHIRPS-Monthly --paramsfile=chirps-monthly.json```

(3) Run the CHIRPS-Monthly model using the default configuration settings in *.config* and specified model parameters:
- ```dojocli runmodel --model=CHIRPS-Monthly --params='{"month": "09", "year": "2016", "bounding_box": "[[33.512234, 2.719907], [49.98171,16.501768]]"}'```

