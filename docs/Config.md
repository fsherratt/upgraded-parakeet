# Architecture Config Guide
Some description of what config is

## Useful links
- [OmegaConf config files](https://omegaconf.readthedocs.io/en/latest/)
- [YAML Tutorial: Everything You Need to Get Started in Minutes](https://rollout.io/blog/yaml-tutorial-everything-you-need-get-started/)
- [YAML Ancors](https://confluence.atlassian.com/bitbucket/yaml-anchors-960154027.html)

## How to use
Config arguments are defined in `.yaml` files. These are then opened and parsed using the OmegaConf library

## Converting to DataType
It can be useful to pass configurations around as a NamedTuple structure. For this the `conf_to_named_tuple` function can be used. This function requires all fields in the tuple are declared in the YAML file.