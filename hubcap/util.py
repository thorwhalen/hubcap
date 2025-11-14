"""Utils for hubcap."""

from typing import Union, Dict, Literal, get_args
from collections.abc import Callable, Iterable
from functools import lru_cache
from urllib.parse import urljoin
from operator import attrgetter
import os
import re
import subprocess
import tempfile

from lkj import fields_of_string_formats

from github import Github
from github.Repository import Repository

from hubcap.constants import (
    DFLT_REPO_INFO,
    RepoPropSpec,
    RepoFunc,
    RepoInfo,
)

RepoSpec = Union[str, Repository]


# --------------------------------------------------------------------------------------
# Fundemental functions


@lru_cache(maxsize=3)
def github_token(token=None) -> str:
    token = (
        token
        or os.environ.get("HUBCAP_GITHUB_TOKEN")  # If token not provided, will
        or os.environ.get("GITHUB_TOKEN")  # look under HUBCAP_GITHUB_TOKEN env var
        or get_config(  # look under GITHUB_TOKEN env var
            "GITHUB_TOKEN"
        )  # ask get_config for it (triggering user prompt and file persistence of it)
    )
    if not token:
        raise ValueError("GitHub token not provided")
    return token


@lru_cache(maxsize=3)
def github_object(token=None) -> Github:
    return Github(github_token(token))


@lru_cache(maxsize=10)
def github_repo_object(repo_stub: str, *, token=None) -> Repository:
    """ """
    g = github_object(token)
    try:
        # Get the repository
        return g.get_repo(repo_stub)
    except Exception as e:
        raise RuntimeError(f"Failed to fetch the repo: {repo_stub}. Error: {e}")


# --------------------------------------------------------------------------------------
# Get content


def github_file_contents(
    file_url: str,
    *,
    egress: Callable = lambda file_obj: file_obj.decoded_content.decode("utf-8"),
) -> str:
    """
    Fetches the contents of a file from a GitHub repository.

    Args:
        file_url: The URL of the file to fetch (doesn't have to be a raw file!)
        egress: A function to extract the contents of the file object. By default, it
            decodes the file object's content as UTF-8, but if it's bytes you want,
            don't decode those bytes, and if it's the "file object" you want, just
            use `egress=lambda x: x`.

    Returns:
        str: The contents of the file as a string.

    Raises:
        Exception: If the repository, file, or branch does not exist, or access is denied.


    >>> file_string = github_file_contents('https://github.com/thorwhalen/hubcap/blob/master/setup.cfg')
    >>> print(file_string[:24])
    [metadata]
    name = hubcap

    """
    necessary_parts = ["username", "repository", "branch", "path"]
    url_parts = parse_github_url(file_url)
    if not set(url_parts).issuperset(necessary_parts):
        missing_parts = ", ".join(set(url_parts) - set(necessary_parts))
        raise ValueError(
            "Your URL is missing the following parts: "
            + missing_parts
            + f"Your URL was: {file_url}"
        )

    org, repo, ref, path = map(
        url_parts.get, ["username", "repository", "branch", "path"]
    )
    repo_stub = f"{org}/{repo}"

    repo = github_repo_object(repo_stub)

    try:
        file_obj = repo.get_contents(path, ref=ref)
    except Exception as e:
        raise RuntimeError(f"Failed to fetch the file from {file_url}: {e}")

    return egress(file_obj)


