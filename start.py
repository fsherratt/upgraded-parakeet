#!/usr/bin/env python3
"""
Startup modules
"""
import argparse
import subprocess
import time

from modules import data_types, load_config

# Add to the launch list any modules that can be run
launch_list = {
    # TAG: module startup code
    "rs_depth": ["modules.realsense", "-o", "depth"],
    "rs_pose": "modules.realsense -o pose",
    "rs_color": "modules.realsense -o color",
    "map_predepth": "modules.map_preprocess -o depth",
}

# ---DO NOT MODIFY BELOW THIS LINE---
startup_list = []

parser = argparse.ArgumentParser(description="Startup module(s)")
parser.add_argument(
    "-m",
    "-M",
    "--module",
    action="append",
    nargs="+",
    default=None,
    help="[Module Name] [Debug] [Config File] [Process Name]",
)
parser.add_argument(
    "-c",
    "-C",
    "--config_file",
    type=str,
    default=None,
    help="Startup list config file",
)
args = parser.parse_known_args()[0]


# Parse module list from config file
if args.config_file is not None:
    conf = load_config.from_file(args.config_file, use_cli_input=False)

    for _ in conf.startup_list:
        startup_list.append(load_config.conf_to_named_tuple(data_types.StartupItem, _))


# Parse module list from CLI
if args.module:
    for _ in args.module:
        if len(_) == 1:  # Only modules specified
            new_item = data_types.StartupItem(
                module=_[0], debug=False, config_file=None, process_name=None
            )

        elif len(_) == 2:  # Debug specified
            new_item = data_types.StartupItem(
                module=_[0], debug=_[1], config_file=_[2], process_name=None
            )
        elif len(_) == 3:  # Config file specified
            new_item = data_types.StartupItem(
                module=_[0], debug=_[1], config_file=_[2], process_name=None
            )

        elif len(_) == 4:  # Process name specified
            new_item = data_types.StartupItem(
                module=_[0], debug=_[1], config_file=_[2], process_name=_[3]
            )

        startup_list.append(new_item)


# Launch modules
for _ in startup_list:
    try:
        item = launch_list.get(_.module)
    except KeyError:
        print("Oh No")

    argslist = ["python3", "-m"]
    argslist.extend(launch_list[_.module])

    if _.config_file is not None:
        argslist.extend(["-c", _.config_file])

    if _.debug:
        argslist.extend(["-d"])

    if _.process_name is not None:
        argslist.extend(["-pn", _.process_name])

    p = subprocess.Popen(args=argslist, start_new_session=True)

    print("New process created\tTAG:{}\tPID:{}".format(_.module, p.pid))

time.sleep(10)
