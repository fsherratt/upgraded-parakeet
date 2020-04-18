from omegaconf import OmegaConf

def load_config( config_file ):
    conf = OmegaConf.load(config_file)
    confCli = OmegaConf.from_cli()

    conf = OmegaConf.merge(conf, confCli)

    return conf

if __name__ == "__main__":
    conf = load_config('conf/realsense_d435.yaml')

    print(conf.pretty())