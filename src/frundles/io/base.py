"""
# Base classes for I/O handling

- Florian Dupeyron <florian.dupeyron@mugcat.fr>
- September 2024
"""

from abc import ABC, abstractmethod
import logging


class OutputHandler(ABC):
    """
    Base class to create an output handler.

    Output handling in frundles has been designed to handle integration in vendor
    software like Vivado. For instance, in vivado, when an external command outputs
    any text to stderr, the command is considered as failed.

    Output handing addresses two types of records:

    - Log records, following python standard logging record;
    - Output values (that would traditionally go to stdout).

    Please not that the current implementation doesn't contain synchronisation mechanisms.
    It should block to output whole line of text. Underlying buffering mechanisms, etc. are
    relevant to the underlying output stream.
    """

    def __init__(self):
        pass

    def configure(self):
        pass

    @abstractmethod
    def send_output(self, data: str):
        pass

    @abstractmethod
    def send_log(self, record: logging.LogRecord):
        pass


class OutputHandlerLogging(logging.Handler):
    """
    Utility class to connect standard python logging to output handler
    mechanism using logging's handlers.
    """

    def __init__(self, output_handler=None):
        super().__init__()
        self.output_handler = output_handler

    def emit(self, record):
        self.output_handler.send_log(record)
