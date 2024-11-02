"""
# List of available output handlers for frundles I/O

- Florian Dupeyron <florian.dupeyron@mugcat.fr>
- September 2024
"""

from .vivado import VivadoOutputHandler
from .tty import TTYOutputHandler

AVAILABLE_HANDLERS = {"tty": TTYOutputHandler, "vivado": VivadoOutputHandler}


def get(name: str):
    return AVAILABLE_HANDLERS.get(name, None)


def default():
    return "tty"
