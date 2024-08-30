"""
# List available libraries for the current workspace

- Florian Dupeyron <florian.dupeyron@mugcat.fr>
- August 2024
"""

from tabulate import tabulate
from argparse import ArgumentParser, Namespace
from ..backend import workspace
from pathlib import Path


def setup_parser(parser: ArgumentParser):
    subparser = parser.add_parser(  # noqa: F841
        "list", help="List available libraries in the current workspace"
    )


def run(args: Namespace):
    cwd = Path.cwd()

    # Find the current workspace
    cur_wspace_path = workspace.find_current_workspace(cwd)

    # Load information
    wsinfo, libraries, externals, resolved_refspecs = workspace.load_workspace(
        cur_wspace_path
    )

    # Display information
    headers = ["Reference", "Friendly name"]

    rows = [
        (lib.identifier.identifier, lib.identifier.friendly_name) for lib in libraries
    ]

    print("")
    print("Available libraries:")
    print("")
    print(tabulate(rows, headers=headers, tablefmt="github"))
