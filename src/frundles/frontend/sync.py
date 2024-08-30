"""
# frundles sync frontend command

- Florian Dupeyron
- August 2024
"""

import logging
import argparse

from ..backend import workspace
from pathlib import Path

log = logging.getLogger("frontend.sync")


def setup_parser(parser: argparse.ArgumentParser):
    subparser = parser.add_parser("sync", help="Synchronize dependencies")  # noqa: F841


def run(args: argparse.Namespace):
    cwd = Path.cwd()

    # Find the root workspace
    root_ws_path = workspace.find_root_workspace(cwd)
    log.info(f"Synchronize workspace located in {root_ws_path}")

    # Do the proper synchronization
    workspace.sync_workspace(root_ws_path)
