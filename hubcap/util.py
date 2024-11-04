"""Utils for hubcap."""

from typing import Union, Dict
from functools import lru_cache
from urllib.parse import urljoin
from operator import attrgetter
import os
import re
import subprocess
import tempfile

from github import Github
from github.Repository import Repository

from hubcap.constants import (
    DFLT_REPO_INFO,
    RepoPropSpec,
    RepoFunc,
    RepoInfo,
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


from lkj import enable_sourcing_from_file


DFLT_RELATIVE_URL_PATTERN = (
    r'(!?\[.*?\]\()'  # Matches the opening part of markdown link or image
    r'((?!http[s]?://|ftp://|mailto:|#|/)[^)]*)'  # Matches relative URLs in markdown
    r'(\))'  # Matches the closing parenthesis
    r'|(<img\s+[^>]*src=")'  # Matches the opening part of HTML img tag
    r'((?!http[s]?://|ftp://|mailto:|#|/)[^"]*)'  # Matches relative URLs in HTML img tag
    r'(")'  # Matches the closing quote of the src attribute
)


@enable_sourcing_from_file(write_output=True)
def replace_relative_urls(
    markdown_str: str,
    root_url,
    *,
    relative_url_pattern: str = DFLT_RELATIVE_URL_PATTERN,
):
    """
    Replace relative URLs in a markdown string with absolute URLs based on the root_url.

    This is useful, for example, to solve problems like when pypi renders markdown and
    images are not shown because they are relative URLs.
    See [issue]()

    Args:
        markdown_str (str): The markdown content containing URLs.
        root_url (str): The base URL to resolve relative URLs against.

    Returns:
        str: The markdown content with relative URLs replaced by absolute URLs.

    Examples:
        >>> markdown_str = '''
        ... [With dot](./page)
        ... ![With double dot](../image.png)
        ... ![](relative/path/to/image.png)
        ... [Absolute Link](http://example.com)
        ... <img src="path/to/image" width="320">
        ... '''
        >>> root_url = 'http://mysite.com/docs'
        >>> print(replace_relative_urls(markdown_str, root_url))
        <BLANKLINE>
        [With dot](http://mysite.com/docs/page)
        ![With double dot](http://mysite.com/image.png)
        ![](http://mysite.com/docs/relative/path/to/image.png)
        [Absolute Link](http://example.com)
        <img src="http://mysite.com/docs/path/to/image" width="320">
        <BLANKLINE>
    """
    # Define a pattern to match markdown links and images with relative URLs
    relative_url_pattern = re.compile(relative_url_pattern)

    if not root_url.endswith('/'):
        root_url += '/'

    def replacement(match):
        prefix = match.group(1) or match.group(4)
        relative_path = match.group(2) or match.group(5)
        suffix = match.group(3) or match.group(6)
        absolute_url = urljoin(root_url, relative_path)
        return f'{prefix}{absolute_url}{suffix}'

    updated_markdown = relative_url_pattern.sub(replacement, markdown_str)
    return updated_markdown


# --------------------------------------------------------------------------- #
# Ensure functions

# TODO: Add validation to all the "ensure" functions:
# TODO: Could make it more robust by defining github url regexes
#  (or perhaps github package has some utils for this already?)

# standard_lib_dir = os.path.dirname(os.__file__)
path_sep = os.path.sep


def ensure_folder_to_clone_into(folder_to_clone_into: str = None):
    """Return a folder to clone into. If not provided, create a temporary folder."""
    if folder_to_clone_into is None:
        folder_to_clone_into = tempfile.mkdtemp()
    return folder_to_clone_into


def ensure_slash_suffix(s: str):
    if not s.endswith(path_sep):
        s += path_sep
    return s


def ensure_no_slash_suffix(s: str):
    return s.rstrip(path_sep)


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
    """Ensure a url suffix, that is, get rid of the (...)github.com prefix.

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


def ensure_github_url(user_repo_str: str, prefix='https://github.com/') -> str:
    """Ensure a string to a github url

    >>> ensure_github_url('https://www.github.com/thorwhalen/hubcap')
    'https://github.com/thorwhalen/hubcap'
    >>> ensure_github_url('https://github.com/github.com/thorwhalen/hubcap/')
    'https://github.com/thorwhalen/hubcap'
    """
    user_repo_str = ensure_full_name(user_repo_str)
    return f"{prefix.strip('/')}/{user_repo_str.strip('/')}"


def ensure_repo_obj(repo: RepoSpec) -> Repository:
    """Ensure a Repository object.

    >>> ensure_repo_obj('thorwhalen/hubcap')
    Repository(full_name="thorwhalen/hubcap")
    >>> repo = ensure_repo_obj('https://github.com/thorwhalen/hubcap')
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
# GIT FUNCTIONS

from warnings import warn
import os
import subprocess


DFLT_GIT_COMMAND: str = 'status'

DFLT_PURE_COMMAND_OPTIONS = ('clone', 'init', 'remote', 'config', 'help', 'version')


# Note: Stems, but diverged from the git function of i2mint/wads project
def _build_git_command(
    command: str = DFLT_GIT_COMMAND, work_tree=None, git_dir=None,
):
    if command.startswith('git '):
        warn(
            "You don't need to start your command with 'git '. I know it's a git command. Removing that prefix"
        )
        command = command[len('git ') :]
    if work_tree is not None:
        work_tree = os.path.abspath(os.path.expanduser(work_tree))
        if git_dir is None:
            git_dir = os.path.join(work_tree, '.git')
    if git_dir is not None:
        assert os.path.isdir(git_dir), f"Didn't find the git_dir: {git_dir}"
        git_dir = ensure_no_slash_suffix(git_dir)
        if not git_dir.endswith('.git'):
            warn(f"git_dir doesn't end with `.git`: {git_dir}")

    # Commands that should not include --work-tree or --git-dir
    full_command = f'git'
    if work_tree is not None:
        full_command += f' --work-tree="{work_tree}"'
    if git_dir is not None:
        full_command += f' --git-dir="{git_dir}"'

    full_command += f' {command}'

    return full_command


def git(command: str = DFLT_GIT_COMMAND, *, work_tree=None, git_dir=None):
    """Launch git commands.

    :param command: git command (e.g. 'status', 'branch', 'commit -m "blah"', 'push', etc.)
    :param work_tree: The work_tree directory (i.e. where the project is)
    :param git_dir: The .git directory (usually, and by default, will be taken to be "{work_tree}/.git/"
    :return: What ever the command line returns (decoded to string)
    """

    """

    git --git-dir=/path/to/my/directory/.git/ --work-tree=/path/to/my/directory/ add myFile
    git --git-dir=/path/to/my/directory/.git/ --work-tree=/path/to/my/directory/ commit -m 'something'

    """
    command_str = _build_git_command(command, work_tree, git_dir)
    r = subprocess.check_output(command_str, shell=True)
    if isinstance(r, bytes):
        r = r.decode()
    return r.strip()


def _prep_git_clone_args(repo, clone_to_folder=None):
    return (ensure_github_url(repo), ensure_folder_to_clone_into(clone_to_folder))


def git_clone(repo, clone_to_folder=None):
    repo_url, clone_to_folder = _prep_git_clone_args(repo, clone_to_folder)
    git(f'clone {repo_url} {clone_to_folder}')
    return clone_to_folder


def git_wiki_clone(repo, clone_to_folder=None):
    repo_url, clone_to_folder = _prep_git_clone_args(repo, clone_to_folder)
    try:
        git(f'clone {repo_url}.wiki.git {clone_to_folder}')
    except subprocess.CalledProcessError as e:
        if next(iter(e.args), None) == 128:
            warn(f"It's possible that the repository doesn't have a wiki. Error: {e}")
        raise e

    return clone_to_folder


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
        raise ValueError('GitHub token not provided')
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
            'Accept': 'application/vnd.github.squirrel-girl-preview',
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
        fields_query = '\n'.join(self.discussion_fields)
        if 'author' in self.discussion_fields:
            fields_query = fields_query.replace('author', 'author { login }')
        if 'comments' in self.discussion_fields:
            fields_query = fields_query.replace(
                'comments',
                f'''
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
            }}''',
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
