import sys
from os.path import exists, dirname, abspath

# Add path of the run files to the system path so VS Code can find things. 
sys.path.append(dirname(dirname(abspath(__file__))))

import click
from datetime import datetime
from dojocli.dojo_client import DojoClient
import json


def print_description(model_dict: dict):
    """
    Description
    -----------
    Called from cli.describe(). Prints the model information.

    """

    print(f'NAME\n----\n{model_dict["name"]}\n')
    print(f'VERSION\n----\n{model_dict["id"]}\n')

    print(f'MODEL FAMILY\n------------\n{model_dict["family_name"]}\n')
    print(f'DESCRIPTION\n-----------\n{model_dict["description"]}\n')
    
    # Convert epoch time in milliseconds to seconds.
    created_at = datetime.fromtimestamp(model_dict["created_at"]/1000).strftime('%Y-%m-%d %H:%M:%S')
    print(f'CREATED DATE\n------------\n{created_at}\n')
    
    print('CATEGORY\n--------')
    category = ''
    for i in model_dict["category"]:
        category = category + f'{i.upper()}\t'
    print(category + '\n')

    print('MAINTAINER\n------------')
    for k, v in model_dict["maintainer"].items():
        print(f'{k.upper()}: {v}')
    print()

    print(f'DOCKER IMAGE\n------------\n{model_dict["image"]}\n')

    print('PARAMETERS\n----------')
    for param_dict in model_dict["parameters"]:
        print(param_dict["display_name"])

    print()

def print_outputfiles(model: str, version: str, outputfile_dict: dict):
    """
    Description
    -----------
    Called from cli.printoutputs(). Prints information about the model output files.
    
    """

    print(f'\n"{model}" version {version} writes {len(outputfile_dict)} output file(s):\n')

    for idx, outputfile in enumerate(outputfile_dict):
        transform = outputfile["transform"]
        print(f'({idx+1}) {outputfile["path"]}: {outputfile["name"]} in {transform["meta"]["ftype"]} format with the following labeled data:')
        #print(f'({idx+1}) {outputfile["name"]} in {transform["meta"]["ftype"]} file {outputfile["path"]} with the following labeled data:')
        for transform_type in ['geo', 'date', 'feature']:
            for data_type in transform[transform_type]:
                print(f'    {data_type["name"]}: {data_type["display_name"]}')
        print()
    print()

def print_params(model: str,  model_dict: dict, params_filename: str = 'params_template.json'):
    """
    Description
    -----------
    (1) Print model parameters and instructions derived from the model metadata.

    (2) Write the json structure to params.json or specified filename.

    Parameters
    ----------
    model_dict: dict
        Model metadata returned by dojo_client.get_model_info()
    model: str
        The name of the model.
    params_filename:
            Filename for params template file. Defaults to "params.json".

    """

    output_params = {}
    # (1) Parse the parameters name, description etc. from metadata retrived via dojo_api/models
    if "parameters" in model_dict:
        for idx, p in enumerate(model_dict["parameters"]):
            param_name = p["name"]
            param_default = p["default"]
            param_type = p['type']

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

            print(f"Parameter {idx+1}     : {p['display_name']}")
            print("Description     : " + str(p['description']).replace('\n',' '))
            print(f"Type            : {p['type']}")
            print(f"Unit            : {p['unit']}")
            print(f"Unit Description: {p['unit_description']}")
            print(f"Default Value   : {p['default']}")
            print()

        # Reprint default parameter as examples.
        print('Example parameters:')
        for k, v in output_params.items():
            print(f'{k}: {v}')

        # Write the output_params as a template to file.
        with open(params_filename, 'w') as f:
            json.dump(output_params, f, indent=4)

        click.echo(f"\nExample {model} template parameters file written to {params_filename}.")

    else:
        print(f'\nNo model run parameters found for {model}:\n')
    """        
        # or parse command parameters from the 'command_raw' directive.
        elif 'directive' in metadata:
            directive = metadata['directive']
            if (not directive == None 
                and "command_raw" in directive 
                and directive["command_raw"] != ""
                and "command" in directive):

                command_raw = directive["command_raw"]
                command = directive["command"]
                print('\nExample parameters:\n')
        
                for param_name in param_type_dict:
                    if not command.__contains__(param_name):
                        continue
                    # Find the token before the param_name.
                    # For example, the parameter bounding_box in the CHIRPS models.
                    # command:     python3 run_chirps_tiff.py --name=CHIRPS --month={{ month }} --year={{ year }} --bbox='{{ bounding_box }}'
                    splitter = "{{ " + param_name + " }}"
                    sa = command.split(splitter) 
                    # sa[0] = "python3 run_chirps_tiff.py --name=CHIRPS --month={{ month }} --year={{ year }} --bbox='{{ "
                    # Strip trailing whitespace from sa[0] and any single quotes.
                    param_marker =  re.sub("[']", "", sa[0].strip())
                    # Now param_marker = bounding_box python3 run_chirps_tiff.py --name=CHIRPS --month={{ month }} --year={{ year }} --bbox=
                    # Next split on a space, and take the last symbol in the array.
                    sa = param_marker.split(" ")
                    param_marker = sa[-1] 
                    # In this example, param_marker is now --bbox=; we can use that to parse command_raw to get an example parameter.
                    # command_raw: python3 run_chirps_tiff.py --name=CHIRPS --month=01 --year=2021 --bbox='[[33.512234, 2.719907], [49.98171,16.501768]]'               
                    sa = command_raw.split(param_marker)
                    param_value = sa[1] 
                    # param_example = '[[33.512234, 2.719907], [49.98171,16.501768]]'
                    # In other instances, there may be trailing params in param_example,
                    # e.g. for CHIRPS model param month where the param_example would
                    # be: 
                    # 01 --year=2021 --bbox='[[33.512234, 2.719907], [49.98171,16.501768]]'
                    # in this example.
                    # Use the shlex library to split on spaces but not inside quotes.
                    # Strip the quotes via posix=True (default setting for shlex)
                    param_value = shlex.split(param_value, posix=True)[0].strip()                       
                    output_params[param_name] = param_value

                    print(f'{param_name}: {param_value}')        
            else:
                for param_name in param_type_dict:
                    output_params[param_name] = ""
    """
        
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

    print(f'\nAvailable versions of "{model}":\n')
    
    print('Current Version')
    print(f'"{versions["current_version"]}"')

    print('\nPrevious Versions')
    for pv in versions["prev_versions"]:
        print(f'"{pv}"')

    print('\nLater Versions')
    for lv in versions["later_versions"]:
        print(f'"{lv}"')

    print()


