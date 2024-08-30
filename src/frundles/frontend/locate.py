"""
# Find where a library is stored

- Florian Dupeyron <florian.dupeyron@mugcat.fr>
- August 2024

"""

from argparse import ArgumentParser, Namespace
from pathlib import Path

import logging
import sys

from ..backend import workspace

log = logging.getLogger("frontend.locate")


def setup_parser(parser: ArgumentParser):
    subparser = parser.add_parser(
        "locate", help="Find where a library is stored using its friendly name"
    )
    subparser.add_argument("friendly_name", help="Friendly name of the library")


def run(args: Namespace):
    cwd = Path.cwd()

    # Find the closest workspace
    cur_wspace_path = workspace.find_current_workspace(cwd)

    # Get the friendly name
    friendly_name = args.friendly_name

    # Find that damn library
    lib_path = workspace.locate(cur_wspace_path, friendly_name)

    if lib_path is None:
        log.error(f"Could not found library path with name '{friendly_name}'")
        sys.exit(1)

    print(lib_path)
