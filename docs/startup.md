# Module Startup
A guide to launching modules

## Table of Contents
- [Useful Links](#links)
- [Launching a Module](#launching)
- [Prepare a Module for Launching](#intergrating)

# <a name="links"></a>Useful Links
- [Subprocess management](https://docs.python.org/3.6/library/subprocess.html)

# <a name="launching"></a>Launching a Module
This section covers how to use startup a modules using the repository launching methods.

## Launch Commands
The `start.py` script allows modules to be started and monitored. Modules implementing the startup object can also be started directly, this is described [below](#module_cmd).

### start.py Command
The following commands can be used with the start.py
|Argument| Description |
|:---|:---|
|`-c`, `-C`, `--config_file` | Startup config file address |
|`-m`, `-M`, `--module` | Module Tag \[Debug \[Config file \[Process name\]\]\] |

The module argument must be specified for each module

Example uses are presented below
```bash
$ ./start.py -M rs_depth true conf/realsense.yaml depth_camera -M rs_color true
```
```bash
$ ./start.py -C conf/startup.yaml
```

### Startup Tag List
Below is a list of availabe tags and the module they are associated with.
| Tag| Module |
|:---|:---|
|`rs_pose` | Realsense T265 Pose data |
| `rs_depth` | Realsense D435 Depth Image |
| `rs_color` | Realsense D435 Color RGB Image |


### <a name="module_cmd"></a>Module Commands
Modules can be launched directly using the following arguments
|Argument| Description |
|:---|:---|
| `-c`, `-C`, `--config_file` | Configuration file address |
| `-d`, `-D`, `--debug` | Enable debuging output |
| `-pn`, `-PN`, `--process_name` | Process friendly name |

When launched like this the process std_err will not be captured automatically, this can useful when debugging code.

Note it must be run as a python module using the `-m` python argument, see below.

```python
python3 -m modules.example -c conf/test.yaml -D -pn example_process
```

## Startup Config File
Modules can be launched and configued from a YAML file allowing them to be quickly launched

An example startup file is presented below. The yaml anchor must include all elements of the data type [StartupItem](Publisher_List.md#startItem). The alias then only needs to override fields that need to be modified.

```yaml
templates: &node
    module: null
    config_file: null
    process_name: null
    debug: false

startup_list:
    -
        <<: *node
        module: 'rs_pose'

    -
        <<: *depth
        module: 'rs_depth'
        debug: true
        process_name: 'depth_camera

```

See [config.md](config.md) for more detail on configuration files.

# <a name="intergrating"></a>Prepare a Module for Launching
This section details how to prepare your module for use with the launching system

## Adding modules to start.py
At the top of _start.py_ is a dictionary of TAGs and there associated startup commands . To add your module to the start command just add

```python
launch_list = {
    "ex_tag": ["modules.example", "-x", "other_arguments"],
    ...
}
```

The above line would execute the command

```bash
$ python3 -m modules.example -x other_arguments...
```

## Module argument parsing
```python
if __name__ == "__main__":
    args = startup.ParseArguments()

    # Do something with args
```

The args return object contains the following elements
|Attribute|Description|
|:---|:---|
|`args.option` | List of module specified launch arguments |
|`args.config` | Config file |
|`args.debug` | Enable/Disable debugging |
|`args.process_name` | Frieldly process name |

## The setup object
Each module requires to have a child class of the `startup.Startup` class. This implements thread health monitoring and process heartbeats