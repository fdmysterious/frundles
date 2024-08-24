"""
# Frundles model classes

- Florian Dupeyron <florian.dupeyron@mugcat.fr>
- August 2024
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Set
from pathlib import Path

from ..errors import UnlockedRefSpec


###########################################
# Ref spec classes
###########################################


class RefSpecKind(Enum):
    """
    The kind of used ref spec for a git library.
    """

    """Indicated reference is a commit (sha1)"""
    Commit = "commit"

    """Indicated reference is a branch name"""
    Branch = "branch"

    """Indicated reference is a tag"""
    Tag = "tag"


@dataclass(frozen=True)
class RefSpec:
    """
    An indication of a target git library revision
    """

    """The kind of ref spec"""
    kind: RefSpecKind

    """The value of the reference"""

    value: str

    def __hash__(self):
        return hash(f"{self.kind.value}:{self.value}")


###########################################
# Library related classes
###########################################


@dataclass(frozen=True)
class LibraryIdentifier:
    """
    Library identification information
    """

    """The name of the library"""
    name: str

    """The target revision"""
    refspec: RefSpec

    """The locked revision"""
    locked_refspec: Optional[RefSpec] = None

    @property
    def identifier(self):
        return f"{self.name}:{self.refspec.value}"

    @property
    def locked_identifier(self):
        """Returns an identifier string that shall be unique to a given library"""

        if self.locked_refspec is None:
            raise UnlockedRefSpec(self.refspec)

        return f"{self.name}:{self.locked_refspec.value}"

    def __hash__(self):
        if self.locked_identifier:
            return hash(self.locked_identifier)
        else:
            return hash(self.identifier)


@dataclass
class Library:
    """Contains detailled information about a specific library"""

    """Unique identification information for the library"""
    identifier: LibraryIdentifier

    """Git origin URL"""
    origin: str

    """Set of dependencies"""
    dependencies: Set[LibraryIdentifier] = field(default_factory=set)

    def __hash__(self):
        return self.identifier.__hash__()


###########################################
# Workspace related information
###########################################


@dataclass
class WorkspaceInfo:
    catalog_dir: Path
