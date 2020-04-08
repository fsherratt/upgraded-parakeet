from omegaconf import OmegaConf
conf = OmegaConf.load('conf/test.yaml')
confCli = OmegaConf.from_cli()

conf = OmegaConf.merge(conf, confCli)

print(conf.pretty())
print(conf.server.port)