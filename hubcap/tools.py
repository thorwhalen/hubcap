"""A medley of tools for Hubcap."""

from typing import Iterable, Literal
import time
from functools import partial

from dol import KvReader
from i2 import Sig
from github.Repository import Repository

from hubcap.base import GithubReader, RepoReader
from hubcap.constants import repo_collection_names
from hubcap.util import RepoSpec, ensure_url_suffix


def hubcap(path: RepoSpec):
    path = ensure_url_suffix(path)
    if '/' not in path:
        org = path
        return GithubReader(org)
    # at this point we have at least org/repo/...
    org, repo, *_path = path.split('/')
    s = RepoReader(f"{org}/{repo}")
    path_iter = iter(_path)
    if (repo := next(path_iter, None)) is not None:
        s = s[repo]
    if (resource := next(path_iter, None)) is not None:
        if resource in repo_collection_names or resource == 'discussions':
            s = RepoReader(s.src)[resource]
        else:
            if resource == 'tree':
                # then consider this to be a request for branches
                resource = next(path_iter)
            s = s[resource]
    # Process the rest of the path with the s mapping
    for part in path_iter:
        s = s[part]
    return s


def team_repositories_action(
    repositories: Iterable[str],
    team: str,
    *,
    action: Literal["add_to_repo", "remove_from_repos"],
    org: str,
    wait_s: int = 1,
):
    """
    Add a list of repositories to a team with read permission
    """
    # Create a GitHub instance using an access token
    g = GithubReader()._github

    # Get the organization object by name
    org_ = g.get_organization(org)

    # Get the team object by name
    team_ = org_.get_team_by_slug(team)
    action_ = getattr(team_, action)

    for repo in repositories:
        # Get the repository object by name
        repo_ = g.get_repo(repo)
        # Carry out the action
        action_(repo_)
        time.sleep(wait_s)


add_repos_to_team = partial(team_repositories_action, action="add_to_repo")
rm_repos_from_team = partial(team_repositories_action, action="remove_from_repos")
