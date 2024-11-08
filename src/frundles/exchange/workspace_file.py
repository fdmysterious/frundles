"""
# Simple parser for yaml workspace file

- Florian Dupeyron
- August 2024
"""

import re
import yaml

import urllib.parse
from pathlib import Path

from typing import Dict, List

from ..model import (
    ArtifactKind,
    WorkspaceInfo,
    WorkspaceMode,
    ItemIdentifier,
    Library,
    RefSpec,
    RefSpecKind,
    External,
)
from ..errors import MultipleRefSpec, DuplicateFriendlyName


###########################################
# Load workspace functions
###########################################


def _extract_name_from_repo_url(x: str):
    url_scheme, url_netloc, url_path, url_query, url_fragment = urllib.parse.urlsplit(x)
    last_path_token = Path(url_path).parts[-1]
    name = re.sub("[.]git$", "", last_path_token)  # Remove trailing .git if needed

    return name


def _parse_refspec(name: str, data: Dict[str, any]) -> RefSpec:
    # Parse refspec ; check that only one ref specification is defined, and build the corresponding refspec
    branch = data.get("branch", None)
    tag = data.get("tag", None)
    commit = data.get("commit", None)

    refspec = None
    locked_refspec = None

    # -- branch is specified
    if (branch is not None) and (tag is None) and (commit is None):
        refspec = RefSpec(kind=RefSpecKind.Branch, value=branch)
        locked_refspec = None

    # -- tag is specified
    elif (branch is None) and (tag is not None) and (commit is None):
        refspec = RefSpec(kind=RefSpecKind.Tag, value=tag)
        locked_refspec = None

    # -- commit is specified -> lock the refspec
    elif (branch is None) and (tag is None) and (commit is not None):
        refspec = RefSpec(kind=RefSpecKind.Commit, value=commit)
        locked_refspec = refspec

    else:
        raise MultipleRefSpec(
            name, defs={"branch": branch, "tag": tag, "commit": commit}
        )

    return refspec, locked_refspec


def parse_workspace_info(cwd: Path, data: Dict[str, any]) -> WorkspaceInfo:
    catalog_dir = Path(data["catalog_dir"])
    workspace_mode = data.get("mode", None)

    # Try to parse workspace mode if given
    if workspace_mode is not None:
        workspace_mode = WorkspaceMode(workspace_mode)

    # Resolve catalog dir relative to current config file path if needed
    if not catalog_dir.is_absolute():
        catalog_dir = cwd / catalog_dir

    return WorkspaceInfo(catalog_dir=catalog_dir, mode=workspace_mode)


def parse_library_definition(cwd: Path, data: Dict[str, any]) -> Library:
    origin = data["origin"]

    # Parse the url and extract the library name
    name = _extract_name_from_repo_url(origin)

    # Parse refspecs
    refspec, locked_refspec = _parse_refspec(name, data)

    # Extract friendly name if any, or deduce from repo name and refspec tag
    friendly_name = data.get("friendly_name", f"{name}:{refspec.value}")

    # Build the corresponding library identifier
    lib_id = ItemIdentifier(
        kind=ArtifactKind.Library,
        name=name,
        friendly_name=None,
        refspec=refspec,
        locked_refspec=locked_refspec,
    )

    # Extract friendly name if any
    friendly_name = data.get("friendly_name", None) or lib_id.identifier

    lib_id = lib_id.add_friendly_name(friendly_name)

    # Build the final Library object
    lib = Library(identifier=lib_id, origin=origin)

    return lib


def parse_external_definition(cwd, data: Dict[str, any]) -> External:
    origin = data["origin"]
    dest_path = data["dest_path"]

    # Parse the URL and extract the external name
    name = _extract_name_from_repo_url(origin)

    # Parse refspecs
    refspec, locked_refspec = _parse_refspec(name, data)

    # Parse destination folder
    dest_path = Path(dest_path)

    # Build the corresponding external identifier
    ext_id = ItemIdentifier(
        kind=ArtifactKind.External,
        name=name,
        refspec=refspec,
        locked_refspec=locked_refspec,
    )

    # Build the External object
    ext = External(identifier=ext_id, origin=origin, dest_path=dest_path)

    return ext


