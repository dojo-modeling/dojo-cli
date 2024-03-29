import sys
from os.path import abspath, basename, dirname, exists

# Add path of the run files to the system path so VS Code can find things. 
sys.path.append(dirname(dirname(abspath(__file__))))

import click
from datetime import datetime
from dojocli.dojo_client import DojoClient
import json


def print_description(model_dict: dict, param_dicts: dict):
    """
    Description
    -----------
    Called from cli.describe(). Prints the model information.

    """

    click.echo(f'NAME\n----\n{model_dict["name"]}\n')
    click.echo(f'VERSION\n----\n{model_dict["id"]}\n')

    click.echo(f'MODEL FAMILY\n------------\n{model_dict["family_name"]}\n')
    click.echo(f'DESCRIPTION\n-----------\n{model_dict["description"]}\n')
    
    # Convert epoch time in milliseconds to seconds.
    created_at = datetime.fromtimestamp(model_dict["created_at"]/1000).strftime('%Y-%m-%d %H:%M:%S')
    click.echo(f'CREATED DATE\n------------\n{created_at}\n')
    
    click.echo('CATEGORY\n--------')
    category = ''
    for i in model_dict["category"]:
        category = category + f'{i.upper()}\t'
    click.echo(category + '\n')

    click.echo('MAINTAINER\n------------')
    for k, v in model_dict["maintainer"].items():
        click.echo(f'{k.upper()}: {v}')
    click.echo()

    click.echo(f'DOCKER IMAGE\n------------\n{model_dict["image"]}\n')

    click.echo('PARAMETERS\n----------')
    for param_dict in param_dicts:
        click.echo(param_dict["annotation"]["name"])

    click.echo()

def print_outputs(model: str, version: str, outputfile_dict: dict, accessories_dict: dict):
    """
    Description
    -----------
    Called from cli.printoutputs(). Prints information about the model output
    and accessory files.
    
    """

    # Output files
    click.echo(f'\n"{model}" version {version} writes {len(outputfile_dict)} output file(s):\n')
    for idx, outputfile in enumerate(outputfile_dict):
        transform = outputfile["transform"]
        click.echo(f'({idx+1}) {outputfile["path"]}: {outputfile["name"]} in {transform["meta"]["ftype"]} format with the following labeled data:')
        for transform_type in ['geo', 'date', 'feature']:
            for data_type in transform[transform_type]:
                click.echo(f'    {data_type["name"]}: {data_type["display_name"]}')
        click.echo()

    # Accessories
    if len(accessories_dict) > 0:
        accessories = [basename(acc["path"]) for acc in accessories_dict]
        accessories.sort()
        click.echo(f'\n"{model}" version {version} writes {len(accessories)} accessory file(s):\n')
        for idx, acc in enumerate(accessories):
            click.echo(f'({idx+1}) {acc}')

    click.echo()

def print_params(model_dict: dict, dc: DojoClient, params_filename: str = 'params_template.json'):
    """
    Description
    -----------
    (1) Print model parameters and instructions derived from the model metadata.

    (2) Write the json structure to params.json or specified filename.

    Parameters
    ----------
    model_dict: dict
        Model metadata returned by dojo_client.get_model_info()
    dc: DojoClient
        The client that fetches the parameters from the API.
    params_filename:
        Filename for params template file. Defaults to "params.json".

    """

    output_params = {}
    model_id, model_name = (model_dict["id"], model_dict["name"])
    # (1) Parse the parameters name, description etc. from metadata retrived via dojo_api/models
    for idx, param in enumerate(dc.get_parameters(model_id)):
        annot = param['annotation']
        param_name = annot['name']
        param_default = annot['default_value']
        param_type = annot['type']

        # Add param names and defaults to output dictionary, correcting for
        # type (not data_type).
        # Massive leap of faith here that the param type is correct.
        if (param_type == 'float' or param_type == 'numerical'):
            try:
                output_params[param_name] = float(param_default)
            except Exception:
                output_params[param_name] = param_default 
        elif (param_type == 'int' or param_type == 'integer'):
            try:
                output_params[param_name] = int(param_default)
            except Exception:
                output_params[param_name] = param_default
        else:
            output_params[param_name] = param_default

        click.echo(f"Parameter {idx+1}     : {annot['name']}")
        click.echo("Description     : " + str(annot['description']).replace('\n',' '))
        click.echo(f"Type            : {annot['type']}")
        click.echo(f"Unit            : {annot['unit']}")
        click.echo(f"Unit Description: {annot['unit_description']}")
        click.echo(f"Default Value   : {annot['default_value']}")
        click.echo()

    # Reprint default parameter as examples.
    click.echo('Example parameters:')
    for k, v in output_params.items():
        click.echo(f'{k}: {v}')

    # Write the output_params as a template to file.
    with open(params_filename, 'w') as f:
        json.dump(output_params, f, indent=4)

    click.echo(f"\nExample {model_name} version {model_id} template parameters file written to {params_filename}.")

        
