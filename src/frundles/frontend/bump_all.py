"""
# Bump all libraries revision

- Florian Dupeyron <florian.dupeyron@mugcat.fr>
- November 2024

"""

from argparse import ArgumentParser, Namespace
from pathlib import Path

import logging

from ..backend import workspace
from ..io.base import OutputHandler

log = logging.getLogger("frontend.bump_all")


def setup_parser(parser: ArgumentParser):
    parser.add_parser("bump-all", help="Bump all libraries")


def run(output_handler: OutputHandler, args: Namespace):
    cwd = Path.cwd()

    # Find root workspace
    root_ws_path = workspace.find_root_workspace(cwd)
    log.info("Bump all dependencies for workspace located in {root_ws_path}")

    # Bumping all libraries is a synchronization ignoring the root lock file
    workspace.sync_workspace(root_ws_path, ignore_root_lockfile=True)
