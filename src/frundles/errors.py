"""
# Frundles errors

- Florian Dupeyron <florian.dupeyron@mugcat.fr>
- August 2024
"""

from pathlib import Path
from typing import Dict


class UnlockedRefSpec(Exception):
    def __init__(self, library):
        # NOTE # Precising library type as "ItemIdentifier" (using the quotes for deferred reference)
        # breaks ruff type checking stuff. See https://github.com/astral-sh/ruff/issues/7175.

        super().__init__(f"Unlocked library: {library.identifier}")


class MultipleRefSpec(Exception):
    def __init__(self, libname: str, defs: Dict[str, str]):
        deflist = map(
            lambda x: f"{x[0]}={x[1]}", filter(lambda x: x[1] is not None, defs.items())
        )

        super().__init__(
            f"Multiple refspecs for library {libname}: {', '.join(deflist)}"
        )


class WorkspaceNotFound(Exception):
    def __init__(self, start_path: Path, recursive: bool = False):
        super().__init__(
            f"No workspace found starting from {start_path}. Recursive search was {'on' if recursive else 'off'}"
        )


class CatalogNotADirError(Exception):
    def __init__(self, catalog_dir: Path):
        super().__init__(f"{catalog_dir} exists, but is not a directory")


class CatalogWriteAccessError(Exception):
    def __init__(self, catalog_dir: Path):
        super().__init__(f"{catalog_dir} is not writeable for the current user")


class LockFileSyntaxError(Exception):
    def __init__(self, lineno, linecontent: str, error_explanation: str):
        super().__init__(
            f"Invalid lockfile syntax on line {lineno} for line '{linecontent}': {error_explanation}"
        )


class DuplicateFriendlyName(Exception):
    def __init__(self, friendly_name: str):
        super().__init__(f"Duplicate friendly name found: {friendly_name}")


class DuplicateLockfileIdentifier(Exception):
    def __init__(self, identifier):
        super().__init__(
            f"Item identifier {identifier.identifier} already present in lock file"
        )


class InvalidOrigin(Exception):
    def __init__(self, target_origin, got_origin):
        super().__init__(
            f"Unexpected origin URL. Expected {target_origin}, got {got_origin}"
        )
