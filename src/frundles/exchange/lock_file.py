"""
# Lock file encoder/decoder

- Florian Dupeyron <florian.dupeyron@mugcat.fr>
- August 2024
"""

import re
from pathlib import Path

from ..errors import LockFileSyntaxError
from ..model import LibraryIdentifier, RefSpec, RefSpecKind

_SHA1_RE = re.compile(r"^[0-9a-fA-F]{40}$")


def from_file(path: Path):
    libs = set()

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
            lib_id = LibraryIdentifier(
                name=name,
                refspec=refspec,
                locked_refspec=locked_refspec,
            )

            libs.add(lib_id)

    return libs
