from omegaconf import OmegaConf

def from_file(config_file=None, use_cli_input=True):
    if config_file is None and not use_cli_input:
        raise AttributeError('No input specified')

    if use_cli_input:
        conf_cli = OmegaConf.from_cli()

    if config_file is not None:
        conf = OmegaConf.load(config_file)

    if use_cli_input and config_file is not None:
        conf = OmegaConf.merge(conf, conf_cli)
    elif use_cli_input:
        conf = conf_cli

    return conf
