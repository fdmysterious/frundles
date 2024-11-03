"""
# Bump a library to a specific revision

- Florian Dupeyron <florian.dupeyron@mugcat.fr>
- November 2024

"""

from argparse import ArgumentParser, Namespace
from pathlib import Path

import logging
import traceback
import sys

from ..backend import workspace

from ..io.base import OutputHandler

from ..errors import CannotBumpFixedCommit


log = logging.getLogger("frontend.bump")


def setup_parser(parser: ArgumentParser):
    subparser = parser.add_parser("bump", help="Bump a library revision")
    subparser.add_argument("friendly_name", help="Friendly name of the library")
    subparser.add_argument(
        "--ignore_commits",
        help="Just raise a warning if targetted lib is fixed at a given commit. May avoid some scripts to fail.",
        action="store_true",
    )


def run(output_handler: OutputHandler, args: Namespace):
    cwd = Path.cwd()

    # Find closest workspace
    cur_wspace_path = workspace.find_current_workspace(cwd)

    # Find root workspace
    root_wspace_path = workspace.find_root_workspace(cwd)

    if cur_wspace_path != root_wspace_path:
        log.warning(
            f"Bump command refers to root workspace. Current workspace is at {cur_wspace_path}, whereas root workspace is at {root_wspace_path}"
        )

    # Get the target friendly name
    friendly_name = args.friendly_name

    try:
        workspace.bump_workspace_library(root_wspace_path, friendly_name)

    except CannotBumpFixedCommit as exc:
        if args.ignore_commits:
            log.warning()
        else:
            log.error(str(exc))
            log.debug(traceback.format_exc())
            sys.exit(1)

    except Exception as exc:
        log.critical(exc)
        log.debug(traceback.format_exc())
        sys.exit(1)
