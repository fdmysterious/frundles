"""
# Frundles errors

- Florian Dupeyron <florian.dupeyron@mugcat.fr>
- August 2024
"""

from .model import LibraryIdentifier


class UnlockedRefSpec:
    def __init__(self, library: LibraryIdentifier):
        super().__init__(self, f"Unlocked library: {library.identifier}")
