"""
# Frundles frontend commands for CLI

- Florian Dupeyron <florian.dupeyron@mugcat.fr>
- August 2024
"""

import logging
import sys

from . import sync
from . import locate
from . import list as cmd_list


CLI_COMMANDS = {
    "sync": sync,
    "locate": locate,
    "list": cmd_list,
}


def main():
    # Imports and initial setup
    import coloredlogs
    import argparse

    coloredlogs.install(level=logging.ERROR)

    # Setup argument parser
    parser = argparse.ArgumentParser(
        prog="frundles",
        description="Frundles is a simple HDL library manager",
        epilog="Hmmmm... I'm Mr.Frundles!",
    )
    subcommand = parser.add_subparsers(dest="subcommand")

    for cmd in CLI_COMMANDS.values():
        cmd.setup_parser(subcommand)

    # Parse the arguments
    args = parser.parse_args()

    if args.subcommand is None:
        parser.print_help(sys.stderr)
        sys.exit(1)
    else:
        cmd = CLI_COMMANDS[args.subcommand]
        cmd.run(args)
