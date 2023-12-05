"""Utils for hubcap."""

from typing import Union, Dict
from functools import lru_cache
from operator import attrgetter

from github import Github, GithubException
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


def ensure_url_suffix(url: Union[str, Repository]) -> str:
    """Ensure a url suffix, that is, get rid of the (...)www.github.com prefix.

    >>> ensure_url_suffix('https://www.github.com/thorwhalen/hubcap/README.md')
    'thorwhalen/hubcap/README.md'
    >>> ensure_url_suffix('www.github.com/thorwhalen/hubcap/README.md')
    'thorwhalen/hubcap/README.md'
    >>> ensure_url_suffix('thorwhalen/hubcap/README.md')
    'thorwhalen/hubcap/README.md'
    """
    if isinstance(url, Repository):
        return url.full_name
    return url.split("github.com/")[-1].strip("/")


def ensure_full_name(repo: RepoSpec) -> str:
    """Ensure we have a full name (user/repo string)

    >>> ensure_full_name('https://www.github.com/thorwhalen/hubcap')
    'thorwhalen/hubcap'
    >>> ensure_full_name('github.com/thorwhalen/hubcap/')
    'thorwhalen/hubcap'
    >>> ensure_full_name('thorwhalen/hubcap')
    'thorwhalen/hubcap'
    """
    suffix = ensure_url_suffix(repo)
    slash_seperated = suffix.strip("/").split("/")
    if len(slash_seperated) == 2:
        return suffix.strip("/")
    else:
        raise ValueError(f"Couldn't (safely) parse {repo} as a repo full name")


def ensure_github_url(user_repo_str: str, prefix="https://www.github.com/") -> str:
    """Ensure a string to a github url

    >>> ensure_github_url('https://www.github.com/thorwhalen/hubcap')
    'https://www.github.com/thorwhalen/hubcap'
    >>> ensure_github_url('https://www.github.com/github.com/thorwhalen/hubcap/')
    'https://www.github.com/thorwhalen/hubcap'
    """
    user_repo_str = ensure_full_name(user_repo_str)
    return f"{prefix.strip('/')}/{user_repo_str.strip('/')}"


def ensure_repo_obj(repo: RepoSpec) -> Repository:
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


# --------------------------------------------------------------------------------------
# At the time of writing this, python's github API doesn't provide discussions info
# so we're using the graphQL github API here, directly, using requests

import os
import requests
from functools import cached_property, partial
import json
from warnings import warn
from importlib.resources import files
from dol import KvReader, path_get
from config2py import simple_config_getter

APP_NAME = 'hubcap'
REPO_COLLECTION_CONFIGS = 'REPO_COLLECTION_CONFIGS'
USER_REPO_COLLECTION_KEY_PROPS_FILE = 'repo_collections_key_props.json'

get_config = simple_config_getter(APP_NAME)
configs = get_config.configs
data_files = files('hubcap.data')
repo_collections_configs = json.loads(
    data_files.joinpath('dflt_repo_collections_key_props.json').read_text()
)


def github_token(token=None):
    token = (
        token
        or get_config('HUBCAP_GITHUB_TOKEN')  # If token not provided, will
        or os.getenv('GITHUB_TOKEN')  # look under HUBCAP_GITHUB_TOKEN env var
        or get_config(  # look under GITHUB_TOKEN env var
            'GITHUB_TOKEN'
        )  # ask get_config for it (triggering user prompt and file persistence of it)
    )


if USER_REPO_COLLECTION_KEY_PROPS_FILE not in configs:
    configs[USER_REPO_COLLECTION_KEY_PROPS_FILE] = '{}'

try:
    user_key_props = json.loads(configs[USER_REPO_COLLECTION_KEY_PROPS_FILE])
    repo_collections_configs.update(user_key_props)
except Exception as e:
    warn(f'Error loading user repo_collections_key_props.json: {e}', UserWarning)


def defaulted_itemgetter(d, k, default):
    return d.get(k, default)


def _raise_if_error(data):
    """Raises an error if the data has errors"""
    if errors := data.get('errors'):
        msg = '\n'.join([e['message'] for e in errors])
        raise RuntimeError(msg)
    return data


# TODO: Pack the graphQL query logic further using template-enabled function
class Discussions(KvReader):
    get_value = partial(path_get, get_value=partial(defaulted_itemgetter, default={}))
    _max_discussions = 100

    def __init__(self, repo: RepoSpec, token=None):
        repo = ensure_repo_obj(repo)
        self.owner, self.repo_name = ensure_full_name(repo).split('/')
        self.repo = repo
        self.token = github_token(token)
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.url = "https://api.github.com/graphql"

    @cached_property
    def _discussions(self):
        query = f"""
        query {{
          repository(owner: "{self.owner}", name: "{self.repo_name}") {{
            discussions(first: {self._max_discussions}) {{
              nodes {{
                number
              }}
              totalCount
            }}
          }}
        }}
        """
        response = requests.post(self.url, headers=self.headers, json={"query": query})
        response.raise_for_status()
        data = _raise_if_error(json.loads(response.text))
        return self.get_value(data, 'data.repository.discussions')

    # TODO: Should get rid of this and replace uses with use of _discussions
    @cached_property
    def _discussion_numbers(self):
        headers = {"Authorization": f"Bearer {self.token}"}
        url = "https://api.github.com/graphql"
        query = f"""
        query {{
        repository(owner: "{self.owner}", name: "{self.repo_name}") {{
            discussions(first: {self._max_discussions}) {{
            nodes {{
                number
            }}
            }}
        }}
        }}
        """
        response = requests.post(url, headers=headers, json={"query": query})
        response.raise_for_status()
        data = response.json()
        if errors := data.get('errors'):
            msg = '\n'.join([e['message'] for e in errors])
            raise RuntimeError(msg)
        return tuple(
            [
                node['number']
                for node in self.get_value(data, "data.repository.discussions.nodes")
            ]
        )

    def __iter__(self):
        yield from self._discussion_numbers
        # nodes = self._discussions.get('nodes', ())
        # return (node["number"] for node in nodes)

    def __len__(self):
        return len(self._discussion_numbers)
        # return self._discussions.get('totalCount', 0)

    def __contains__(self, key):
        nodes = self._discussions.get('nodes', ())
        return key in (node["number"] for node in nodes)

    def __getitem__(self, key):
        query = f"""
        query {{
          repository(owner: "{self.owner}", name: "{self.repo_name}") {{
            discussion(number: {key}) {{
              title
              body
            }}
          }}
        }}
        """
        response = requests.post(self.url, headers=self.headers, json={"query": query})
        response.raise_for_status()
        data = _raise_if_error(response.json())
        discussion = self.get_value(data, 'data.repository.discussion')
        return {
            "title": discussion.get('title', ''),
            "body": discussion.get('body', ''),
        }
