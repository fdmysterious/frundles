"""
# Frundles workspace related backend features

- Florian Dupeyron <florian.dupeyron@mugcat.fr>
- August 2024

"""

import logging

from functools import partial
from typing import Dict
from pathlib import Path
from ..errors import WorkspaceNotFound

from ..exchange import workspace_file, lock_file
from ..model import LibraryIdentifier, RefSpec, Library

log = logging.getLogger("backend.workspace")


###########################################
# Find frundles.yml file
###########################################


def _iter_path(pp: Path):
    cur_path = pp

    while True:
        yield cur_path

        if cur_path.parent != cur_path:
            cur_path = cur_path.parent
        else:
            break


def find_workspace(start_path: Path, recursive: bool = False):
    log.info(f"Search workspace file starting from {start_path}")

    def check_frundles(path: Path):
        return (path / "frundles.yml").is_file()

    # Search for file in folder
    if check_frundles(start_path):
        return start_path

    # Search in parents
    elif recursive:
        for subpath in _iter_path(start_path.parent):
            log.debug(f"Check parent directory: {subpath}")

            if check_frundles(subpath):
                return subpath

        else:
            raise WorkspaceNotFound(start_path=start_path, recursive=recursive)

    else:
        raise WorkspaceNotFound(start_path=start_path, recursive=recursive)


def is_workspace(path: Path):
    return (path / "frundles.yml").is_file()


def load_workspace(path: Path):
    """
    Load workspace information.
    """

    path = Path(path).resolve()

    log.info(f"Load workspace information from {path}")

    ws_file = (path / "frundles.yml").resolve()
    lockfile = (path / "frundles.lock").resolve()

    # Load workspace information from config file
    wsinfo, libraries = workspace_file.from_file(ws_file)

    # Load locked references from lock file, if it exists
    def resolve_locked_lib(lib: Library, locked_libs: Dict[LibraryIdentifier, RefSpec]):
        if lib.identifier in locked_libs:
            lib = lib.lock(locked_libs[lib.identifier])

        return lib

    if lockfile.is_file():
        locked_libs = lock_file.from_file(lockfile)

        resolve_func = partial(resolve_locked_lib, locked_libs=locked_libs)

        libraries = [resolve_func(lib) for lib in libraries]

    return wsinfo, libraries
