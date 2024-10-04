"""
# Default output handler for TTY consoles

- Florian Dupeyron <florian.dupeyron@mugcat.fr>
- September 2024
"""

import coloredlogs
import logging

from .base import OutputHandler


class TTYOutputHandler(OutputHandler):
    """
    Simple output handler for TTY environments.

    - Outputs return values on stdout;
    - Output log messages on stderr using a colored output.
    """

    def __init__(self):
        pass

    def configure(self):
        coloredlogs.install(level=logging.INFO)

    def send_output(self, x: str):
        print(x)

    def send_log(self, record: logging.LogRecord):
        pass
