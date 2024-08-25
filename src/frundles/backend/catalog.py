"""
# Frundles catalog management

- Florian Dupeyron <florian.dupeyron@mugcat.fr>
- August 2024
"""

import os
import logging

from pathlib import Path

from ..model import WorkspaceInfo, LibraryIdentifier
from ..errors import CatalogNotADirError, CatalogWriteAccessError


log = logging.getLogger("backend.catalog")


###########################################
# Catalog directory management
###########################################


def get_lib_path(catalog_dir: Path, lib_id: LibraryIdentifier):
    return catalog_dir / lib_id.locked_identifier_path


def ensure_catalog_dir(wspace: WorkspaceInfo):
    catalog_dir = Path(wspace.catalog_dir).resolve()
    log.info(f"Check for {catalog_dir} as a catalog folder")

    # Ensure folder exists and is a regular folder
    if not catalog_dir.exists():
        log.warning(f"{catalog_dir} doesn't exist yet, creating the folder")

        # NOTE # Can raise NotADirectoryError if path has several components,
        # for instance subdir/ip, and that "subdir" exists as a file.
        catalog_dir.mkdir(parents=True)

    elif not catalog_dir.is_dir():
        raise CatalogNotADirError(catalog_dir)

    # Check write access to folder
    if not os.access(str(catalog_dir), os.W_OK):
        raise CatalogWriteAccessError(catalog_dir)
