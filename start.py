#!/usr/bin/env python3
"""
Startup modules
"""
import argparse

from modules import data_types, load_config


startup_list = []

parser = argparse.ArgumentParser(description="Startup module(s)")
parser.add_argument(
    "-m",
    "-M",
    "--module",
    action="append",
    nargs="+",
    default=None,
    help="[Module Name] [Config File] [Process Name]",
)
parser.add_argument(
    "-c",
    "-C",
    "--config_file",
    type=str,
    nargs=1,
    default=None,
    help="Startup list config file",
)
args = parser.parse_args()


# Parse module list from config file
if args.config_file:
    conf = load_config.from_file(args.config_file, use_cli_input=False)

    for _ in conf.startup_list:
        startup_list.extend(load_config.conf_to_named_tuple(data_types.StartupItem, _))


# Parse module list from CLI
if args.module:
    for _ in args.module:
        if len(_) == 1:  # Only modules specified
            new_item = data_types.StartupItem(
                module=_[0], config_file=None, process_name=None
            )

        elif len(_) == 2:  # Config file specified
            new_item = data_types.StartupItem(
                module=_[0], config_file=_[1], process_name=None
            )

        elif len(_) == 3:  # Process name specified
            new_item = data_types.StartupItem(
                module=_[0], config_file=_[1], process_name=_[2]
            )

        startup_list.extend(new_item)


# Launch modules
for _ in startup_list:
    print(_)