# --------------------------------------------------------------------------------------
def get_repository_info(
    repo: Repository,
    repo_info: RepoInfo = DFLT_REPO_INFO,
    *,
    refresh: bool = True,
    token: str = None,
    use_auth: bool = True,
):
    """Get info about a repository.

    >>> info = get_repository_info('thorwhalen/hubcap')

    This gives us a ``dict`` with default info fields:

    >>> list(info)  # doctest: +NORMALIZE_WHITESPACE +ELLIPSIS
    ['name', 'full_name', 'description', ...]
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

    Args:
        repo: Repository object or string identifier
        repo_info: Info fields to return (default returns standard fields)
        refresh: If True, fetches fresh data from GitHub and caches it.
                 If False, returns cached data if available, otherwise fetches and caches.
        token: GitHub token for authentication. If None and use_auth=True, will use
               token from environment variables or config.
        use_auth: If True (default), uses authenticated requests to avoid rate limits.
                  Set to False to make unauthenticated requests.

    """
    from hubcap.constants import repo_props

    if repo_info is None:
        repo_info = repo_props  # all repo properties

    requested_repo_info = _ensure_repo_info_dict_with_func_values(repo_info)

    # Get GitHub client with authentication if requested
    if use_auth:
        g = github_object(token)
    else:
        g = Github()  # Unauthenticated client

    full_name = ensure_full_name(repo)
    cache_key = f"{full_name}/info.json"

    # Check if we should use cached data
    if not refresh and cache_key in repo_cache_json_files:
        all_info = repo_cache_json_files[cache_key]
    else:
        # Fetch all available repo properties
        repo_obj = g.get_repo(full_name)
        all_info_spec = {prop: prop for prop in repo_props}
        all_info_funcs = _ensure_repo_info_dict_with_func_values(all_info_spec)
        all_info = {k: f(repo_obj) for k, f in all_info_funcs.items()}

        # Cache the complete info
        repo_cache_json_files[cache_key] = all_info

    # Return only the requested fields
    return {
        k: all_info.get(k, f(g.get_repo(full_name)))
        for k, f in requested_repo_info.items()
    }


@lru_cache(maxsize=1)
def cached_github_object():
    """Returns a cached authenticated GitHub client using the default token."""
    return github_object()


# Define or modify the base patterns with their corresponding URL patterns here:
github_url_patterns = {
    "https://github.com/": {
        "pattern": r"^https://github\.com/",
        "url_patterns": [
            # Repository URL
            (r"^(?P<username>[^/]+)/(?P<repository>[^/]+)/?$", "repository"),
            # Branch URL
            (
                r"^(?P<username>[^/]+)/(?P<repository>[^/]+)/tree/(?P<branch>[^/]+)/?$",
                "branch",
            ),
            # File or Directory URL
            (
                r"^(?P<username>[^/]+)/(?P<repository>[^/]+)/blob/(?P<branch>[^/]+)/(?P<path>.+)$",
                "file",
            ),
            # Issues URL
            (
                r"^(?P<username>[^/]+)/(?P<repository>[^/]+)/issues/(?P<issue_number>\d+)$",
                "issue",
            ),
            # Pull Request URL
            (
                r"^(?P<username>[^/]+)/(?P<repository>[^/]+)/pull/(?P<pr_number>\d+)$",
                "pull_request",
            ),
            # Releases URL
            (r"^(?P<username>[^/]+)/(?P<repository>[^/]+)/releases/?$", "releases"),
        ],
    },
    "https://raw.githubusercontent.com/": {
        "pattern": r"^https://raw\.githubusercontent\.com/",
        "url_patterns": [
            # Raw file URL
            (
                r"^(?P<username>[^/]+)/(?P<repository>[^/]+)/(?P<branch>[^/]+)/(?P<path>.+)$",
                "raw_file",
            ),
        ],
    },
    "git@github.com:": {
        "pattern": r"^git@github\.com:",
        "url_patterns": [
            # Clone URL
            (r"^(?P<username>[^/]+)/(?P<repository>[^/]+?)(?:\.git)?$", "clone_url"),
        ],
    },
}


