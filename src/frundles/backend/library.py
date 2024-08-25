"""
# Frundles library management

- Florian Dupeyron <florian.dupeyron@mugcat.fr>
- August 2024
"""

import logging
import tempfile

from ..model import LibraryIdentifier, LibraryStatus, Library
from git import Repo, InvalidGitRepositoryError
from pathlib import Path


log = logging.getLogger("backend.library")


###########################################
# Utility functions
###########################################


def _is_workspace_dirty(repo: Repo):
    """Check if a repository workspace is clean.

    This checks that there is :
        - No diff with tracked files
        - No new untracked file
    """

    return repo.index.diff(None) or repo.untracked_files


def _get_commit_sha1(lib: Library):
    """Get the associated commit SHA1 for a given repository"""

    repo_url = lib.origin
    ref_name = lib.refspec.value

    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"Fetch to {tmpdir}")

        repo = Repo.init(tmpdir)
        origin = repo.create_remote("origin", url=repo_url)

        origin.fetch()

        commit_sha1 = repo.git.rev_parse(f"origin/{ref_name}")

        return commit_sha1


###########################################
# Library status management
###########################################


def check_status(catalog_dir: Path, lib_id: LibraryIdentifier):
    folder_path = catalog_dir / lib_id.locked_identifier_path

    # Step 1: Checked that folder exists
    if not folder_path.exists():
        return LibraryStatus.NotCloned

    elif not folder_path.is_dir():
        return LibraryStatus.Invalid

    # Step 2: Check properties of git repository
    try:
        repo = Repo(folder_path)
        oid = repo.head.commit.hexsha

        # Commit doesn't correspond to target
        if oid != lib_id.locked_refspec.value:
            return LibraryStatus.Modified

        # Uncomitted modifications exists in repo
        elif _is_workspace_dirty(repo):
            return LibraryStatus.Dirty

        else:
            return LibraryStatus.Ok

    # Directory is not a valid git repository
    except InvalidGitRepositoryError:
        return LibraryStatus.Invalid
