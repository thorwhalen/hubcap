"""
Transformation graph for GitHub project references with flexible input handling.

This module provides automatic conversion between different representations of GitHub
projects using i2.castgraph. It integrates with hubcap's URL parsing/generation and
supports user-configurable local project folder discovery.

Supported Kinds
---------------
- **proj_name**: Simple project name (e.g., "dol")
- **github_stub**: Org/repo format (e.g., "i2mint/dol")
- **github_https_url**: HTTPS URLs (e.g., "https://github.com/i2mint/dol")
- **github_ssh_url**: SSH URLs (e.g., "git@github.com:i2mint/dol.git")
- **local_git_folder**: Local path with .git folder
- **local_proj_folder**: Alias for local_git_folder
- **url_components**: Parsed URL components dict

Configuration
-------------
Register your local project root folders in the hubcap config:

    >>> from hubcap.casting import register_project_root, get_project_roots
    >>> register_project_root('/Users/me/projects/personal')  # doctest: +SKIP
    >>> register_project_root('/Users/me/work')  # doctest: +SKIP
    >>> get_project_roots()  # doctest: +SKIP
    ['/Users/me/projects/personal', '/Users/me/work']

The system will search one level deep in these roots for folders containing .git.

Usage with Ingress Decorator
-----------------------------
    >>> from hubcap.casting import project_kinds
    >>>
    >>> @project_kinds.ingress('local_proj_folder')
    ... def process_project(project_path: str):
    ...     '''Accepts any project reference, gets local path.'''
    ...     return f"Processing {project_path}"
    >>>
    >>> process_project("dol")  # doctest: +SKIP
    >>> process_project("i2mint/dol")  # doctest: +SKIP
    >>> process_project("https://github.com/i2mint/dol")  # doctest: +SKIP

Direct Transformation
---------------------
    >>> from hubcap.casting import normalize_project
    >>>
    >>> # From name to local path
    >>> normalize_project("dol", to_kind='local_proj_folder')  # doctest: +SKIP
    '/Users/thorwhalen/Dropbox/py/proj/i/dol'
    >>>
    >>> # From URL to stub
    >>> normalize_project(
    ...     "https://github.com/i2mint/dol/tree/master",
    ...     to_kind='github_stub'
    ... )  # doctest: +SKIP
    'i2mint/dol'
"""

import os
import re
import subprocess
from pathlib import Path
from functools import lru_cache
from typing import Literal

from i2.castgraph import TransformationGraph
from hubcap.util import parse_github_url, generate_github_url, get_config, LOCAL_PROJECT_ROOTS_FILE

# ======================================================================================
# Configuration Management
# ======================================================================================


def get_project_roots() -> list[str]:
    """Get the list of registered project root folders.

    Returns:
        List of absolute paths to project root directories

    Example:
        >>> roots = get_project_roots()  # doctest: +SKIP
        >>> print(roots)  # doctest: +SKIP
        ['/Users/me/projects', '/Users/me/work']
    """
    config = get_config(LOCAL_PROJECT_ROOTS_FILE, default='')
    if not config:
        return []
    # Config stores as newline-separated paths
    roots = [p.strip() for p in config.split('\n') if p.strip()]
    return roots


def register_project_root(root_path: str) -> None:
    """Register a new project root folder.

    Projects (folders with .git) one level below this root will be discoverable
    by project name.

    Args:
        root_path: Absolute path to a directory containing project folders

    Example:
        >>> register_project_root('/Users/me/projects')  # doctest: +SKIP
        >>> register_project_root('/Users/me/work/repos')  # doctest: +SKIP
    """
    root_path = str(Path(root_path).resolve())
    if not os.path.isdir(root_path):
        raise ValueError(f"Not a directory: {root_path}")

    roots = get_project_roots()
    if root_path not in roots:
        roots.append(root_path)
        # Store as newline-separated
        get_config.configs[LOCAL_PROJECT_ROOTS_FILE] = '\n'.join(roots)


def unregister_project_root(root_path: str) -> None:
    """Remove a project root folder from the registry.

    Args:
        root_path: Path to remove from registered roots
    """
    root_path = str(Path(root_path).resolve())
    roots = get_project_roots()
    if root_path in roots:
        roots.remove(root_path)
        get_config.configs[LOCAL_PROJECT_ROOTS_FILE] = '\n'.join(roots)