# TODO: Use dol.KeyTemplate to implement parsing and generation of github URLs?
def parse_github_url(url: str) -> dict:
    """
    Parses a GitHub URL and returns a dictionary of its components.

    The returned dict includes a "base" field that indicates the base URL.

    Parameters:
        url (str): The GitHub URL to parse.

    Returns:
        dict: A dictionary containing the parsed components.

    Raises:
        ValueError: If the URL cannot be parsed.

    Examples:

        >>> parse_github_url('https://github.com/torvalds/linux')
        {'base': 'https://github.com/', 'username': 'torvalds', 'repository': 'linux', 'type': 'repository'}
        >>> parse_github_url('https://github.com/torvalds/linux/tree/master')
        {'base': 'https://github.com/', 'username': 'torvalds', 'repository': 'linux', 'branch': 'master', 'type': 'branch'}
        >>> parse_github_url('https://github.com/torvalds/linux/blob/master/README.md')
        {'base': 'https://github.com/', 'username': 'torvalds', 'repository': 'linux', 'branch': 'master', 'path': 'README.md', 'type': 'file'}
        >>> parse_github_url('https://raw.githubusercontent.com/torvalds/linux/master/README.md')
        {'base': 'https://raw.githubusercontent.com/', 'username': 'torvalds', 'repository': 'linux', 'branch': 'master', 'path': 'README.md', 'type': 'raw_file'}
        >>> parse_github_url('https://github.com/torvalds/linux/issues/1')
        {'base': 'https://github.com/', 'username': 'torvalds', 'repository': 'linux', 'issue_number': '1', 'type': 'issue'}
        >>> parse_github_url('https://github.com/torvalds/linux/pull/1')
        {'base': 'https://github.com/', 'username': 'torvalds', 'repository': 'linux', 'pr_number': '1', 'type': 'pull_request'}
        >>> parse_github_url('https://github.com/torvalds/linux/releases')
        {'base': 'https://github.com/', 'username': 'torvalds', 'repository': 'linux', 'type': 'releases'}
        >>> parse_github_url('git@github.com:username/repo.git')
        {'base': 'git@github.com:', 'username': 'username', 'repository': 'repo', 'type': 'clone_url'}

    """

    # Determine the base
    base = None
    for key, value in github_url_patterns.items():
        if re.match(value["pattern"], url):
            base = key
            patterns = value["url_patterns"]
            break
    if not base:
        raise ValueError("URL does not match any known GitHub URL patterns.")

    result = {"base": base}

    # Remove the base from the URL
    rest = re.sub(github_url_patterns[base]["pattern"], "", url)

    # Attempt to match the rest of the URL with the patterns
    for pattern, url_type in patterns:
        m = re.match(pattern, rest)
        if m:
            result.update(m.groupdict())
            result["type"] = url_type
            break
    else:
        raise ValueError("Invalid GitHub URL")

    return result


from lkj import enable_sourcing_from_file


