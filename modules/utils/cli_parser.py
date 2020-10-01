"""
This module handles all startup classes
"""
import argparse


def standard_parser(multiple_processes=False) -> argparse.ArgumentParser:
    """
    Parse standard command line inputs for launchable module
    """
    parser = argparse.ArgumentParser(
        description="Upgraded Parakeet Standard parser", allow_abbrev=False
    )
    parser.add_argument(
        "-p",
        "-P",
        "--process",
        type=str,
        required=multiple_processes,
        help="Realsense stream type to launch",
    )
    parser.add_argument(
        "-c",
        "-C",
        "--config",
        type=str,
        required=False,
        default=None,
        help="Configuration file",
    )
    parser.add_argument(
        "-d",
        "-D",
        "--debug",
        action="store_true",
        required=False,
        default=False,
        help="Enable debug output",
    )

    return parser


def parse_cli_input(multiple_processes=False) -> argparse.Namespace:
    parser = standard_parser(multiple_processes)
    return parser.parse_known_args()[0]
