"""
# Lock file encoder/decoder

- Florian Dupeyron <florian.dupeyron@mugcat.fr>
- August 2024
"""

import re
from pathlib import Path
from typing import Dict, FrozenSet

from ..errors import LockFileSyntaxError
from ..model import LibraryIdentifier, RefSpec, RefSpecKind

_SHA1_RE = re.compile(r"^[0-9a-fA-F]{40}$")


def from_file(path: Path) -> Dict[LibraryIdentifier, LibraryIdentifier]:
    libs = dict()

    with open(path, "r") as fhandle:
        for lineno, linecontent in enumerate(fhandle, start=1):
            tokens = linecontent.split(":")

            if len(tokens) != 4:
                raise LockFileSyntaxError(
                    lineno, linecontent, "Expected for segments, separated by ':'"
                )

            name = tokens[0].strip()
            refspec_kind_s = tokens[1].strip()
            refspec_kind = None
            refspec_value = tokens[2].strip()
            locked_commit = tokens[3].strip()

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
            unlocked_lib_id = LibraryIdentifier(
                name=name, refspec=refspec, locked_refspec=None
            )

            if unlocked_lib_id in libs:
                raise LockFileSyntaxError(
                    lineno,
                    linecontent,
                    f"Duplicate entry for {unlocked_lib_id.identifier}",
                )

            libs[unlocked_lib_id] = locked_refspec

    return libs


def to_file(path: Path, libs: FrozenSet[LibraryIdentifier]):
    with open(path, "w") as fhandle:
        for lib_id in libs:
            print(
                f"{lib_id.name}:{lib_id.refspec.kind.value}:{lib_id.refspec.value}:{lib_id.locked_refspec.value}",
                file=fhandle,
            )


def add_to_lock_file(path: Path, lib_id: LibraryIdentifier):
    try:
        locked_libs = {k.lock(v) for k, v in from_file(path).items()}

    except FileNotFoundError:
        locked_libs = set()

    locked_libs.add(lib_id)

    to_file(path, locked_libs)
