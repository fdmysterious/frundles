"""
# Lock file encoder/decoder

- Florian Dupeyron <florian.dupeyron@mugcat.fr>
- August 2024
"""

import re
from pathlib import Path
from typing import Dict, FrozenSet

from ..errors import LockFileSyntaxError, DuplicateLockfileIdentifier, UnlockedRefSpec
from ..model import ItemIdentifier, RefSpec, RefSpecKind, ArtifactKind

_SHA1_RE = re.compile(r"^[0-9a-fA-F]{40}$")


def from_file(path: Path) -> Dict[ItemIdentifier, RefSpec]:
    """Parses a lock file

    Args:
        path: Path to lockfile

    Returns:
        A dictionary matching the input item identifier (potentially unlocked) to its corresponding locked refspec
    """

    libs = dict()

    with open(path, "r") as fhandle:
        for lineno, linecontent in enumerate(fhandle, start=1):
            tokens = linecontent.split(":")

            if len(tokens) != 5:
                raise LockFileSyntaxError(
                    lineno, linecontent, "Expected for segments, separated by ':'"
                )

            artifact_kind_s = tokens[0].strip()
            artifact_kind = None
            name = tokens[1].strip()
            refspec_kind_s = tokens[2].strip()
            refspec_kind = None
            refspec_value = tokens[3].strip()
            locked_commit = tokens[4].strip()

            # Parse artifact kind
            try:
                artifact_kind = ArtifactKind(artifact_kind_s)
            except ValueError:
                raise LockFileSyntaxError(
                    lineno, linecontent, f"Invalid artifact kind: '{artifact_kind_s}'"
                )

            # Parse refspec
            try:
                refspec_kind = RefSpecKind(refspec_kind_s)
            except ValueError:
                raise LockFileSyntaxError(
                    lineno, linecontent, f"Invalid refspec kind: '{refspec_kind_s}'"
                )

            if (refspec_kind == RefSpecKind.Commit) and not (
                _SHA1_RE.match(refspec_value)
            ):
                raise LockFileSyntaxError(
                    lineno,
                    linecontent,
                    f"{refspec_value} for refspec doesn't appear to be a valid SHA1",
                )

            refspec = RefSpec(kind=refspec_kind, value=refspec_value)

            # Parse locked refspec kind
            if not _SHA1_RE.match(locked_commit):
                raise LockFileSyntaxError(
                    lineno,
                    linecontent,
                    f"{locked_commit} doesn't appear to be a valid SHA1",
                )

            locked_refspec = RefSpec(kind=RefSpecKind.Commit, value=locked_commit)

            # Create library identifier
            unlocked_lib_id = ItemIdentifier(
                kind=artifact_kind, name=name, refspec=refspec, locked_refspec=None
            )

            if unlocked_lib_id in libs:
                raise LockFileSyntaxError(
                    lineno,
                    linecontent,
                    f"Duplicate entry for {unlocked_lib_id.identifier}",
                )

            libs[unlocked_lib_id] = locked_refspec

    return libs


def to_file(path: Path, libs: FrozenSet[ItemIdentifier]):
    with open(path, "w") as fhandle:
        for lib_id in libs:
            print(
                f"{lib_id.kind.value}:{lib_id.name}:{lib_id.refspec.kind.value}:{lib_id.refspec.value}:{lib_id.locked_refspec.value}",
                file=fhandle,
            )


def add_to_lock_file(
    path: Path, lib_id: ItemIdentifier, replace_existing: bool = False
):
    """Add a locked reference to lock file

    Args:
        path: Path to lock file
        lib_id: Identifier of target library
        replace_existing: Replace exisitng locked reference if it exists in file. Raise an error otherwise.
    """

    # Check if target lib_id is correctly locked
    if not lib_id.is_locked():
        raise UnlockedRefSpec(lib_id)

    # Load existing lock file information if it exists
    try:
        libs = from_file(path)
    except FileNotFoundError:
        # Default: Prepare an empty file
        libs = dict()

    # Check if identifier already exist in file?
    unlocked_id = lib_id.unlock()

    if unlocked_id in libs:
        if replace_existing:
            # Replace identifier with its new version
            libs[unlocked_id] = lib_id.locked_refspec
        else:
            # Identifier already exist in file and no replacement allowed
            raise DuplicateLockfileIdentifier(unlocked_id)

    # Lock references
    locked_libs = {k.lock(v) for k, v in libs.items()}

    # Save to file
    to_file(path, locked_libs)
