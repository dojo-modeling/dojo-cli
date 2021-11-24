"""
"""

import click
from dojo_client import DojoClient




def generate_model_params_file(metadata, model_name):
    """
    Generate and write to file a list of model parameters and instructions 
    derived from the directive portion of the metadata.
    """

    params_output = []
    param_list = []
    directive = metadata['directive']

    params_output.append("# Lines starting with # are comments.")

    # Parse and add the command parameters.
    # "command_raw": "python3 run_chirps_tiff.py --name=CHIRPS --month=01 --year=2021 --bbox='[[33.512234, 2.719907], [49.98171,16.501768]]'",
    params_output.append(f'# Model run parameters for {model_name}')
    params_output.append('# Example parameters:')
    command_raw = directive["command_raw"]
    param_array = command_raw.split("--")
    for param_pair in param_array:
        if str(param_pair).lower().startswith('python'):
            continue

        # split the param_pair
        sa = param_pair.split("=")
        
        # keep a list of the parameter names
        param_name = sa[0]
        param_list.append(param_name)

        param_example = str(sa[1]).strip()

        if param_name == 'name':
            continue

        # strip the quotes from string parameters
        if param_example[0] == "'":
            param_example = param_example[1:-1]

        # add the example param:value pair.
        params_output.append(f'# {param_name}: {param_example}')

    params_output.append('#\n# Set run parameter values here:')
    for p in param_list:
        params_output.append(f'{p}: ')

    with open(f'{model_name}_params.txt', 'w') as f:
        f.writelines("%s\n" % line for line in params_output)

@click.group()
def cli():
    pass

@cli.command()
@click.option("--model_name", type=str, default=None, help="the model name e.g. CHIRPS-Monthly")
@click.option("--config", type=str, default=".config", help="configuration json filename e.g. sample.config")
def get_model_params(model_name, config):
    """Get the parameters required to run a model."""
    click.echo(f"Getting parameters for {model_name} ...")
    
    dc = DojoClient(config)
    metadata = dc.get_metadata(model_name)
    generate_model_params_file(metadata, model_name)

    click.echo(f"{model_name} parameters file written to {model_name}_params.txt.")

@cli.command()
@click.option("--config", type=str, default=".config", help="configuration json filename e.g. sample.config")
def list_models(config):
    """List available models."""
    click.echo("Listing available models...\n")

    dc = DojoClient(config)

    models = dc.get_available_models() 
    for idx, m in enumerate(models):
        click.echo(f'({idx+1}) {m}')


@cli.command()
@click.option("--model_name", type=str, default=None, help="the model name e.g. CHIRPS-Monthly")
@click.option("--config", type=str, default=".config", help="configuration json filename e.g. sample.config")
@click.option("--params", type=str, default="params.txt", help="model run parameters filename e.g. params.txt")
def run_model(model_name, config, params):
    """Run a model."""
    click.echo(f"Running {model_name}")

    dc = DojoClient(config)
    dc.run_model(model_name, params)

if __name__ == "__main__":     
    cli()
    #get_parameters(model_name="CHIRPS-Monthly", config=".config")
    #run_model(model_name="CHIRPS-Monthly", config=".config", params="CHIRPS-Monthly_params.txt")