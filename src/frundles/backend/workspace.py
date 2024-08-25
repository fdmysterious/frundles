"""
# Frundles workspace related backend features

- Florian Dupeyron <florian.dupeyron@mugcat.fr>
- August 2024

"""

import logging

from pathlib import Path
from ..errors import WorkspaceNotFound

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
