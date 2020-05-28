# Module Startup
A guide to launching modules

## Table of Contents
- [Useful Links](#links)
- [Launching a Module](#launching)
- [Prepare a Module for Launching](#intergrating)


# <a name="links"></a>Useful Links
- [Subprocess management](https://docs.python.org/3.6/library/subprocess.html)

# <a name="launching"></a>Launching a Module
This section covers how to use start.py to launch up modules

## Launch Commands

### _start.py_ Command
- -c
- -m

### Module Commands
- -c Configuration_file
- -d enable debug
- -p process name

## Startup Config File
The yaml file must included a list with name `startup_list` and each item in the list must include all items from the [StartupItem](Publisher_List.md#startItem) data type.

As an example 

See [config.md](config.md) for more detail on configuration files.

# <a name="intergrating"></a>Prepare a Module for Launching
This section details how to prepare your module for use with the launching system

## Prepare Module

- -c Configuration_file
- -d enable debug
- -p process name

## Updating start.py
At the top of _start.py_ is a dictionary of TAGs and there associated startup commands . To add your module to the start command just add

```python
launch_list = {
    "ex_tag": ["modules.example", "-x", "other_arguments"],
    ...
}
```

The above line would execute the command

```python
python3 -m modules.example -x other_argument
```