"""A medley of tools for Hubcap."""

from typing import Iterable, Literal
import time
from functools import partial

from hubcap.base import GithubReader, Issues
from hubcap.util import Discussions


def hubcap(path):
    org, *_path = path.split('/')
    s = GithubReader(org)
    path_iter = iter(_path)
    if (repo := next(path_iter, None)) is not None:
        s = s[repo]
    if (resource := next(path_iter, None)) is not None:
        if resource == 'issues':
            s = Issues(s.src)
        elif resource == 'discussions':
            s = Discussions(s.src)
        else:
            if resource == 'tree':  # then skip this to the next resource (a branch)
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
