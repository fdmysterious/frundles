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


from frundles.io.available_handlers import AVAILABLE_HANDLERS, default as default_handler
from frundles.io.base import OutputHandlerLogging
from frundles.io.tty import TTYOutputHandler


CLI_COMMANDS = {
    "sync": sync,
    "locate": locate,
    "list": cmd_list,
}


def main():
    # Imports and initial setup
    import argparse

    # Setup argument parser
    parser = argparse.ArgumentParser(
        prog="frundles",
        description="Frundles is a simple HDL library manager",
        epilog="Hmmmm... I'm Mr.Frundles!",
    )

    # Add argument for output handler
    parser.add_argument("--output_mode", choices=AVAILABLE_HANDLERS.keys(), default=default_handler(), help="Set output mode for integration with other tools")

    subcommand = parser.add_subparsers(dest="subcommand")

    for cmd in CLI_COMMANDS.values():
        cmd.setup_parser(subcommand)

    # Parse the arguments
    args = parser.parse_args()

    if args.subcommand is None:
        parser.print_help(sys.stderr)
        sys.exit(1)
    else:
        # Setup output handler
        output_handler = AVAILABLE_HANDLERS[args.output_mode]()
        output_handler.configure()

        log_handler = OutputHandlerLogging(output_handler)

        logging.getLogger().addHandler(log_handler)
        logging.getLogger("frundles").info("Hello world!")

        cmd = CLI_COMMANDS[args.subcommand]
        cmd.run(output_handler, args)