@lru_cache(maxsize=128)
def _find_project_by_name(project_name: str) -> str | None:
    """Search registered roots for a project folder by name.

    Args:
        project_name: Simple project name (folder name)

    Returns:
        Absolute path to project folder if found, None otherwise
    """
    for root in get_project_roots():
        candidate = os.path.join(root, project_name)
        if os.path.isdir(candidate) and os.path.exists(os.path.join(candidate, '.git')):
            return candidate
    return None


def _get_git_remote_url(git_folder: str) -> str | None:
    """Get the origin remote URL from a git folder.

    Args:
        git_folder: Path to folder containing .git

    Returns:
        Remote URL or None if not found
    """
    try:
        output = subprocess.check_output(
            ["git", "-C", git_folder, "remote", "get-url", "origin"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        # Clean control characters
        output = re.sub(r"[\x00-\x1F\x7F]", "", output)
        return output.strip()
    except subprocess.CalledProcessError:
        return None


# ======================================================================================
# Transformation Graph
# ======================================================================================

project_kinds = TransformationGraph()

# Define kinds with predicates

project_kinds.add_node(
    'proj_name',
    isa=lambda x: isinstance(x, str)
    and '/' not in x
    and not x.startswith('http')
    and not x.startswith('git@')
    and not os.path.sep in x,
)

project_kinds.add_node(
    'github_stub',
    isa=lambda x: isinstance(x, str)
    and x.count('/') == 1
    and not x.startswith('http')
    and not x.startswith('git@'),
)

project_kinds.add_node(
    'github_https_url',
    isa=lambda x: isinstance(x, str) and x.startswith('https://github.com/'),
)

project_kinds.add_node(
    'github_ssh_url',
    isa=lambda x: isinstance(x, str) and x.startswith('git@github.com:'),
)

project_kinds.add_node(
    'local_git_folder',
    isa=lambda x: isinstance(x, (str, Path))
    and os.path.isdir(str(x))
    and os.path.exists(os.path.join(str(x), '.git')),
)

# Alias for local_git_folder
project_kinds.add_node(
    'local_proj_folder',
    isa=lambda x: isinstance(x, (str, Path))
    and os.path.isdir(str(x))
    and os.path.exists(os.path.join(str(x), '.git')),
)

project_kinds.add_node(
    'url_components',
    isa=lambda x: isinstance(x, dict) and 'username' in x and 'repository' in x,
)

# Add transformation edges


@project_kinds.register_edge('proj_name', 'local_proj_folder')
def proj_name_to_local_folder(name: str, ctx) -> str:
    """Find local project folder by searching registered roots."""
    folder = _find_project_by_name(name)
    if folder is None:
        roots = get_project_roots()
        raise ValueError(
            f"Project '{name}' not found in registered roots. "
            f"Searched: {roots}\n"
            f"Use register_project_root() to add project folders."
        )
    return folder


@project_kinds.register_edge('local_proj_folder', 'proj_name')
def local_folder_to_proj_name(folder: str, ctx) -> str:
    """Extract project name from folder path."""
    return Path(folder).name


@project_kinds.register_edge('local_proj_folder', 'github_stub')
def local_folder_to_stub(folder: str, ctx) -> str:
    """Get org/repo stub from git remote URL."""
    remote_url = _get_git_remote_url(folder)
    if not remote_url:
        raise ValueError(f"No git remote URL found for {folder}")

    # Parse the remote URL to extract org/repo
    if 'github.com' not in remote_url:
        raise ValueError(f"Remote URL is not a GitHub URL: {remote_url}")

    try:
        components = parse_github_url(remote_url)
        return f"{components['username']}/{components['repository']}"
    except:
        # Fallback parsing for SSH URLs like git@github.com:org/repo.git
        match = re.search(r'github\.com[:/]([^/]+)/([^/\.]+)', remote_url)
        if match:
            return f"{match.group(1)}/{match.group(2)}"
        raise ValueError(f"Could not parse GitHub URL: {remote_url}")


@project_kinds.register_edge('github_stub', 'local_proj_folder')
def stub_to_local_folder(stub: str, ctx) -> str:
    """Try to find local folder by searching for repo name."""
    _, repo_name = stub.split('/', 1)
    folder = _find_project_by_name(repo_name)
    if folder is None:
        raise ValueError(
            f"Local folder for '{stub}' not found. "
            f"Searched registered project roots."
        )
    return folder


@project_kinds.register_edge('github_stub', 'url_components')
def stub_to_components(stub: str, ctx) -> dict:
    """Convert org/repo stub to URL components."""
    org, repo = stub.split('/', 1)
    return {'username': org, 'repository': repo}


@project_kinds.register_edge('github_https_url', 'url_components')
def https_url_to_components(url: str, ctx) -> dict:
    """Parse HTTPS GitHub URL to components."""
    return parse_github_url(url)


@project_kinds.register_edge('github_ssh_url', 'url_components')
def ssh_url_to_components(url: str, ctx) -> dict:
    """Parse SSH GitHub URL to components."""
    return parse_github_url(url)


@project_kinds.register_edge('url_components', 'github_stub')
def components_to_stub(components: dict, ctx) -> str:
    """Extract org/repo stub from URL components."""
    return f"{components['username']}/{components['repository']}"


@project_kinds.register_edge('url_components', 'github_https_url')
def components_to_https_url(components: dict, ctx) -> str:
    """Generate HTTPS GitHub URL from components."""
    base_components = {
        'username': components['username'],
        'repository': components['repository'],
    }
    return generate_github_url(base_components, 'repository')


@project_kinds.register_edge('url_components', 'github_ssh_url')
def components_to_ssh_url(components: dict, ctx) -> str:
    """Generate SSH GitHub URL from components."""
    base_components = {
        'username': components['username'],
        'repository': components['repository'],
    }
    return generate_github_url(base_components, 'clone_url')


# Add identity edge for local_proj_folder <-> local_git_folder
@project_kinds.register_edge('local_proj_folder', 'local_git_folder', cost=0.0)
def proj_folder_to_git_folder(folder: str, ctx) -> str:
    """Identity: local_proj_folder and local_git_folder are the same."""
    return folder


@project_kinds.register_edge('local_git_folder', 'local_proj_folder', cost=0.0)
def git_folder_to_proj_folder(folder: str, ctx) -> str:
    """Identity: local_git_folder and local_proj_folder are the same."""
    return folder


# ======================================================================================
# Public API
# ======================================================================================


def normalize_project(
    project: str | Path,
    *,
    to_kind: Literal[
        'local_proj_folder',
        'local_git_folder',
        'github_stub',
        'proj_name',
        'github_https_url',
        'github_ssh_url',
        'url_components',
    ] = 'local_proj_folder',
) -> str | Path | dict:
    """
    Normalize any project reference to the desired kind.

    This allows flexible input handling - pass a project name, stub, URL, or path
    and get it converted to whatever format you need.

    Args:
        project: Any valid project reference
        to_kind: Target kind to convert to

    Returns:
        The project reference in the desired format

    Raises:
        ValueError: If the project cannot be found or converted

    Examples:
        >>> # From simple name to path
        >>> normalize_project("dol")  # doctest: +SKIP
        '/Users/thorwhalen/Dropbox/py/proj/i/dol'

        >>> # From URL to stub
        >>> normalize_project(
        ...     "https://github.com/i2mint/dol/tree/master",
        ...     to_kind='github_stub'
        ... )  # doctest: +SKIP
        'i2mint/dol'

        >>> # From SSH URL to HTTPS URL
        >>> normalize_project(
        ...     "git@github.com:i2mint/dol.git",
        ...     to_kind='github_https_url'
        ... )  # doctest: +SKIP
        'https://github.com/i2mint/dol'
    """
    return project_kinds.transform_any(project, to_kind)


# Convenience functions for common conversions


def to_local_path(project: str | Path) -> str:
    """Convert any project reference to local folder path."""
    return normalize_project(project, to_kind='local_proj_folder')


def to_github_stub(project: str | Path) -> str:
    """Convert any project reference to org/repo stub."""
    return normalize_project(project, to_kind='github_stub')


def to_github_url(project: str | Path, *, ssh: bool = True) -> str:
    """Convert any project reference to GitHub URL.

    Args:
        project: Any project reference
        ssh: If True, return SSH URL; if False, return HTTPS URL
    """
    kind = 'github_ssh_url' if ssh else 'github_https_url'
    return normalize_project(project, to_kind=kind)