def print_versions(model: str, versions: dict):
    """
    Description
    -----------
    Print the list of versions for a model.

    Parameters
    ----------
    model: str
        The name of the model.
    versions: dict
        JSON returned by dojo_client.get_verions() in the format 
        {
        "current_version": "21fe6a15-f0a5-4ea3-a813-1e33d37f948d",
        "prev_versions": [],
        "later_versions": []
        }
    """

    click.echo(f'\nAvailable versions of "{model}":\n')
    
    click.echo('Current Version')
    click.echo(f'"{versions["current_version"]}"')

    click.echo('\nPrevious Versions')
    for pv in versions["prev_versions"]:
        click.echo(f'"{pv}"')

    click.echo('\nLater Versions')
    for lv in versions["later_versions"]:
        click.echo(f'"{lv}"')

    click.echo()


@click.group()
def cli():
    pass

@cli.command()
@click.option("--id", type=str, help="the container id")
@click.option("--name", type=str, help="the container name")
@click.option("--config", type=str, default=".config", help="configuration json filename (defaults to .config)")
def results(id, name, config):
    """Get the results from a stopped model run container by either id or name."""

    if (id is None and name is None):
        click.echo('\nEither --id (container id) or --name (container name) is required.\n')
        return
    
    dc = DojoClient(config)
    dc.get_results(id, name)


@cli.command()
@click.option("--model", type=str, help="the model name e.g. CHIRPS-Monthly")
@click.option("--config", type=str, default=".config", help="configuration json filename (defaults to .config)")
@click.option("--version", type=str, default=None, help="optional version id e.g. ceedd3b0-f48f-43d2-b279-d74be695ed1c")
def describe(model, version, config):
    """Print a description of the model."""

    if (model is None and version is None):
        click.echo('\nEither --model or --version is required.\n')
        return

    if version is None:
        click.echo(f'\nGetting the description of "{model}" ...\n')
    else:
        click.echo(f'\nGetting the description of model version "{version}" ...\n')

    dc = DojoClient(config)
    model_dict = dc.get_model_info(model, version)
    param_dicts = dc.get_parameters(model_dict["id"])

    if (model_dict == None):
        click.echo(f"\n No meta data is available for this model.\n")
        return

    print_description(model_dict, param_dicts)


@cli.command()
@click.option("--config", type=str, default=".config", help="configuration json filename (defaults to .config)")
def listmodels(config):
    """List available models."""
    click.echo("\nListing available models ...\n")

    dc = DojoClient(config)

    models = dc.get_available_models() 
    for idx, m in enumerate(models):
        click.echo(f'({idx+1:>2d}) {m}')


@cli.command()
@click.option("--model", type=str, help="the model name e.g. CHIRPS-Monthly")
@click.option("--config", type=str, default=".config", help="configuration json filename (defaults to .config)")
@click.option("--version", type=str, default=None, help="optional version id e.g. ceedd3b0-f48f-43d2-b279-d74be695ed1c")
def outputs(model, config, version):
    """Print descriptions of the output and accessory files produced by a model."""

    if (model is None and version is None):
        click.echo('\nEither --model or --version is required.\n')
        return

    if version is None:
        click.echo(f'\nGetting output file information for "{model}" ...')
    else:
        click.echo(f'\nGetting output file information for model version "{version}" ...')

    dc = DojoClient(config)
    model_dict = dc.get_model_info(model, version)
    if model is None:
        model = model_dict["name"]
    model_id = model_dict["id"]
    outputfile_dict = dc.get_outputfiles(model_id)
    accessories_dict = dc.get_accessories(model_id)
    # Call a seperate print_outputfiels function to keep things clean.
    print_outputs(model, model_id, outputfile_dict, accessories_dict)


