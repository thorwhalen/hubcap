"""Tools to slurp a repo's information """

# -------------------------------------------------------------------------------------
# git utils


from warnings import warn
import os
import subprocess


# standard_lib_dir = os.path.dirname(os.__file__)
path_sep = os.path.sep


def ensure_slash_suffix(s: str):
    if not s.endswith(path_sep):
        s += path_sep
    return s


def ensure_no_slash_suffix(s: str):
    return s.rstrip(path_sep)


def _build_git_command(command: str = 'status', work_tree='.', git_dir=None):
    if command.startswith('git '):
        warn(
            "You don't need to start your command with 'git '. I know it's a git command. Removing that prefix"
        )
        command = command[len('git ') :]
    work_tree = os.path.abspath(os.path.expanduser(work_tree))
    if git_dir is None:
        git_dir = os.path.join(work_tree, '.git')
    assert os.path.isdir(git_dir), f"Didn't find the git_dir: {git_dir}"
    git_dir = ensure_no_slash_suffix(git_dir)
    if not git_dir.endswith('.git'):
        warn(f"git_dir doesn't end with `.git`: {git_dir}")
    return f'git --git-dir="{git_dir}" --work-tree="{work_tree}" {command}'


def git(command: str = 'status', work_tree='.', git_dir=None):
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


# -------------------------------------------------------------------------------------
# markdown utils

from typing import Callable, KT, VT, Iterable


def _dflt_format_func(k, v):
    return f"## {k}\\n\\n{v}\\n\\n"


def _markdown_lines_from_mapping(
    store, format_func: Callable[[KT, VT], str] = _dflt_format_func
) -> Iterable[str]:
    """
    Generates markdown lines from a given store (mapping) using a formatting function.

    Args:
        store (dict): A mapping with string keys and values.
        format_func (callable): A function that takes a key and value and returns a formatted string.

    Yields:
        str: A markdown formatted line.
    """
    for key, value in store.items():
        yield format_func(key, value)


def markdown_from_mapping(store, format_func):
    """
    Creates a markdown string from a given store (mapping) with string keys and values using a formatting function.

    Args:
        store (dict): A mapping with string keys and values.
        format_func (callable): A function that takes a key and value and returns a formatted string.

    Returns:
        str: A markdown formatted string representing the store.

    Example:
    >>> example_store = {
    ...     "apple.txt": "Crumble",
    ...     "tit.md": "For tat.",
    ...     "state.cfg": "Of the art."
    ... }
    >>> example_format_func = lambda k, v: f"## {k}\\n```\\n{v}\\n```"
    >>> print(markdown_from_mapping(example_store, example_format_func))
    ## apple.txt
    ```
    Crumble
    ```
    ## tit.md
    ```
    For tat.
    ```
    ## state.cfg
    ```
    Of the art.
    ```
    """
    return "\n".join(_markdown_lines_from_mapping(store, format_func))


# -------------------------------------------------------------------------------------
# github_repo_text_aggregate

from dol import Files, wrap_kvs
import tempfile


def data_of_obj(obj, print_errors=False):
    try:
        return obj.decode('utf-8')
    except UnicodeDecodeError:
        if print_errors:
            print(f"Error decoding {obj}")
        return ""


def github_repo_text_aggregate(owner_repo, target_folder=None):
    """
    Clone a git repository and aggregate all file contents into a markdown string.

    Args:
        owner_repo (str): The GitHub repository in the format 'owner/repo'.
        target_folder (str, optional): The target folder to clone the repository into. Defaults to a temporary folder.

    Returns:
        str: A markdown formatted string with all file contents.


    >>> owner_repo_files = github_repo_text_aggregate('thorwhalen/hubcap')  # doctest: +SKIP
    >>> markdown_output = github_repo_text_aggregate(owner_repo_files)  # doctest: +SKIP

    """
    if target_folder is None:
        target_folder = tempfile.mkdtemp()

    # Construct the git clone command
    clone_command = f"git clone https://github.com/{owner_repo}.git {target_folder}"
    subprocess.check_call(clone_command, shell=True)

    # Create a store for the files in the target folder
    store = Files(target_folder)
    store = wrap_kvs(store, obj_of_data=data_of_obj)

    # Define the format function for markdown
    def format_func(key, value):
        return f"## {key}\n```\n{value}\n```"

    # Create the markdown string from the store
    markdown_output = markdown_from_mapping(store, format_func)
    return markdown_output
