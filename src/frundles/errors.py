"""
# Frundles errors

- Florian Dupeyron <florian.dupeyron@mugcat.fr>
- August 2024
"""

from typing import Dict


class UnlockedRefSpec(Exception):
    def __init__(self, library):
        super().__init__(f"Unlocked library: {library.identifier}")


class MultipleRefSpec(Exception):
    def __init__(self, libname: str, defs: Dict[str, str]):
        deflist = map(
            lambda x: f"{x[0]}={x[1]}", filter(lambda x: x[1] is not None, defs.items())
        )

        super().__init__(
            f"Multiple refspecs for library {libname}: {', '.join(deflist)}"
        )