@click.group()
def cli():
    pass


@cli.command()
@click.option("--model", type=str, help="the model name e.g. CHIRPS-Monthly")
@click.option("--config", type=str, default=".config", help="configuration json filename (defaults to .config)")
@click.option("--version", type=str, default=None, help="optional version id e.g. ceedd3b0-f48f-43d2-b279-d74be695ed1c")
def describe(model, version, config):
    """Print a description of the model."""

    if (model is None and version is None):
        click.echo('\neither --model or --version is required.\n')
        return

    if version is None:
        click.echo(f'\nGetting the description for "{model}" ...')
    else:
        click.echo(f'\nGetting the description for model version "{version}" ...')

    dc = DojoClient(config)
    model_dict = dc.get_model_info(model, version)

    if (model_dict == None):
        click.echo(f"\n No meta data is available for this model.\n")
        return

    print_description(model_dict)


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
    """Print descriptions of the output files produced by a model."""

    if (model is None and version is None):
        click.echo('\neither --model or --version is required.\n')
        return

    if version is None:
        click.echo(f'\nGetting output file information for "{model}" ...')
    else:
        click.echo(f'\nGetting output file information for model version "{version}" ...')

    dc = DojoClient(config)
    model_dict = dc.get_model_info(model, version)
    model_id = model_dict["id"]
    outputfile_dict = dc.get_outputfiles(model_id)
    # Call a seperate print_params function to keep things clean.
    print_outputfiles(model, model_id, outputfile_dict)


@cli.command()
@click.option("--model", type=str, help="the model name e.g. CHIRPS-Monthly")
@click.option("--config", type=str, default=".config", help="configuration json filename (defaults to .config)")
@click.option("--version", type=str, default=None, help="optional version id e.g. ceedd3b0-f48f-43d2-b279-d74be695ed1c")
def parameters(model, config, version):
    """Print the parameters required to run a model."""
    
    if (model is None and version is None):
        click.echo('\neither --model or --version is required.\n')
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
    print_params(model, model_dict)


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

@cli.command()
@click.option("--model", type=str, default=None, help="the model name e.g. CHIRPS-Monthly")
@click.option("--config", type=str, default=".config", help="configuration json filename (defaults to .config)")
@click.option("--paramsfile", type=str, default="params_template.json", help="model run parameters filename")
@click.option("--params", type=str, default=None, help='json parameters e.g. --params=\{"temp": 0.05\}')
@click.option("--outputdir", type=str, default=None, help="model output directory")
def runmodel(model, config, paramsfile, params, outputdir: str = None):
    """Run a model."""

    if model==None:
        click.echo("\n--model is a required option.\n")
        return
    elif params==None:
        # If --params json is not passed, then --paramsfile, or the default --paramsfile, must exist.
        # Try opening the file before running the model.
        if not exists(paramsfile):
            click.echo("\n--paramfile not found and --params is blank.\nOne of either --paramfile or --params is required.\n")
            return

    click.echo(f"\nRunning \"{model}\" ...\n")

    dc = DojoClient(config)
    dc.run_model(model, params, paramsfile, local_output_folder = outputdir)


if __name__ == "__main__":     
    cli()
    #runmodel(model="CHIRPS-Monthly", params=None, config=".config", paramsfile="params_template.json", outputdir=None)
