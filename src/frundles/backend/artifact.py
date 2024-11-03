"""
# Frundles library management

- Florian Dupeyron <florian.dupeyron@mugcat.fr>
- August 2024
"""

import logging
import tempfile
import traceback
import urllib.parse

from pathlib import Path

from ..model import ItemIdentifier, FetchStatus, Library, WorkspaceInfo, RefSpec
from git import Repo, InvalidGitRepositoryError

from ..errors import InvalidOrigin

from . import catalog


log = logging.getLogger("backend.artifact")


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
    ref_name = lib.identifier.refspec.value

    with tempfile.TemporaryDirectory() as tmpdir:
        # print(f"Fetch to {tmpdir}")

        repo = Repo.init(tmpdir)
        origin = repo.create_remote("origin", url=repo_url)

        origin.fetch()

        commit_sha1 = repo.git.rev_parse(f"origin/{ref_name}")

        return commit_sha1


###########################################
# Library status management
###########################################


def check_status(
    root_wspace: WorkspaceInfo, cur_wspace: WorkspaceInfo, lib_id: ItemIdentifier
):
    folder_path = catalog.get_lib_path(root_wspace, cur_wspace, lib_id)

    # Step 1: Checked that folder exists
    if not folder_path.exists():
        return FetchStatus.NotCloned

    elif not folder_path.is_dir():
        return FetchStatus.Invalid

    # Step 2: Check properties of git repository
    try:
        repo = Repo(folder_path)
        oid = repo.head.commit.hexsha

        # Commit doesn't correspond to target
        if oid != lib_id.locked_refspec.value:
            return FetchStatus.Modified

        # Uncomitted modifications exists in repo
        elif _is_workspace_dirty(repo):
            return FetchStatus.Dirty

        else:
            return FetchStatus.Ok

    # Directory is not a valid git repository
    except InvalidGitRepositoryError:
        return FetchStatus.Invalid


###########################################
# Library status management
###########################################


def get_origin(repo_dir: Path):
    if (repo_dir / ".git").is_dir():
        try:
            repo = Repo(repo_dir)

            if "origin" in repo.remotes:
                url = (
                    repo.remotes.origin.url
                )  # TODO # Check if remotes[0] can be used to get URL from default remotes with a name different than 'origin'?
                return url
            else:
                log.warning(
                    f"Repo in '{repo_dir}' has no 'origin' remote URL, assuming local directory path"
                )
                return str(repo_dir.resolve())

        except Exception as exc:
            log.error(f"Could not get remote URL for repository {repo_dir}: {str(exc)}")
            log.debug(traceback.format_exc())
            return None
    else:
        return None


def has_local_origin(origin: str):
    url = urllib.parse.urlsplit(origin)
    return url.scheme in {"", "file"}


def clone(target_dir: Path, origin: str, target_refspec: RefSpec):
    target_dir = Path(target_dir)
    target_dir.mkdir(exist_ok=False, parents=True)

    repo = Repo.init(target_dir)
    origin = repo.create_remote("origin", url=origin)

    origin.fetch()

    repo.git.checkout(target_refspec.value)


def update(target_dir: Path, origin: str, target_refspec: RefSpec):
    log.info(f"Update repo at {target_dir} to reference {target_refspec}")

    # Check valid origin
    existing_origin = get_origin(target_dir)

    if str(existing_origin) != str(origin):
        raise InvalidOrigin(target_origin=origin, got_origin=existing_origin)

    # Open repo, fetch, checkout target reference
    repo = Repo(target_dir)
    origin = repo.remotes.origin

    origin.fetch()

    repo.git.checkout(target_refspec.value)