def from_file(path: Path):
    """Parses an input yaml file.

    Returns the workspace information, associated with the set of found libraries definitions
    """

    path = Path(path)  # ensure path var is of Path type
    cwd = path.parent.resolve()

    data = None
    with open(path, "r") as fhandle:
        data = yaml.safe_load(fhandle)

    # TODO # File schema validation

    # Parse workspace info
    workspace_info = parse_workspace_info(cwd, data["workspace"])

    # Parse libraries definitions
    libraries = [
        parse_library_definition(cwd, lib) for lib in data.get("libraries", [])
    ]

    # Parse externals
    externals = [
        parse_external_definition(cwd, ext) for ext in data.get("externals", [])
    ]

    # Search for duplicate friendly names
    friendly_names = set()
    for lib in libraries:
        friendly_name = lib.identifier.friendly_name
        if friendly_name in friendly_names:
            raise DuplicateFriendlyName(friendly_name)
        else:
            friendly_names.add(friendly_name)

    return workspace_info, libraries, externals


###########################################
# Save workspace functions
###########################################


def encode_workspace_info(wsdir: Path, wsinfo: WorkspaceInfo):
    """Encode workspace info in a dictionary for YAML encoding.

    Args:
        wsdir: Path to current workspace
        wsinfo: Workspace information to encode

    Returns:
        A dictionary containing encoded workspace information
    """

    s_catalog_dir = str(
        wsinfo.catalog_dir.relative_to(wsdir)
        if wsinfo.catalog_dir.is_relative_to(wsdir)
        else wsinfo.catalog_dir
    )
    s_mode = str(wsinfo.mode)

    return {
        "catalog_dir": s_catalog_dir,
        "mode": s_mode,
    }


def _encode_refspec(refspec: RefSpec):
    key = str(refspec.kind)
    value = str(refspec.value)

    return {key: value}


def encode_library_definition(lib: Library):
    s_origin = str(lib.origin)
    d_refspec = _encode_refspec(lib.identifier.refspec)
    s_friendly_name = str(lib.identifier.friendly_name)

    # Create a temp dict that contains the friendly name only if different from automatically generated one when loading
    d_friendly_name = (
        {"friendly_name": s_friendly_name}
        if s_friendly_name != f"{lib.identifier.name}:{lib.identifier.refspec.value}"
        else dict()
    )

    return {"origin": s_origin, **d_friendly_name, **d_refspec}


def encode_external_definition(wsdir: Path, ext: External):
    s_origin = ext.origin
    s_dest_path = str(
        ext.dest_path.relative_to(wsdir)
        if ext.dest_path.is_relative_to(wsdir)
        else ext.dest_path
    )
    d_refspec = _encode_refspec(ext.identifier.refspec)
    s_friendly_name = str(ext.identifier.friendly_name)

    # Create a temp dict that contains the friendly name only if different from automatically generated one when loading
    d_friendly_name = (
        {"friendly_name": s_friendly_name}
        if s_friendly_name != f"{ext.identifier.name}:{ext.identifier.refspec.value}"
        else dict()
    )

    return {
        "origin": s_origin,
        "dest_path": s_dest_path,
        **d_friendly_name,
        **d_refspec,
    }


def to_file(
    path: Path,
    workspace_info: WorkspaceInfo,
    libraries: List[Library],
    externals: List[External],
):
    """Save workspace properties to a target file

    Args:
        path: Target file path
        workspace_info: Workspace info properties
        libraries: List of libraries for workspace
        externals: List of externals for workspace
    """

    path = Path(path)  # ensure path is of Path type

    # Encode workspace info
    d_wsinfo = encode_workspace_info(path, workspace_info)

    # Encode list of libraries and externals
    l_libs = [encode_library_definition(lib) for lib in libraries]
    l_exts = [encode_external_definition(ext) for ext in externals]

    # Generate final output dictionary
    d_output_libs = {"libraries": l_libs} if l_libs else dict()
    d_output_exts = {"externals": l_exts} if l_exts else dict()

    d_output = {
        "workspace": d_wsinfo,
        **d_output_libs,
        **d_output_exts,
    }

    # Save to yaml file
    with open(path, "w") as fhandle:
        yaml.dump(d_output, fhandle)
