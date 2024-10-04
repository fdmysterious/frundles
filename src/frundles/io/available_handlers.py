"""
# List of available output handlers for frundles I/O

- Florian Dupeyron <florian.dupeyron@mugcat.fr>
- September 2024
"""

from .vivado import VivadoOutputHandler


def get(name: str):
    AVAILABLE_HANDLERS = {"vivado": VivadoOutputHandler}

    return AVAILABLE_HANDLERS.get(name, None)
