"""
# Frundles workspace related backend features

- Florian Dupeyron <florian.dupeyron@mugcat.fr>
- August 2024

"""

import logging
import traceback

from functools import partial
from typing import Dict, List, FrozenSet, Tuple
from pathlib import Path
from ..errors import WorkspaceNotFound

from ..exchange import workspace_file, lock_file
from ..model import (
    ItemIdentifier,
    RefSpec,
    Library,
    FetchStatus,
    RefSpecKind,
    WorkspaceInfo,
    WorkspaceMode,
)

from . import catalog
from . import artifact

log = logging.getLogger("backend.workspace")


###########################################
# Find frundles.yml file
###########################################


def is_workspace(path: Path):
    return (path / "frundles.yml").is_file()


def _iter_path(pp: Path):
    cur_path = pp

    while True:
        yield cur_path

        if cur_path.parent != cur_path:
            cur_path = cur_path.parent
        else:
            break


def find_current_workspace(start_path: Path):
    log.info(f"Search workspace file starting from {start_path}")

    # Search for file in folder
    if is_workspace(start_path):
        return start_path

    # Search in parents
    else:
        for subpath in _iter_path(start_path.parent):
            log.debug(f"Check parent directory: {subpath}")

            if is_workspace(subpath):
                return subpath
        else:
            raise WorkspaceNotFound(start_path=start_path, recursive=True)


def find_root_workspace(start_path: Path):

    cur_path = start_path

    for subpath in _iter_path(start_path.parent):
        if is_workspace(subpath):
            cur_path = subpath

    if not is_workspace(cur_path):
        raise WorkspaceNotFound(start_path=start_path, recursive=True)

    return cur_path


def load_workspace(path: Path, ignore_lockfile=False):
    """Load workspace information.

    Args:
        path: path of workspace information to load
        ignore_lockfile: ignore lockfile information if True
    """

    path = Path(path).resolve()
    workspace_git_origin = artifact.get_origin(path)
    ws_is_local_origin = artifact.has_local_origin(workspace_git_origin or "")

    log.info(f"Load workspace information from {path}")

    ws_file = (path / "frundles.yml").resolve()
    lockfile = (path / "frundles.lock").resolve()

    # Load workspace information from config file
    wsinfo, libraries, externals = workspace_file.from_file(ws_file)

    # Resolve local dependencies, if needed
    def resolve_local_lib_dependency(path: Path, lib: Library):
        if artifact.has_local_origin(lib.origin):
            if not ws_is_local_origin:
                log.warning(
                    f"Depedency to {lib.origin} for workspace located in {path} points to a local directory, but this workspace has a non-local remote URL. This may lead to some weird stuff. Assuming a path relative to the local directory"
                )
                lib = lib.change_origin((path / lib.origin).resolve())
            else:
                if workspace_git_origin:
                    lib = lib.change_origin(
                        (Path(workspace_git_origin) / lib.origin).resolve()
                    )
                else:
                    log.warning(
                        f"Assuming {path} start path to resolve dependency to local repository {lib.origin}"
                    )
                    lib = lib.change_origin((path / lib.origin).resolve())
        return lib

    libraries = [resolve_local_lib_dependency(path, lib) for lib in libraries]

    # Load locked references from lock file, if it exists
    def resolve_locked_lib(lib: Library, locked_libs: Dict[ItemIdentifier, RefSpec]):
        if lib.identifier in locked_libs:
            lib = lib.lock(locked_libs[lib.identifier])

        return lib

    locked_libs = None
    if lockfile.is_file() and not ignore_lockfile:
        log.info(f"Found lockfile for workspace {path} at {lockfile}")
        locked_libs = lock_file.from_file(lockfile)

        resolve_func = partial(resolve_locked_lib, locked_libs=locked_libs)

        libraries = [resolve_func(lib) for lib in libraries]
        externals = [resolve_func(ext) for ext in externals]

    return wsinfo, libraries, externals, locked_libs


