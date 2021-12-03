import click
from dojo_client import DojoClient
import json
from os.path import exists
import re

def print_params(metadata, model: str, params_filename: str = 'params_template.json'):
    """
    Description
    -----------
    (1) Print model parameters and instructions derived from the directive 
    portion of the metadata.

    (2) Write the json structure to params.json or specified filename.

    Parameters
    ----------
        metadata: dict
            Model metadata returned by dojo_client.get_metadata()
        model: str
            The name of the model.
        params_filename:
            Filename for params template file. Defaults to "params.json".

    """

    # Parse command parameters from the 'command_raw' directive.
    # "command": "python3 run_chirps_tiff.py --name=CHIRTSmax --month={{ month }} --year={{ year }} --bbox='{{ bounding_box }}'"
    # "command_raw": "python3 run_chirps_tiff.py --name=CHIRPS --month=01 --year=2021 --bbox='[[33.512234, 2.719907], [49.98171,16.501768]]'",
    print(f'\nModel run parameters for {model}')
    params = {}

    directive = metadata['directive']

    # Parse the param names from "command" and the param exmaples from
    # "commnad_raw". Rely on param position for matching since the "command"
    # and "command_raw" param names can differ.

    command = directive["command"]
    param_array = command.split("--")

    command_raw = directive["command_raw"]
    param_raw_array = command_raw.split("--")

    assert(len(param_array) == len(param_raw_array))

    for idx, param_pair in enumerate(param_array):
        if str(param_pair).lower().startswith('python'):
            continue

        # command: Split the param_pair to get param_name
        sa = param_pair.split("=")
        
        # Skip the model name; it is added as a discreet cli parameter.
        if sa[0] == 'name':
            continue
        param_name = re.sub("[\{\}']", '', sa[1]).strip()

        # command_raw: Split the param_pair_raw to get example.
        param_pair_raw = param_raw_array[idx]
        sa = param_pair_raw.split("=")
        param_example = str(sa[1]).strip()

        # strip any quotes from string parameters
        param_example = re.sub("[']", '', param_example).strip()

        # Print the example param:value pair.
        print(f'# {param_name}: {param_example}')

        # Add the param: value pair to the dictionary.
        params[param_name] = param_example

    # Write the template to file.
    with open(params_filename, 'w') as f:
        json.dump(params, f)

    click.echo(f"\nTemplate {model} parameters file written to {params_filename}.")

@click.group()
def cli():
    pass

@cli.command()
@click.option("--model", type=str, help="the model name e.g. CHIRPS-Monthly")
@click.option("--config", type=str, default=".config", help="configuration json filename e.g. sample.config")
def printparams(model, config):
    """Print the parameters required to run a model."""
    click.echo(f"Getting parameters for {model} ...")
    
    dc = DojoClient(config)
    metadata = dc.get_metadata(model)
    #generate_model_params_file(metadata, model)
    print_params(metadata, model)

@cli.command()
@click.option("--config", type=str, default=".config", help="configuration json filename e.g. sample.config")
def listmodels(config):
    """List available models."""
    click.echo("Listing available models...\n")

    dc = DojoClient(config)

    models = dc.get_available_models() 
    for idx, m in enumerate(models):
        click.echo(f'({idx+1}) {m}')


@cli.command()
@click.option("--model", type=str, default=None, help="the model name e.g. CHIRPS-Monthly")
@click.option("--config", type=str, default=".config", help="configuration json filename e.g. sample.config")
@click.option("--paramsfile", type=str, default="params_template.json", help="model run parameters filename")
@click.option("--params", type=str, default=None, help='json parameters e.g. --params=\{"temp": 0.05\}')
@click.option("--outputdir", type=str, default=None, help="model output directory")
def runmodel(model, config, paramsfile, params, outputdir: str = None):
    """Run a model."""

    if model==None:
        click.echo("runmodel --model parameter is required.")
        return
    elif params==None:
        # If --params json is not passed, then --paramsfile, or the default --paramsfile, must exist.
        # Try opening the file before running the model.
        if not exists(paramsfile):
            click.echo("\n--paramfile not found and --params is blank.\nOne of either --paramfile or --params is required.\n")
            return

    click.echo(f"Running {model}")

    dc = DojoClient(config)
    dc.run_model(model, params, paramsfile, local_output_folder = outputdir)

if __name__ == "__main__":     
    cli()
    #printparams(model="dummy-model", config=".config")
    #listmodels(config=".config")
    #runmodel(model="dummy-model", config=".config", params="dummy-model_params.txt")