"""A medley of tools for Hubcap."""

from typing import Iterable, Literal
import time
from functools import partial

from github import Github
from hubcap.base import GitHubReader


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
    g = GitHubReader()._github

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
