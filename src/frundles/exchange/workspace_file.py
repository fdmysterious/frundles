"""
# Simple parser for yaml workspace file

- Florian Dupeyron
- August 2024
"""

import re
import yaml
from furl import furl

from pathlib import Path
from typing import Dict

from ..model import (
    WorkspaceInfo,
    WorkspaceMode,
    LibraryIdentifier,
    Library,
    RefSpec,
    RefSpecKind,
)
from ..errors import MultipleRefSpec


def parse_workspace_info(file_path: Path, data: Dict[str, any]) -> WorkspaceInfo:
    config_file_path = file_path.resolve().parent
    catalog_dir = Path(data["catalog_dir"])
    workspace_mode = data.get("mode", None)

    # Try to parse workspace mode if given
    if workspace_mode is not None:
        workspace_mode = WorkspaceMode(workspace_mode)

    # Resolve catalog dir relative to current config file path if needed
    if not catalog_dir.is_absolute():
        catalog_dir = config_file_path / catalog_dir

    return WorkspaceInfo(catalog_dir=catalog_dir, mode=workspace_mode)


def parse_library_definition(data: Dict[str, any]) -> Library:
    origin = data["origin"]

    # Parse the url and extract the library name
    origin = data["origin"]
    last_path_token = None

    if origin.startswith("ssh://"):
        last_path_token = origin.split(":")[2].split("/")[-1]
    else:
        origin_url = furl(origin)
        last_path_token = origin_url.path.segments[-1]

    name = re.sub("[.]git$", "", last_path_token)  # Remove trailing .git if needed

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

    # Build the corresponding library identifier
    lib_id = LibraryIdentifier(
        name=name, refspec=refspec, locked_refspec=locked_refspec
    )

    # Build the final Library object
    lib = Library(identifier=lib_id, origin=origin)

    return lib


def from_file(path: Path):
    """Parses an input yaml file.

    Returns the workspace information, associated with the set of found libraries definitions
    """

    path = Path(path)  # ensure path var is of Path type

    data = None
    with open(path, "r") as fhandle:
        data = yaml.safe_load(fhandle)

    # TODO # File schema validation

    # Parse workspace info
    workspace_info = parse_workspace_info(path, data["workspace"])

    # Parse libraries definitions
    libraries = [parse_library_definition(lib) for lib in data["libraries"]]

    return workspace_info, libraries