DFLT_RELATIVE_URL_PATTERN = (
    r"(!?\[.*?\]\()"  # Matches the opening part of markdown link or image
    r"((?!http[s]?://|ftp://|mailto:|#|/)[^)]*)"  # Matches relative URLs in markdown
    r"(\))"  # Matches the closing parenthesis
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

    if not root_url.endswith("/"):
        root_url += "/"

    def replacement(match):
        prefix = match.group(1) or match.group(4)
        relative_path = match.group(2) or match.group(5)
        suffix = match.group(3) or match.group(6)
        absolute_url = urljoin(root_url, relative_path)
        return f"{prefix}{absolute_url}{suffix}"

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


def _ensure_repo_info_dict_with_func_values(repo_info: RepoInfo) -> dict[str, RepoFunc]:
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


def ensure_url_suffix(url: str | Repository) -> str:
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


def ensure_github_url(user_repo_str: str, prefix="https://github.com/") -> str:
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


DFLT_GIT_COMMAND: str = "status"

DFLT_PURE_COMMAND_OPTIONS = ("clone", "init", "remote", "config", "help", "version")


# Note: Stems, but diverged from the git function of i2mint/wads project
def _build_git_command(
    command: str = DFLT_GIT_COMMAND,
    work_tree=None,
    git_dir=None,
):
    if command.startswith("git "):
        warn(
            "You don't need to start your command with 'git '. I know it's a git command. Removing that prefix"
        )
        command = command[len("git ") :]
    if work_tree is not None:
        work_tree = os.path.abspath(os.path.expanduser(work_tree))
        if git_dir is None:
            git_dir = os.path.join(work_tree, ".git")
    if git_dir is not None:
        assert os.path.isdir(git_dir), f"Didn't find the git_dir: {git_dir}"
        git_dir = ensure_no_slash_suffix(git_dir)
        if not git_dir.endswith(".git"):
            warn(f"git_dir doesn't end with `.git`: {git_dir}")

    # Commands that should not include --work-tree or --git-dir
    full_command = f"git"
    if work_tree is not None:
        full_command += f' --work-tree="{work_tree}"'
    if git_dir is not None:
        full_command += f' --git-dir="{git_dir}"'

    full_command += f" {command}"

    return full_command


def git(
    command: str = DFLT_GIT_COMMAND,
    *,
    work_tree=None,
    git_dir=None,
    suppress_errors=False,
):
    """Launch git commands.

    :param command: git command (e.g. 'status', 'branch', 'commit -m "blah"', 'push', etc.)
    :param work_tree: The work_tree directory (i.e. where the project is)
    :param git_dir: The .git directory (usually, and by default, will be taken to be "{work_tree}/.git/"
    :param suppress_errors: If True, suppress errors and return an empty string or None.
    :return: What ever the command line returns (decoded to string), or an empty string/None if errors are suppressed.
    """

    """
    git --git-dir=/path/to/my/directory/.git/ --work-tree=/path/to/my/directory/ add myFile
    git --git-dir=/path/to/my/directory/.git/ --work-tree=/path/to/my/directory/ commit -m 'something'
    """
    command_str = _build_git_command(command, work_tree, git_dir)
    try:
        r = subprocess.check_output(command_str, shell=True)
        if isinstance(r, bytes):
            r = r.decode()
        return r.strip()
    except subprocess.CalledProcessError as e:
        if suppress_errors:
            return ""
        else:
            raise e


def _prep_git_clone_args(repo, clone_to_folder=None, branch=None):
    return (
        ensure_github_url(repo),
        ensure_folder_to_clone_into(clone_to_folder),
        branch,
    )


def git_clone(repo, clone_to_folder=None, branch=None):
    """Clone a GitHub repository, optionally specifying a branch.

    Args:
        repo: Repository URL or identifier
        clone_to_folder: Local folder to clone into (creates temp folder if None)
        branch: Optional branch name to clone (clones default branch if None)

    Returns:
        Path to the cloned repository folder
    """
    repo_url, clone_to_folder, branch = _prep_git_clone_args(
        repo, clone_to_folder, branch
    )
    if branch:
        git(f"clone --branch {branch} {repo_url} {clone_to_folder}")
    else:
        git(f"clone {repo_url} {clone_to_folder}")
    return clone_to_folder


def git_wiki_clone(repo, clone_to_folder=None, *, suppress_errors=False):
    repo_url, clone_to_folder = _prep_git_clone_args(repo, clone_to_folder)
    try:
        git(
            f"clone {repo_url}.wiki.git {clone_to_folder}",
            suppress_errors=suppress_errors,
        )
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
from datetime import datetime
from warnings import warn
from importlib.resources import files
from typing import Tuple, Optional
from dol import KvReader, path_get, Files, mk_dirs_if_missing, wrap_kvs
from config2py import (
    simple_config_getter,
    get_app_data_folder,
    process_path,
)

# --------------------------------------------------------------------------------------
# Config and data resources (folders, configs, stores, etc.)

APP_NAME = "hubcap"
REPO_COLLECTION_CONFIGS = "REPO_COLLECTION_CONFIGS"
USER_REPO_COLLECTION_KEY_PROPS_FILE = "repo_collections_key_props.json"

app_data_dir = os.getenv("HUBCAP_DATA_FOLDER", get_app_data_folder(APP_NAME))
app_data_dir = process_path(app_data_dir, ensure_dir_exists=True)
repo_cache_dir = process_path(
    os.path.join(app_data_dir, "repos"), ensure_dir_exists=True
)
repo_cache_store = mk_dirs_if_missing(Files(repo_cache_dir))

get_config = simple_config_getter(APP_NAME)
configs = get_config.configs
data_files = files("hubcap.data")
repo_collections_configs = json.loads(
    data_files.joinpath("dflt_repo_collections_key_props.json").read_text()
)
# get_app_data_folder = get_app_data_folder(APP_NAME)


if USER_REPO_COLLECTION_KEY_PROPS_FILE not in configs:
    configs[USER_REPO_COLLECTION_KEY_PROPS_FILE] = "{}"

try:
    user_key_props = json.loads(configs[USER_REPO_COLLECTION_KEY_PROPS_FILE])
    repo_collections_configs.update(user_key_props)
except Exception as e:
    warn(f"Error loading user repo_collections_key_props.json: {e}", UserWarning)


def _github_object_to_json_serializable(obj):
    """
    Convert a GitHub API object to a JSON-serializable representation.

    Recursively processes dicts, lists, and other structures to ensure
    all nested objects are JSON-serializable.
    """
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: _github_object_to_json_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_github_object_to_json_serializable(item) for item in obj]
    # Handle PyGithub objects by checking for common attributes
    if hasattr(obj, "__dict__") and hasattr(obj, "raw_data"):
        # PyGithub objects typically have a raw_data attribute
        return _github_object_to_json_serializable(obj.raw_data)
    if hasattr(obj, "__dict__") and not isinstance(
        obj, (str, int, float, bool, type(None))
    ):
        # Try to convert to dict representation
        try:
            obj_dict = {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
            return _github_object_to_json_serializable(obj_dict)
        except:
            return str(obj)
    # Fallback to string representation
    return str(obj)


def github_json_serializer(obj):
    """
    Prepare objects for JSON serialization, handling GitHub API objects and datetime.

    Handles datetime objects and other common GitHub API types by recursively
    converting them to JSON-serializable types, then encoding to JSON bytes.

    >>> from datetime import datetime, timezone
    >>> dt = datetime(2021, 1, 15, 22, 34, 10, tzinfo=timezone.utc)
    >>> result = github_json_serializer(dt)
    >>> result
    b'"2021-01-15T22:34:10+00:00"'
    >>> github_json_serializer({'created_at': dt, 'name': 'test'})
    b'{"created_at": "2021-01-15T22:34:10+00:00", "name": "test"}'
    """
    serializable_obj = _github_object_to_json_serializable(obj)
    return json.dumps(serializable_obj).encode("utf-8")


def github_json_deserializer(data):
    """Decode JSON bytes back to Python objects."""
    if isinstance(data, bytes):
        data = data.decode("utf-8")
    return json.loads(data)


JsonFiles = wrap_kvs(
    Files, value_encoder=github_json_serializer, value_decoder=github_json_deserializer
)

repo_cache_json_files = mk_dirs_if_missing(JsonFiles(repo_cache_dir))


# --------------------------------------------------------------------------------------


def defaulted_itemgetter(d, k, default):
    return d.get(k, default)


def _raise_if_error(data):
    """Raises an error if the data has errors"""
    if errors := data.get("errors"):
        msg = "\n".join([e["message"] for e in errors])
        raise RuntimeError(msg)
    return data


DFLT_DISCUSSION_FIELDS = (
    "number",
    "title",
    "body",
    "author",
    "createdAt",
    "updatedAt",
    "comments",
)


# TODO: Pack the graphQL query logic further using template-enabled function
class Discussions(KvReader):
    get_value = partial(path_get, get_value=partial(defaulted_itemgetter, default={}))

    def __init__(
        self,
        repo: RepoSpec,
        *,
        token: str | None = None,
        discussion_fields: tuple[str] = DFLT_DISCUSSION_FIELDS,
        _max_discussions: int = 100,
        _max_comments: int = 100,
        _max_replies: int = 100,
        cache: bool = False,
        refresh: bool = True,
    ):
        repo = ensure_repo_obj(repo)
        self.owner, self.repo_name = ensure_full_name(repo).split("/")
        self.full_name = ensure_full_name(repo)
        self.repo = repo
        self.token = github_token(token)
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.squirrel-girl-preview",
        }
        self.url = "https://api.github.com/graphql"
        self.discussion_fields = discussion_fields
        self._max_discussions = _max_discussions
        self._max_comments = _max_comments
        self._max_replies = _max_replies
        self.cache = cache
        self.refresh = refresh

        if cache:
            self._cache_dir = os.path.join(
                repo_cache_dir, self.full_name, "discussions"
            )
            os.makedirs(self._cache_dir, exist_ok=True)
            self._cache_store = JsonFiles(self._cache_dir)

    @cached_property
    def _discussions(self):
        """The discussions metadata of the repository."""
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
        data = _raise_if_error(response.json())
        return self.get_value(data, "data.repository.discussions", {})

    @cached_property
    def _discussion_numbers(self):
        """The discussion numbers (keys) of the repository."""
        discussions = self._discussions.get("nodes", [])
        return tuple(node["number"] for node in discussions)

    def __iter__(self):
        """Iterates over the discussion numbers (keys of the mapping)."""
        return iter(self._discussion_numbers)

    def __len__(self):
        """Returns the number of discussions."""
        return self._discussions.get("totalCount", 0)

    def __contains__(self, key):
        """Checks if a discussion number (key) is in the mapping."""
        return key in self._discussion_numbers

    def __getitem__(self, key):
        """Gets the discussion data for a given discussion number (key)."""
        # Check cache first if caching is enabled
        if self.cache and not self.refresh:
            cache_key = f"{key}.json"
            if cache_key in self._cache_store:
                return self._cache_store[cache_key]

        # Fetch from GitHub
        query = self._build_query(key)
        response = requests.post(self.url, headers=self.headers, json={"query": query})
        response.raise_for_status()
        data = _raise_if_error(response.json())
        result = self._process_discussion_data(data)

        # Cache if enabled
        if self.cache:
            cache_key = f"{key}.json"
            self._cache_store[cache_key] = result

        return result

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
        return f"""
        query {{
          repository(owner: "{self.owner}", name: "{self.repo_name}") {{
            discussion(number: {key}) {{
              {fields_query}
            }}
          }}
        }}
        """

    def _process_discussion_data(self, data):
        """Processes the discussion data."""
        discussion = self.get_value(data, "data.repository.discussion", {})

        comments = [
            {
                "body": comment["node"]["body"],
                "author": comment["node"]["author"]["login"],
                "replies": [
                    {
                        "body": reply["node"]["body"],
                        "author": reply["node"]["author"]["login"],
                    }
                    for reply in comment["node"]["replies"]["edges"]
                ],
            }
            for comment in discussion.get("comments", {}).get("edges", [])
        ]

        result = {field: discussion.get(field, "") for field in self.discussion_fields}
        result["comments"] = comments
        return result


