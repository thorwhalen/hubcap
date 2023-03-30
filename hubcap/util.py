"""Utils for hubcap."""

from typing import Union, Dict
from functools import lru_cache
from operator import attrgetter

from github import Github
from github.Repository import Repository

from hubcap.constants import (
    DFLT_REPO_INFO,
    RepoPropSpec,
    RepoFunc,
    RepoInfo,
    repo_props,
)

RepoSpec = Union[str, Repository]


def get_repository_info(repo: Repository, repo_info: RepoInfo = DFLT_REPO_INFO):
    """Get info about a repository.

    >>> info = get_repository_info('thorwhalen/hubcap')

    This gives us a ``dict`` with default info fields:

    >>> list(info)  # doctest: +NORMALIZE_WHITESPACE
    ['name', 'full_name', 'description', 'stargazers_count',
    'forks_count', 'watchers_count', 'html_url', 'last_commit_date']
    >>> info['name']
    'hubcap'
    >>> info['html_url']
    'https://github.com/thorwhalen/hubcap'
    >>> info['stargazers_count'] >= 1
    True

    We can also specify a custom ``repo_info`` get different info.

    You can specify a space separated string of repo properties:

    >>> get_repository_info('thorwhalen/hubcap', 'name html_url')
    {'name': 'hubcap', 'html_url': 'https://github.com/thorwhalen/hubcap'}

    Note that you have a list of valid repo properties in ``constants.repo_props``,
    which is dynamically generated from the ``github.Repository.Repository`` class:

    >>> from hubcap.constants import repo_props
    >>> len(repo_props) >= 90
    True

    If you want to give the fields different names, or use a function to compute some
    custom information based on the repo you can specify a  dict of
    ``{field: prop_spec, ...}`` values where ``prop_spec`` is either a valid repo
    property or a function to compute the value (the function needs to take a
    ``Repository`` as its first and only required argument).

    >>> get_repository_info(
    ...     'thorwhalen/hubcap',
    ...     {'name': 'name', 'has stars': lambda repo: repo.stargazers_count > 0}
    ... )
    {'name': 'hubcap', 'has stars': True}

    """
    repo_info = _ensure_repo_info_dict_with_func_values(repo_info)
    g = cached_github_object()
    repo = g.get_repo(ensure_full_name(repo))
    return {k: f(repo) for k, f in repo_info.items()}


@lru_cache(maxsize=1)
def cached_github_object():
    return Github()


# --------------------------------------------------------------------------- #
# Ensure functions

# TODO: Add validation to all the "ensure" functions:
# TODO: Could make it more robust by defining github url regexes
#  (or perhaps github package has some utils for this already?)


def _ensure_repo_func(prop_spec: RepoPropSpec) -> RepoFunc:
    """Ensure callable (convert strings to attribute getters)"""
    if isinstance(prop_spec, str):
        return attrgetter(prop_spec)
    else:
        assert callable(prop_spec)
        return prop_spec


def _ensure_repo_info_dict_with_func_values(repo_info: RepoInfo) -> Dict[str, RepoFunc]:
    """Ensure a dict of repo info.

    >>> d = _ensure_repo_info_dict_with_func_values('name html_url')
    >>> all(callable(x) for x in d.values())
    True
    """
    if isinstance(repo_info, str):
        prop_names = repo_info.split()
        repo_info = {x: x for x in prop_names}
    repo_info = dict(repo_info)
    return {k: _ensure_repo_func(v) for k, v in repo_info.items()}


def ensure_full_name(repo: RepoSpec) -> str:
    """Ensure we have a full name (user/repo string)

    >>> ensure_full_name('https://www.github.com/thorwhalen/hubcap')
    'thorwhalen/hubcap'
    >>> ensure_full_name('github.com/thorwhalen/hubcap/')
    'thorwhalen/hubcap'
    >>> ensure_full_name('thorwhalen/hubcap')
    'thorwhalen/hubcap'
    """
    if isinstance(repo, Repository):
        return repo.full_name
    suffix = repo.split("github.com/")[-1]
    slash_seperated = suffix.strip("/").split("/")
    if len(slash_seperated) == 2:
        return suffix.strip("/")
    else:
        ValueError(f"Couldn't (safely) parse {repo} as a repo full name")


def ensure_github_url(user_repo_str: str, prefix="https://www.github.com/") -> str:
    """Ensure a string to a github url

    >>> ensure_github_url('https://www.github.com/thorwhalen/hubcap')
    'https://www.github.com/thorwhalen/hubcap'
    >>> ensure_github_url('https://www.github.com/github.com/thorwhalen/hubcap/')
    'https://www.github.com/thorwhalen/hubcap'
    """
    user_repo_str = ensure_full_name(user_repo_str)
    return f"{prefix.strip('/')}/{user_repo_str.strip('/')}"


def ensure_repo_obj(repo: Union[Repository, str]) -> Repository:
    """Ensure a Repository object.

    >>> ensure_repo_obj('thorwhalen/hubcap')
    Repository(full_name="thorwhalen/hubcap")
    >>> repo = ensure_repo_obj('https://www.github.com/thorwhalen/hubcap')
    >>> repo
    Repository(full_name="thorwhalen/hubcap")

    And if we pass in a ``Repository`` object, we just get it back:

    >>> ensure_repo_obj(repo)
    Repository(full_name="thorwhalen/hubcap")

    """
    if isinstance(repo, Repository):
        return repo
    else:
        g = cached_github_object()
        return g.get_repo(ensure_full_name(repo))