def _fetch_artifacts(
    root_wspace: WorkspaceInfo,
    wspace: WorkspaceInfo,
    fetch_mode: WorkspaceMode,
    lockfile_path: Path,
    libraries: List[Library],
    resolved_refspecs: Dict[ItemIdentifier, RefSpec] = None,
    synced_libraries: FrozenSet[ItemIdentifier] = frozenset(),
    fetch_stack: Tuple[ItemIdentifier] = tuple(),
    allow_lockfile_replace: bool = False,
):
    resolved_refspecs = dict(
        resolved_refspecs or dict()
    )  # Create a copy to avoid side effect if modified unintentionally

    new_synced_libraries = set()
    new_resolved_refspecs = dict()

    for lib in libraries:
        # If a circular dependency is detected, error
        if lib.identifier in set(fetch_stack):
            fetch_order = (
                " -> ".join(map(lambda x: x.identifier, fetch_stack))
                + f" -> {lib.identifier.identifier}"
            )
            log.error(
                f"CIRCULAR DEPENDECY DETECTED: {fetch_order}. Not processing this dependency!"
            )

        # If library is already synced and in aggregate mode, ignore
        elif (fetch_mode == WorkspaceMode.Aggregate) and (
            (lib.identifier in synced_libraries)
            or (lib.identifier in new_synced_libraries)
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
                            (resolved_refspecs | new_resolved_refspecs)[lib.identifier]
                        )

                        # Avoid circular dependencies
                        # FIXME # Duplicated code
                        if lib.identifier in set(fetch_stack):
                            fetch_order = (
                                " -> ".join(
                                    map(lambda x: x.locked_identifier, fetch_stack)
                                )
                                + f" -> {lib.identifier.locked_identifier}"
                            )
                            log.error(
                                f"CIRCULAR DEPENDECY DETECTED: {fetch_order}. Not processing this dependency!"
                            )
                            continue  # Skip this one

                        # If library (with now locked reference) is already synced, ignore
                        # FIXME # Duplicated code
                        elif (fetch_mode == WorkspaceMode.Aggregate) and (
                            (lib.identifier in synced_libraries)
                            or (lib.identifier in new_synced_libraries)
                        ):
                            log.warning(
                                f"Library {lib.identifier} is already synced, ignoring"
                            )
                            continue  # Already fetched, skip to next lib

                    # Commit must be resolved
                    else:
                        log.warning(
                            f"{lib.identifier.identifier} is not locked, resolve commit"
                        )
                        oid = artifact._get_commit_sha1(lib)

                        lib = lib.lock(RefSpec(kind=RefSpecKind.Commit, value=oid))

                        log.info(
                            f"Resolved commit to {oid}, saving to lock file {lockfile_path}"
                        )
                        lock_file.add_to_lock_file(
                            lockfile_path,
                            lib.identifier,
                            replace_existing=allow_lockfile_replace,
                        )

                        new_resolved_refspecs[lib.identifier.unlock()] = (
                            lib.identifier.locked_refspec
                        )

                # Check status for library
                lib_status = artifact.check_status(root_wspace, wspace, lib.identifier)

                if lib_status == FetchStatus.NotCloned:
                    target_dir = catalog.get_lib_path(
                        root_wspace, wspace, lib.identifier
                    )
                    log.info(
                        f"Clone {lib.identifier.identifier} library to {target_dir}"
                    )
                    artifact.clone(
                        target_dir, lib.origin, lib.identifier.locked_refspec
                    )

                elif lib_status == FetchStatus.Dirty:
                    log.warning(
                        f"{lib.identifier.identifier} has untracked modifications. This could break your project as it's inconsistent."
                    )
                elif lib_status == FetchStatus.Modified:
                    log.warning(
                        f"{lib.identifier.identifier} isn't pointing to the target commit, meaning that is it may be modified by hand. This could break your project as it's inconsistent."
                    )

                # Process library if it's a workspace
                lib_folder = catalog.get_lib_path(root_wspace, wspace, lib.identifier)
                if is_workspace(lib_folder):
                    log.info(
                        f"'{lib_folder}' contains frundles data, process it recursively"
                    )

                    lib_wsinfo, lib_ws_libraries, lib_ws_externals, _ = load_workspace(
                        lib_folder
                    )

                    if root_wspace.mode == WorkspaceMode.Recurse:
                        catalog.ensure_catalog_dir(lib_wsinfo)

                    lib_new_synced_libraries, lib_new_resolved_refspecs = (
                        _fetch_artifacts(
                            root_wspace,
                            lib_wsinfo,
                            fetch_mode=fetch_mode,
                            lockfile_path=lockfile_path,
                            libraries=lib_ws_libraries,
                            resolved_refspecs=resolved_refspecs | new_resolved_refspecs,
                            synced_libraries=synced_libraries | new_synced_libraries,
                            fetch_stack=fetch_stack + (lib.identifier,),
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


def sync_workspace(path: Path, ignore_root_lockfile=False):
    """Sync workspace. This means to fetch missing dependencies, and check status of current fetched libraries.

    Args:
        path: Path of workspace to synchronize
        ignore_root_lockfile: Ignore the workspace's lockfile. This means bumping all branch and potentially tag references.
    """

    path = Path(path).resolve()

    # Load workspace information
    root_wspace, libraries, externals, resolved_refspecs = load_workspace(
        path, ignore_lockfile=ignore_root_lockfile
    )
    resolved_refspecs = resolved_refspecs or dict()

    log.info(
        f"Syncing workspace located at {path}, using mode '{root_wspace.mode.value}'"
    )

    # Ensure catalog dir status
    log.debug(f"Ensure catalog dir status for {root_wspace.catalog_dir}")
    catalog.ensure_catalog_dir(root_wspace)

    # Sync libraries
    synced_libraries, resolved_refspecs = _fetch_artifacts(
        root_wspace=root_wspace,
        wspace=root_wspace,
        fetch_mode=root_wspace.mode,
        lockfile_path=path / "frundles.lock",  # FIXME # Refactor in function
        libraries=libraries,
        resolved_refspecs=resolved_refspecs,
        allow_lockfile_replace=ignore_root_lockfile,
    )


def locate(path: Path, friendly_name: str):

    root_wspace_path = find_root_workspace(path)

    root_wspace, _, _, _ = load_workspace(root_wspace_path)

    # TODO# Maybe some optimization if root_wspace_path == path?
    cur_wspace, libraries, externals, _ = load_workspace(path)

    try:
        lib = next(
            filter(lambda x: x.identifier.friendly_name == friendly_name, libraries)
        )
        lib_path = catalog.get_lib_path(root_wspace, cur_wspace, lib.identifier)

        return lib_path

    except StopIteration:
        return None  # This library doesn't exist in the workspace
