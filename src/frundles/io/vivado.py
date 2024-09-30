"""
# Output handler format for Vivado integration

- Florian Dupeyron <florian.dupeyron@mugcat.fr>
- September 2024
"""

import logging
from .base import OutputHandler


class VivadoOutputHandler:
    """
    Output handler format for vivado integration
    """

    LOG_LEVELS_NAMES = {
        logging.DEBUG: "DEBUG",
        logging.INFO: "INFO",
        logging.WARNING: "WARNING",
        logging.ERROR: "ERROR",
        logging.CRITICAL: "CRITICAL",
    }

    def __init__(self):
        super().__init__(self)

        self.formatter = None
    

    def configure(self):
        pass


    def _encode_name(self, x: str):
        """
        Auxiliary encoder for log names. Replaces ":" by "-"
        """

        return x.replace(":", "-")


    def _encode_text(self, x: str):
        """
        Escapes \\n to \\r and \\r to \\r\\r, ":" to "::"
        """

        return x.replace(":", "::").replace("\r", "\r\r").replace("\n", "\r")


    def send_output(self, x):
        """
        Output result to console
        """
        print(f"OUTPUT:{self._encdode_text(x)}")


    def send_log(self, record: logging.LogRecord):
        """
        Output format for vivado log messages:

        <SEVERITY>:<NAME>:<MESSAGE>

        Ex: INFO:test_log:This is test message
        """

        lvl  = self.LOG_LEVEL_NAMES[record.level]
        name = self._encode_name(record.name)
        msg  = self._encode_text(record.message)

        print(f"{lvl}:{name}:{msg}")