# TODO: Make it so that we can pass in subdicts of the discussion fields (for example, single or multiple comments)
# TODO: Perculate more control to the arguments
def create_markdown_from_jdict(jdict: dict | Iterable[dict]):
    """
    Creates a markdown representation of a discussion or issue (metadata json-dict).

    Headers are used to separate the different sections.

    This is meant to be applied to json exports of github discussions or issues.

    Note: For issues, the 'comments' field is just a count (int), not the actual
    comment data. For discussions, 'comments' is a list of comment objects with
    their full data including replies.
    """
    if isinstance(jdict, dict) and {"title", "body"} <= jdict.keys():
        markdown = f"# {jdict['title']} (#{jdict['number']})\n\n{jdict['body']}\n\n"

        # Process comments (only if it's a list, not an int count)
        comments = jdict.get("comments")
        if comments and isinstance(comments, list):
            for comment in comments:
                markdown += f"## Comment\n\n{comment['body']}\n\n"

                # Process replies to comments
                if comment.get("replies"):
                    for reply in comment["replies"]:
                        markdown += f"### Reply\n\n{reply['body']}\n\n"

        return markdown
    else:
        assert isinstance(jdict, Iterable), (
            f"Expected dict or Iterable, got {type(jdict)}"
        )
        if isinstance(jdict, dict):
            jdict = jdict.values()
        return "\n\n".join(create_markdown_from_jdict(d) for d in jdict)


