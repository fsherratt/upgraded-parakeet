#!/usr/bin/env python3
"""
Progrmatically launch modules
"""
import argparse
import select
import subprocess

from modules import data_types, load_config

# Add to the launch list any modules that can be run
launch_list = {
    # TAG: module + startup commands
    "rs_depth": ["modules.realsense", "-o", "depth"],
    "rs_pose": ["modules.realsense", "-o", "pose"],
    "rs_color": ["modules.realsense", "-o", "color"],
    "map_predepth": ["modules.map_preprocess", "-o", "depth"],
}
# ---DO NOT MODIFY BELOW THIS LINE---


def decode_startup_yaml(config_file: str, current_startup_list=None) -> list:
    """
    """
    if current_startup_list is None:
        current_startup_list = []

    conf = load_config.from_file(config_file, use_cli_input=False)

    for _ in conf.startup_list:
        current_startup_list.append(
            load_config.conf_to_named_tuple(data_types.StartupItem, _)
        )

    return current_startup_list


def decode_startup_cli(modules: list, current_startup_list=None) -> list:
    """
    """
    if current_startup_list is None:
        current_startup_list = []

    for _ in modules:
        new_item = decode_startup_list(_)
        startup_list.append(new_item)


def decode_startup_list(module: list) -> data_types.StartupItem:
    """
    """
    item = None
    if len(module) == 1:  # Only modules specified
        item = data_types.StartupItem(
            module=module[0], debug=False, config_file=None, process_name=None
        )
    elif len(module) == 2:  # Debug specified
        item = data_types.StartupItem(
            module=module[0], debug=module[1], config_file=None, process_name=None
        )
    elif len(module) == 3:  # Config file specified
        item = data_types.StartupItem(
            module=module[0], debug=module[1], config_file=module[2], process_name=None
        )
    elif len(module) == 4:  # Process name specified
        item = data_types.StartupItem(
            module=module[0],
            debug=module[1],
            config_file=module[2],
            process_name=module[3],
        )

    return item


def launch_process(launch_item: data_types.StartupItem) -> subprocess.Popen:
    """
    """
    try:
        launch_cmd = launch_list[launch_item.module]
    except KeyError:
        print("Launch process `{}` not known".format(launch_item.module))
        return None

    argslist = ["python3", "-m"]
    argslist.extend(launch_cmd)

    if launch_item.config_file is not None:
        argslist.extend(["-c", launch_item.config_file])

    if launch_item.debug:
        argslist.extend(["-d"])

    if launch_item.process_name is not None:
        argslist.extend(["-pn", launch_item.process_name])

    return subprocess.Popen(
        args=argslist, stderr=subprocess.PIPE, start_new_session=True
    )


def parse_cli() -> argparse.Namespace:
    """
    """
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
    return parser.parse_known_args()[0]


if __name__ == "__main__":
    startup_list = []
    args = parse_cli()

    # Parse module list from CLI
    if args.module:
        decode_startup_cli(args.module)

    # Parse module list from config file
    if args.config_file is not None:
        startup_list = decode_startup_yaml(args.config_file, startup_list)

    processes = []
    # Launch modules
    for _ in startup_list:
        p = launch_process(_)

        if p is None:
            continue

        processes.append(p)
        print("New process created\tTAG:{}\tPID:{}".format(_.module, p.pid))

    while True:
        err_streams = [p.stderr for p in processes]
        rstreams, _, _ = select.select(err_streams, [], [], 1)

        for stream in rstreams:
            error_string = stream.read()

            if error_string:
                # TODO: Log errors produced of stderr
                print(error_string)

        for p in processes:
            if p.poll() is not None:
                processes.remove(p)

        if not processes:
            break
