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
    return url.split('github.com/')[-1].strip('/')


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
    slash_seperated = suffix.strip('/').split('/')
    if len(slash_seperated) == 2:
        return suffix.strip('/')
    else:
        raise ValueError(f"Couldn't (safely) parse {repo} as a repo full name")


def ensure_github_url(user_repo_str: str, prefix='https://www.github.com/') -> str:
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
# DISCUSSIONS
# At the time of writing this, python's github API doesn't provide discussions info
# so we're using the graphQL github API here, directly, using requests

import os
import requests
from functools import cached_property, partial
import json
from warnings import warn
from importlib.resources import files
from typing import Tuple, Optional
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
        or os.environ.get('HUBCAP_GITHUB_TOKEN')  # If token not provided, will
        or os.environ.get('GITHUB_TOKEN')  # look under HUBCAP_GITHUB_TOKEN env var
        or get_config(  # look under GITHUB_TOKEN env var
            'GITHUB_TOKEN'
        )  # ask get_config for it (triggering user prompt and file persistence of it)
    )
    if not token:
        raise ValueError("GitHub token not provided")
    return token


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


DFLT_DISCUSSION_FIELDS = (
    'number',
    'title',
    'body',
    'author',
    'createdAt',
    'updatedAt',
    'comments',
)


# TODO: Pack the graphQL query logic further using template-enabled function
class Discussions(KvReader):
    get_value = partial(path_get, get_value=partial(defaulted_itemgetter, default={}))

    def __init__(
        self,
        repo: RepoSpec,
        *,
        token: Optional[str] = None,
        discussion_fields: Tuple[str] = DFLT_DISCUSSION_FIELDS,
        _max_discussions: int = 100,
        _max_comments: int = 100,
        _max_replies: int = 100,
    ):
        repo = ensure_repo_obj(repo)
        self.owner, self.repo_name = ensure_full_name(repo).split('/')
        self.repo = repo
        self.token = github_token(token)
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            "Accept": "application/vnd.github.squirrel-girl-preview",
        }
        self.url = 'https://api.github.com/graphql'
        self.discussion_fields = discussion_fields
        self._max_discussions = _max_discussions
        self._max_comments = _max_comments
        self._max_replies = _max_replies

    @cached_property
    def _discussions(self):
        """The discussions metadata of the repository."""
        query = f'''
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
        '''
        response = requests.post(self.url, headers=self.headers, json={'query': query})
        response.raise_for_status()
        data = _raise_if_error(response.json())
        return self.get_value(data, 'data.repository.discussions', {})

    @cached_property
    def _discussion_numbers(self):
        """The discussion numbers (keys) of the repository."""
        discussions = self._discussions.get('nodes', [])
        return tuple(node['number'] for node in discussions)

    def __iter__(self):
        """Iterates over the discussion numbers (keys of the mapping)."""
        return iter(self._discussion_numbers)

    def __len__(self):
        """Returns the number of discussions."""
        return self._discussions.get('totalCount', 0)

    def __contains__(self, key):
        """Checks if a discussion number (key) is in the mapping."""
        return key in self._discussion_numbers

    def __getitem__(self, key):
        """Gets the discussion data for a given discussion number (key)."""
        query = self._build_query(key)
        response = requests.post(self.url, headers=self.headers, json={'query': query})
        response.raise_for_status()
        data = _raise_if_error(response.json())
        return self._process_discussion_data(data)

    def _build_query(self, key):
        """Builds the graphQL query for a discussion."""
        fields_query = "\n".join(self.discussion_fields)
        if "author" in self.discussion_fields:
            fields_query = fields_query.replace("author", "author { login }")
        if "comments" in self.discussion_fields:
            fields_query = fields_query.replace(
                "comments",
                f"""
            comments(first: {self._max_comments}) {{
                edges {{
                    node {{
                        body
                        author {{ login }}
                        replies(first: {self._max_replies}) {{
                            edges {{
                                node {{
                                    body
                                    author {{ login }}
                                }}
                            }}
                        }}
                    }}
                }}
            }}""",
            )
        return f'''
        query {{
          repository(owner: "{self.owner}", name: "{self.repo_name}") {{
            discussion(number: {key}) {{
              {fields_query}
            }}
          }}
        }}
        '''

    def _process_discussion_data(self, data):
        """Processes the discussion data."""
        discussion = self.get_value(data, 'data.repository.discussion', {})

        comments = [
            {
                'body': comment['node']['body'],
                'author': comment['node']['author']['login'],
                'replies': [
                    {
                        'body': reply['node']['body'],
                        'author': reply['node']['author']['login'],
                    }
                    for reply in comment['node']['replies']['edges']
                ],
            }
            for comment in discussion.get('comments', {}).get('edges', [])
        ]

        result = {field: discussion.get(field, '') for field in self.discussion_fields}
        result['comments'] = comments
        return result


# TODO: Perculate more control to the arguments
def create_markdown_from_jdict(jdict: dict):
    """
    Creates a markdown representation of a discussion (metadata json-dict).

    Headers are used to separate the different sections.

    This is meant to be applied to json exports of github discussions or issues.
    """
    markdown = f"# {jdict['title']}\n\n{jdict['body']}\n\n"

    # Process comments
    if jdict.get('comments'):
        for comment in jdict['comments']:
            markdown += f"## Comment\n\n{comment['body']}\n\n"

            # Process replies to comments
            if comment.get('replies'):
                for reply in comment['replies']:
                    markdown += f"### Reply\n\n{reply['body']}\n\n"

    return markdown
