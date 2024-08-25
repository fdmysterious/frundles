"""
# Frundles model classes

- Florian Dupeyron <florian.dupeyron@mugcat.fr>
- August 2024
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional
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


class LibraryStatus(Enum):
    """Indicates the current status of the library"""

    """Library hasn't been cloned yet"""
    NotCloned = "not_cloned"

    """Everything is fine : library is fetched at correct revision"""
    Ok = "ok"

    """Library is fetched at correct revision, but uncomitted modifications are present in files"""
    Dirty = "dirty"

    """Library is not at the target revision"""
    Modified = "modified"

    """Library folder is broken"""
    Invalid = "invalid"


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

    @property
    def locked_identifier_path(self):
        """Returns an identifier that shall be unique to a given library, to be used with folder names"""

        if self.locked_refspec is None:
            raise UnlockedRefSpec(self.refspec)

        return f"{self.name}-{self.locked_refspec.value}"

    def lock(self, locked_refspec: RefSpec):
        return LibraryIdentifier(
            name=self.name, refspec=self.refspec, locked_refspec=locked_refspec
        )

    def unlock(self):
        return LibraryIdentifier(
            name=self.name, refspec=self.refspec, locked_refspec=None
        )

    def is_locked(self):
        return self.locked_refspec is not None

    def __hash__(self):
        if self.locked_refspec:
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

    # """Set of dependencies"""
    # dependencies: Set[LibraryIdentifier] = field(default_factory=set)

    def lock(self, refspec: RefSpec):
        return Library(identifier=self.identifier.lock(refspec), origin=self.origin)

    def __hash__(self):
        return self.identifier.__hash__()


###########################################
# Workspace related information
###########################################


@dataclass
class WorkspaceInfo:
    catalog_dir: Path