# Backwards compatibility alias
create_markdown_from_discussion_jdict = create_markdown_from_jdict

# --------------------------------------------------------------------------------------
# Parse and generate github URLS

import re
from functools import partial
from dol import KeyTemplate

# Import KeyTemplate from your module
# from your_module import KeyTemplate

# For this example, we'll assume KeyTemplate is defined as per your module

# Define mk_key_template to adjust defaults as needed
mk_key_template = partial(KeyTemplate, dflt_pattern="[^/]+", normalize_paths=False)


def _key_templates(github_url_templates):
    """Create KeyTemplate instances for each URL type of github_url_templates"""
    for url_template in github_url_templates:
        # Original template without modifying the slashes
        template = url_template["template"]
        yield (
            url_template["name"],
            mk_key_template(
                template,
                field_patterns=url_template.get("field_patterns", {}),
                from_str_funcs=url_template.get("from_str_funcs", {}),
            ),
        )


# TODO: Order counts in matching, so should be tested and re-ordered automatically before making key_templates
_github_url_templates = [
    {
        "name": "fully_qualified_raw",
        "template": "https://raw.githubusercontent.com/{username}/{repository}/refs/heads/{branch}/{path}",
        "field_patterns": {"path": ".+"},
    },
    {
        "name": "file",
        "template": "https://github.com/{username}/{repository}/blob/{branch}/{path}",
        "field_patterns": {"path": ".+"},
    },
    {
        "name": "raw_file",
        "template": "https://raw.githubusercontent.com/{username}/{repository}/{branch}/{path}",
        "field_patterns": {"path": ".+"},
    },
    {
        "name": "tree_path",
        "template": "https://github.com/{username}/{repository}/tree/{branch}/{path}",
        "field_patterns": {"path": ".+"},
    },
    {
        "name": "branch",
        "template": "https://github.com/{username}/{repository}/tree/{branch}",
    },
    {
        "name": "issue",
        "template": "https://github.com/{username}/{repository}/issues/{issue_number}",
    },
    {
        "name": "pull_request",
        "template": "https://github.com/{username}/{repository}/pull/{pr_number}",
    },
    {
        "name": "releases",
        "template": "https://github.com/{username}/{repository}/releases",
    },
    {
        "name": "repository",
        "template": "https://github.com/{username}/{repository}",
    },
    {
        "name": "clone_url",
        "template": "git@github.com:{username}/{repository}.git",
    },
]

