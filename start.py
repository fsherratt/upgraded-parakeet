#!/usr/bin/env python3
"""
Programmatically launch modules
"""
import argparse
import select
import subprocess
import signal

from modules import data_types, load_config


# Add to the launch list any modules that can be run
# TAG: module + startup commands
launch_list = {
    "rs_depth": ["modules.realsense", "-o", "depth"],
    "rs_pose": ["modules.realsense", "-o", "pose"],
    "rs_color": ["modules.realsense", "-o", "color"],
}
# ---DO NOT MODIFY BELOW THIS LINE---


def parse_cli() -> argparse.Namespace:
    """
    Run argparse on the input arguments to find modules and config file
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


def parse_startup_yaml(config_file: str, current_startup_list=None) -> list:
    """
    Convert yaml startup file into a list of StartupItem
    """
    if current_startup_list is None:
        current_startup_list = []

    conf = load_config.from_file(config_file, use_cli_input=False)

    for _ in conf.startup_list:
        current_startup_list.append(
            load_config.conf_to_named_tuple(data_types.StartupItem, _)
        )

    return current_startup_list


def parse_startup_cli(modules: list, current_startup_list=None) -> list:
    """
    Convert module command line input into a list of StartupItem
    """
    if current_startup_list is None:
        current_startup_list = []

    for module in modules:
        if len(module) > 1:
            debug = bool(module[1] == "true" or module[1] == "True")

        if len(module) == 1:  # Only modules specified
            new_item = data_types.StartupItem(
                module=module[0], debug=False, config_file=None, process_name=None
            )
        elif len(module) == 2:  # Debug specified
            new_item = data_types.StartupItem(
                module=module[0], debug=debug, config_file=None, process_name=None
            )
        elif len(module) == 3:  # Config file specified
            new_item = data_types.StartupItem(
                module=module[0], debug=debug, config_file=module[2], process_name=None,
            )
        elif len(module) == 4:  # Process name specified
            new_item = data_types.StartupItem(
                module=module[0],
                debug=debug,
                config_file=module[2],
                process_name=module[3],
            )
        else:
            continue

        current_startup_list.append(new_item)

    return current_startup_list


def launch_process(launch_item: data_types.StartupItem) -> subprocess.Popen:
    """
    Launch a subprocess from the provided StartupItem definition
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


def launch_processes(startup_items: list) -> list:
    """
    Launch all subprocesses in the specified list and collect their resulting Popen objects
    """
    process_list = []

    for startup_item in startup_items:
        new_process = launch_process(startup_item)

        if new_process is None:
            continue

        process_list.append(new_process)
        print(
            "New process created\tTAG:{}\tPID:{}".format(
                startup_item.module, new_process.pid
            )
        )

    return process_list


def process_is_alive(process_list: list) -> list:
    """
    Filter Popen oject list and remove closed processes
    """
    dead_processes = list(
        filter(lambda process: process.poll() is not None, process_list)
    )

    for process in dead_processes:
        print("Process PID:{} exited with code:{}".format(process.pid, process.poll()))
        process_list.remove(process)

    return process_list


def monitor_stderr(process_list: list, blocking_timeout=1):
    """
    Monitor the standard error stream of a list of Popen ojects
    """
    err_streams = [p.stderr for p in process_list]
    rstreams, _, _ = select.select(err_streams, [], [], blocking_timeout)

    for stream in rstreams:
        error_string = stream.read()

        if error_string:
            # TODO: Log output of subprocess stderr
            print(error_string.decode("utf-8"))


def kill_processes(process_list: list):
    for process in process_list:
        process.terminate()


if __name__ == "__main__":
    startup_list = []
    args = parse_cli()

    # Parse module list from CLI
    if args.module:
        startup_list = parse_startup_cli(args.module)

    # Parse module list from config file
    if args.config_file is not None:
        startup_list = parse_startup_yaml(args.config_file, startup_list)

    processes = launch_processes(startup_list)

    # Monitor until all processes are finish
    while processes:
        try:
            processes = process_is_alive(processes)
            monitor_stderr(processes)

        except KeyboardInterrupt:
            print("Start.py: Keyboard interrupt - stopping all processes")
            kill_processes(processes)

    print("Start.py: Closing - All processes finished")