@cli.command()
@click.option("--model", type=str, help="the model name e.g. CHIRPS-Monthly")
@click.option("--config", type=str, default=".config", help="configuration json filename (defaults to .config)")
@click.option("--version", type=str, default=None, help="optional version id e.g. ceedd3b0-f48f-43d2-b279-d74be695ed1c")
def parameters(model, config, version):
    """Print the parameters required to run a model."""
    
    if (model is None and version is None):
        click.echo('\nEither --model or --version is required.\n')
        return

    if version is None:
        click.echo(f'\nGetting parameters for "{model}" ...')
    else:
        click.echo(f'\nGetting parameters for model version "{version}" ...')

    dc = DojoClient(config)
    model_dict = dc.get_model_info(model, version)

    if (model_dict == None):
        click.echo(f'\nNo model data is available for this model.\n')
        return

    # Call a seperate print_params function to keep things clean.
    print_params(model_dict, dc)


@cli.command()
@click.option("--model", type=str, default=None, help="the model name e.g. CHIRPS-Monthly")
@click.option("--config", type=str, default=".config", help="configuration json filename (defaults to .config)")
@click.option("--paramsfile", type=str, default="params_template.json", help="model run parameters filename")
@click.option("--params", type=str, default=None, help='json parameters e.g. --params=\{"temp": 0.05\}')
@click.option("--outputdir", type=str, default=None, help="model output directory")
@click.option("--version", type=str, default=None, help="optional version id e.g. ceedd3b0-f48f-43d2-b279-d74be695ed1c")
@click.option("--attached", type=bool, default=True, help="wait for model completion")
def runmodel(model, config, paramsfile, params, outputdir: str = None, version: str = None, attached: bool = True):
    """Run a model."""

    # Confirm options and params.
    if (model is None and version is None):
        click.echo('\nEither --model or --version is required.\n')
        return
    elif params==None:
        # If --params json is not passed, then --paramsfile, or the default --paramsfile, must exist.
        # Try opening the file before running the model.
        if not exists(paramsfile):
            click.echo("\n--paramsfile not found and --params is blank.\nOne of either --paramsfile or --params is required.\n")
            return

    dc = DojoClient(config)

    # Get the model_id and image from the model_name or version.
    model_dict = dc.get_model_info(model, model_id=version)
    if version is None:
        version = model_dict["id"]
    elif model is None:
        model = model_dict["name"]

    # Check if the user is attempting to run a model that does not have an image.
    if len(model_dict["image"].strip()) == 0:
        click.echo(f'{model} version {version} does not have a Docker image associated with it and therefore cannot be run.')
        click.echo(f'\nThe following versions of {model} have images and are available to run:')
        versions = dc.get_model_versions_with_images(model)
        
        if len(versions) == 0:
            click.echo('\nNo versions of this model with an image are available.')
        else:
            for t in versions:
                click.echo(f'created date: {t[0]}  version: {t[1]}')
        return

    click.echo(f"\nRunning model {model} version \"{version}\" ...\n")

    dc.run_model(model, params, paramsfile, version, local_output_folder = outputdir, run_attached=attached)


@cli.command()
@click.option("--model", type=str, help="the model name e.g. CHIRPS-Monthly")
@click.option("--config", type=str, default=".config", help="configuration json filename (defaults to .config)")
def versions(model, config):
    """Print all registered versions of a model."""
    
    if model==None:
        click.echo("\n--model is a required option.\n")
        return

    click.echo(f"\nGetting versions of \"{model}\" ...")

    dc = DojoClient(config)
    versions = dc.get_versions(model)

    if (versions == None):
        click.echo(f"\n No versions are available for this model.\n")
        return

    # Call a seperate print_versions function to keep things clean.
    print_versions(model, versions)

if __name__ == "__main__":     
    cli()