# extract all {template_names} from the templates of _github_url_templates_names to
# make a list of valid components fields
from lkj import fields_of_string_formats

url_template_fields = tuple(
    sorted(
        fields_of_string_formats(
            map(lambda d: d.get("template", ""), _github_url_templates)
        )
    )
)

UrlTemplateField = Literal[url_template_fields]
UrlComponents = dict[UrlTemplateField, str]


def is_url_components(d: dict):
    return all(k in d for k in url_template_fields)


key_templates = dict(_key_templates(_github_url_templates))

_github_url_templates_names = tuple([x["name"] for x in _github_url_templates])

# TODO: Get GithubUrlType from _github_url_templates_names dynamically
GithubUrlType = Literal[_github_url_templates_names]

DFLT_GITHUB_URL_TYPE = "raw_file"


def parse_github_url(url: str, *, include_url_type: bool = True) -> dict:
    """
    Parses a GitHub URL and returns a dictionary of its components.

    The returned dict includes a "url_type" field that indicates the type of the URL.

    Parameters:
        url (str): The GitHub URL to parse.

    Returns:
        dict: A dictionary containing the parsed components.

    Raises:
        ValueError: If the URL cannot be parsed.

    Examples:

        >>> parse_github_url('https://github.com/torvalds/linux')
        {'username': 'torvalds', 'repository': 'linux', 'url_type': 'repository'}
        >>> parse_github_url('https://github.com/torvalds/linux/tree/master')
        {'username': 'torvalds', 'repository': 'linux', 'branch': 'master', 'url_type': 'branch'}
        >>> parse_github_url('https://github.com/torvalds/linux/blob/master/README.md')
        {'username': 'torvalds', 'repository': 'linux', 'branch': 'master', 'path': 'README.md', 'url_type': 'file'}
        >>> parse_github_url('https://raw.githubusercontent.com/torvalds/linux/master/README.md')
        {'username': 'torvalds', 'repository': 'linux', 'branch': 'master', 'path': 'README.md', 'url_type': 'raw_file'}
        >>> parse_github_url('https://github.com/torvalds/linux/issues/1')
        {'username': 'torvalds', 'repository': 'linux', 'issue_number': '1', 'url_type': 'issue'}
        >>> parse_github_url('https://github.com/torvalds/linux/pull/1')
        {'username': 'torvalds', 'repository': 'linux', 'pr_number': '1', 'url_type': 'pull_request'}
        >>> parse_github_url('https://github.com/torvalds/linux/releases')
        {'username': 'torvalds', 'repository': 'linux', 'url_type': 'releases'}
        >>> parse_github_url('git@github.com:username/repo.git')
        {'username': 'username', 'repository': 'repo', 'url_type': 'clone_url'}
    """
    for name in key_templates:
        key_template = key_templates[name]
        try:
            components = key_template.str_to_dict(url)
            if include_url_type:
                components["url_type"] = name
            return components
        except ValueError:
            continue
    raise ValueError("Invalid GitHub URL")


