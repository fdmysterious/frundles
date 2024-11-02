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

    def __str__(self):
        return f"{self.kind.value}:{self.value}"


###########################################
# Fetch status and artifact kind
###########################################


class FetchStatus(Enum):
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


class ArtifactKind(Enum):
    """Indicates the artifact kind. Useful for lock file primarly"""

    Library = "lib"
    External = "ext"


###########################################
# Library related classes
###########################################


@dataclass(frozen=True)
class ItemIdentifier:
    """
    Library identification information
    """

    """The kind of the artifact"""
    kind: ArtifactKind

    """The name of the library"""
    name: str

    """The target revision"""
    refspec: RefSpec

    """The locked revision"""
    locked_refspec: Optional[RefSpec] = None

    """Optional friendly name"""
    friendly_name: Optional[str] = None

    def __eq__(self, other: "ItemIdentifier"):
        id_self = self.locked_identifier if self.is_locked() else self.identifier
        id_other = other.locked_identifier if other.is_locked() else other.identifier

        return id_self == id_other

    @property
    def identifier(self):
        return f"{self.kind.value}:{self.name}:{self.refspec.value}"

    @property
    def identifier_path(self):
        return f"{self.name}-{self.refspec.value.replace('/', '_')}"

    @property
    def locked_identifier(self):
        """Returns an identifier string that shall be unique to a given library"""

        if self.locked_refspec is None:
            raise UnlockedRefSpec(self)

        return f"{self.kind.value}:{self.name}:{self.locked_refspec.value}"

    @property
    def locked_identifier_path(self):
        """Returns an identifier that shall be unique to a given library, to be used with folder names"""

        if self.locked_refspec is None:
            raise UnlockedRefSpec(self)

        return f"{self.name}-{self.locked_refspec.value}"

    def lock(self, locked_refspec: RefSpec):
        return ItemIdentifier(
            kind=self.kind,
            name=self.name,
            refspec=self.refspec,
            friendly_name=self.friendly_name,
            locked_refspec=locked_refspec,
        )

    def unlock(self):
        return ItemIdentifier(
            kind=self.kind,
            name=self.name,
            refspec=self.refspec,
            locked_refspec=None,
            friendly_name=self.friendly_name,
        )

    def change_refspec(self, new_refspec: RefSpec):
        return ItemIdentifier(
            kind=self.kind,
            name=self.name,
            refspec=new_refspec,
            locked_refspec=None,
            friendly_name=self.friendly_name,
        )

    def add_friendly_name(self, friendly_name: str):
        return ItemIdentifier(
            kind=self.kind,
            name=self.name,
            refspec=self.refspec,
            locked_refspec=self.locked_refspec,
            friendly_name=friendly_name,
        )

    def is_locked(self):
        return self.locked_refspec is not None

    def __hash__(self):
        if self.locked_refspec:
            return self.locked_identifier.__hash__()
        else:
            return self.identifier.__hash__()


@dataclass
class Library:
    """Contains detailled information about a specific library"""

    """Unique identification information for the library"""
    identifier: ItemIdentifier

    """Git origin URL"""
    origin: str

    def lock(self, refspec: RefSpec):
        return Library(identifier=self.identifier.lock(refspec), origin=self.origin)

    def __hash__(self):
        return self.identifier.__hash__()

    def change_origin(self, new_origin: str):
        return Library(identifier=self.identifier, origin=new_origin)


@dataclass
class External:
    """Contains detailled information about an external reference"""

    """Unique identification information for the external"""
    identifier: ItemIdentifier

    """Git origin URL"""
    origin: str

    """Destination folder"""
    dest_path: Path

    def lock(self, refspec: RefSpec):
        return External(identifier=self.identifier.lock(refspec, origin=self.origin))

    def __hash__(self):
        return self.identifier.__hash__()


###########################################
# Workspace related information
###########################################


class WorkspaceMode(Enum):
    Aggregate = "aggregate"
    Recurse = "recurse"


@dataclass
class WorkspaceInfo:
    catalog_dir: Path
    mode: WorkspaceMode = None

    def __post_init__(self):
        # Set default values
        self.mode = self.mode or WorkspaceMode.Aggregate
