"""
# Frundles workspace related backend features

- Florian Dupeyron <florian.dupeyron@mugcat.fr>
- August 2024

"""

import logging
import traceback

from functools import partial
from typing import Dict, List, FrozenSet
from pathlib import Path
from ..errors import WorkspaceNotFound

from ..exchange import workspace_file, lock_file
from ..model import (
    LibraryIdentifier,
    RefSpec,
    Library,
    LibraryStatus,
    RefSpecKind,
    WorkspaceInfo,
    WorkspaceMode,
)

from . import catalog
from . import library

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

    locked_libs = None
    if lockfile.is_file():
        log.info(f"Found lockfile for workspace {path} at {lockfile}")
        locked_libs = lock_file.from_file(lockfile)

        resolve_func = partial(resolve_locked_lib, locked_libs=locked_libs)

        libraries = [resolve_func(lib) for lib in libraries]

    return wsinfo, libraries, locked_libs


def sync_workspace(path: Path):
    """
    Sync workspace. This means to fetch missing dependencies, and check status of current fetched libraries.
    """

    path = Path(path).resolve()

    # Load workspace information
    root_wspace, libraries, resolved_refspecs = load_workspace(path)
    resolved_refspecs = resolved_refspecs or dict()

    log.info(
        f"Syncing workspace located at {path}, using mode '{root_wspace.mode.value}'"
    )

    # Ensure catalog dir status
    log.debug(f"Ensure catalog dir status for {root_wspace.catalog_dir}")
    catalog.ensure_catalog_dir(root_wspace)

    # Sync libraries
    def fetch_libraries(
        wspace: WorkspaceInfo,
        lockfile_path: Path,
        libraries: List[Library],
        resolved_refspecs: Dict[LibraryIdentifier, RefSpec] = None,
        synced_libraries: FrozenSet[LibraryIdentifier] = frozenset(),
    ):
        resolved_refspecs = dict(
            resolved_refspecs or dict()
        )  # Create a copy to avoid side effect if modified unintentionally

        new_synced_libraries = set()
        new_resolved_refspecs = dict()

        for lib in libraries:
            # If library is already synced, ignore
            if (lib.identifier in synced_libraries) or (
                lib.identifier in new_synced_libraries
            ):
                log.warning(f"Library {lib.identifier} is already synced, ignoring")

            # Sync library
            else:
                log.info(f"Attempt to sync library {lib.identifier.identifier}")

                try:
                    # Ensure library refspec is locked to a specific commit
                    if not lib.identifier.is_locked():
                        if (lib.identifier in resolved_refspecs) or (
                            lib.identifier in new_resolved_refspecs
                        ):
                            # Lock the reference
                            lib = lib.lock(
                                (resolved_refspecs | new_resolved_refspecs)[
                                    lib.identifier
                                ]
                            )

                            # If library is already synced, ignore
                            # FIXME # Duplicated code
                            if (lib.identifier in synced_libraries) or (
                                lib.identifier in new_synced_libraries
                            ):
                                log.warning(
                                    f"Library {lib.identifier} is already synced, ignoring"
                                )
                                continue  # Already fetched, skip to next lib

                        # Commit must be resolved
                        else:
                            log.warning(
                                f"{lib.identifier} is not locked, resolve commit"
                            )
                            oid = library._get_commit_sha1(lib)

                            lib = lib.lock(RefSpec(kind=RefSpecKind.Commit, value=oid))

                            log.info(
                                f"Resolved commit to {oid}, saving to lock file {lockfile_path}"
                            )
                            lock_file.add_to_lock_file(lockfile_path, lib.identifier)

                            new_resolved_refspecs[lib.identifier.unlock()] = (
                                lib.identifier.locked_refspec
                            )

                    # Check status for library
                    lib_status = library.check_status(
                        root_wspace, wspace, lib.identifier
                    )

                    if lib_status == LibraryStatus.NotCloned:
                        library.clone(root_wspace, wspace, lib)
                    elif lib_status == LibraryStatus.Dirty:
                        log.warning(
                            f"{lib.identifier.identifier} has untracked modifications. This could break your project as it's inconsistent."
                        )
                    elif lib_status == LibraryStatus.Modified:
                        log.warning(
                            f"{lib.identifier.identifier} isn't pointing to the target commit, meaning that is it may be modified by hand. This could break your project as it's inconsistent."
                        )

                    # Process library if it's a workspace
                    lib_folder = catalog.get_lib_path(
                        root_wspace, wspace, lib.identifier
                    )
                    if is_workspace(lib_folder):
                        log.info(
                            f"'{lib_folder}' contains frundles data, process it recursively"
                        )

                        lib_wsinfo, lib_ws_libraries, _ = load_workspace(lib_folder)

                        if root_wspace.mode == WorkspaceMode.Recurse:
                            catalog.ensure_catalog_dir(lib_wsinfo)

                        lib_new_synced_libraries, lib_new_resolved_refspecs = (
                            fetch_libraries(
                                lib_wsinfo,
                                lockfile_path=lockfile_path,
                                libraries=lib_ws_libraries,
                                resolved_refspecs=resolved_refspecs
                                | new_resolved_refspecs,
                                synced_libraries=synced_libraries
                                | new_synced_libraries,
                            )
                        )

                        new_resolved_refspecs.update(lib_new_resolved_refspecs)
                        new_synced_libraries.update(lib_new_synced_libraries)

                    # Add to synced libraries
                    new_synced_libraries.add(lib.identifier)

                except Exception as exc:
                    log.error(
                        f"An error occured while retrieving library {lib.identifier}: {str(exc)}"
                    )
                    log.debug(traceback.format_exc())

        return frozenset(new_synced_libraries), new_resolved_refspecs

    synced_libraries, resolved_refspecs = fetch_libraries(
        root_wspace,
        path / "frundles.lock",  # FIXME # Refactor in function
        libraries=libraries,
        resolved_refspecs=resolved_refspecs,
    )