def generate_github_url(
    components: UrlComponents,
    url_type: GithubUrlType = None,
    *,
    prefer_explicit_url_type: bool = True,
    ignore_extra_keys=True,
) -> str:
    """
    Generates a GitHub URL from the provided components dictionary.

    Parameters:
        components (dict): A dictionary containing the URL components.
        url_type (str): The type of the URL to generate.
        prefer_explicit_url_type (bool): If True, the url_type argument takes
            precedence over the 'url_type' key in components.
            This is needed because by default, `parse_github_url` includes the
            'url_type' key, so if you want to easily generate a URL from its
            components, you need an easy way to tell the function to ignore that
            particular key, overriding it with the `url_type` argument.
        ignore_extra_keys (bool): If True, extra keys in the components dictionary

    Returns:
        str: The generated GitHub URL.

    Raises:
        ValueError: If the components are insufficient to generate a URL.

    Examples:

        >>> components = {
        ...     'url_type': 'repository',
        ...     'username': 'torvalds',
        ...     'repository': 'linux',
        ... }
        >>> generate_github_url(components)
        'https://github.com/torvalds/linux'

        >>> components = {
        ...     'url_type': 'branch',
        ...     'username': 'torvalds',
        ...     'repository': 'linux',
        ...     'branch': 'master',
        ... }
        >>> generate_github_url(components)
        'https://github.com/torvalds/linux/tree/master'

        >>> components = {
        ...     'url_type': 'file',
        ...     'username': 'torvalds',
        ...     'repository': 'linux',
        ...     'branch': 'master',
        ...     'path': 'README.md',
        ... }
        >>> generate_github_url(components)
        'https://github.com/torvalds/linux/blob/master/README.md'

        >>> components = {
        ...     'url_type': 'raw_file',
        ...     'username': 'torvalds',
        ...     'repository': 'linux',
        ...     'branch': 'master',
        ...     'path': 'README.md',
        ... }
        >>> generate_github_url(components)
        'https://raw.githubusercontent.com/torvalds/linux/master/README.md'

        >>> components = {
        ...     'url_type': 'issue',
        ...     'username': 'torvalds',
        ...     'repository': 'linux',
        ...     'issue_number': '1',
        ... }
        >>> generate_github_url(components)
        'https://github.com/torvalds/linux/issues/1'

        >>> components = {
        ...     'url_type': 'pull_request',
        ...     'username': 'torvalds',
        ...     'repository': 'linux',
        ...     'pr_number': '1',
        ... }
        >>> generate_github_url(components)
        'https://github.com/torvalds/linux/pull/1'

        >>> components = {
        ...     'url_type': 'releases',
        ...     'username': 'torvalds',
        ...     'repository': 'linux',
        ... }
        >>> generate_github_url(components)
        'https://github.com/torvalds/linux/releases'

        >>> components = {
        ...     'url_type': 'clone_url',
        ...     'username': 'username',
        ...     'repository': 'repo',
        ... }
        >>> generate_github_url(components)
        'git@github.com:username/repo.git'
    """
    components_url_type = components.get("url_type", None)
    if components_url_type and url_type:
        if not prefer_explicit_url_type:
            raise ValueError(
                "You must specify either url_type in components or as an argument, "
                f"but not both: Here you had url_type='{url_type}' "
                f"and url_type in components='{components_url_type}'"
            )
    url_type = url_type or components_url_type
    if not url_type:
        raise ValueError(
            "You must specify a url_type, or components must include 'url_type' key."
        )
    key_template = key_templates.get(url_type)
    if not key_template:
        raise ValueError(f"Unknown URL type '{url_type}'")

    if ignore_extra_keys:
        try:
            # Get only the fields needed for this template
            _components = {k: components[k] for k in key_template._fields}
        except KeyError as e:
            missing_key = e.args[0]
            raise ValueError(
                f"Missing component '{missing_key}' for URL type '{url_type}'."
            )
    else:
        _components = components

    try:
        url = key_template.dict_to_str(_components)
        return url
    except KeyError as e:
        missing_key = e.args[0]
        raise ValueError(
            f"Missing component '{missing_key}' for URL type '{url_type}'."
        )


def transform_github_url(
    url: str, target_url_type: GithubUrlType = DFLT_GITHUB_URL_TYPE, **extras
) -> str:
    """
    Transforms a GitHub URL to another type, updating components as needed.

    Parameters:
        url (str): The original GitHub URL.
        target_url_type (str): The desired URL type.
        **extras: Additional components to update in the URL.

    Returns:
        str: The transformed GitHub URL.

    Raises:
        ValueError: If the URL cannot be parsed or transformed.

    Examples:

        >>> transform_github_url('https://github.com/torvalds/linux', 'clone_url')
        'git@github.com:torvalds/linux.git'

        >>> transform_github_url('https://github.com/torvalds/linux/blob/master/README.md', 'raw_file')
        'https://raw.githubusercontent.com/torvalds/linux/master/README.md'

        >>> transform_github_url('https://github.com/torvalds/linux/issues/1', 'pull_request', pr_number='42')
        'https://github.com/torvalds/linux/pull/42'

        >>> transform_github_url('git@github.com:torvalds/linux.git', 'file', branch='master', path='README.md')
        'https://github.com/torvalds/linux/blob/master/README.md'
    """
    components = parse_github_url(url)
    components["url_type"] = target_url_type
    components.update(extras)
    return generate_github_url(components)
