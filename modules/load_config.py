from omegaconf import OmegaConf

def load_config( config_file=None, use_cli_input=True ):
    if config_file is None and not use_cli_input:
        raise AttributeError('No input specified')

    if use_cli_input:
        confCli = OmegaConf.from_cli()

    if config_file is not None:
        conf = OmegaConf.load(config_file)

    if use_cli_input and config_file is not None:
        conf = OmegaConf.merge(conf, confCli)
    elif use_cli_input:
        conf = confCli

    return conf
