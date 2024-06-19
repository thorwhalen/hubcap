"""Tools to slurp a repo's information """

from typing import Mapping, Union

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

KvToText = Callable[[KT, VT], str]


def kv_to_python_aware_markdown(k, v):
    """Puts .py content in a code block, and returns a markdown formatted string."""
    if k.endswith('.py'):
        # if it's a python file, we'll put it in a code block
        v = f"```python\n{v}\n```\n"
    return f"## {k}\\n\\n{v}\\n\\n"


def _text_segments_from_mapping(
    store, kv_to_text: KvToText = kv_to_python_aware_markdown
) -> Iterable[str]:
    """
    Generates text segments from a given store (mapping) using a formatting function.

    Args:
        store (dict): A mapping with string keys and values.
        kv_to_text (callable): A function that takes a key and value and returns a formatted string.

    Yields:
        str: Text for each kv item
    """
    for key, value in store.items():
        if value is not None:  # None values are skipped (can use None as sentinel)
            yield kv_to_text(key, value)


def text_from_mapping(
    mapping: Mapping, kv_to_text: KvToText = kv_to_python_aware_markdown
):
    """
    Creates a string from a given mapping with string keys and values using a formatting function.

    Args:
        mapping (dict): A mapping with string keys and values.
        kv_to_text (callable): Function that takes a key and value and returns a string.

    Returns:
        str: A string aggregate of the values of the mapping.

    Example:
    >>> example_mapping = {
    ...     "apple.txt": "Crumble",
    ...     "tit.md": "For tat.",
    ...     "state.cfg": "Of the art."
    ... }
    >>> example_kv_to_text = lambda k, v: f"## {k}\\n```\\n{v}\\n```"
    >>> print(text_from_mapping(example_mapping, example_kv_to_text))
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
    return "\n".join(_text_segments_from_mapping(mapping, kv_to_text))


# -------------------------------------------------------------------------------------
# github_repo_text_aggregate

import tempfile
import re
from functools import partial
from dol import TextFiles, wrap_kvs, filt_iter, Files


def _decode_to_text_or_skip(obj, log_error_function=False):
    try:
        return obj.decode('utf-8')
    except UnicodeDecodeError:
        if log_error_function:
            # if log_error_function
            print(f"Error decoding {obj}")
        return None  # Note: None values will be skipped in text_from_mapping


def all_decodable_text_folder_to_mapping(folder):
    """A folder_to_mapping function that takes"""
    return wrap_kvs(Files(folder), obj_of_data=_decode_to_text_or_skip)


def key_filtered_text_files(folder, key_pattern):
    return filt_iter(TextFiles(folder), filt=re.compile(key_pattern).search)


_pattern_for_python_and_markdown_files = r".*\.(py|md)$"

_filtered_py_and_md_files = partial(
    key_filtered_text_files, key_pattern=_pattern_for_python_and_markdown_files
)


def _does_not_start_with_docsrc_or_setup(key: KT):
    return not key.startswith('docsrc/') and not key.startswith('setup.')


def github_repo_mapping(
    owner_repo,
    clone_to_folder=None,
    *,
    folder_to_mapping: Union[Callable[[str], Mapping], str] = _filtered_py_and_md_files,
    extra_key_filter=None,
):
    """
    Clone a git repository and make a mapping of the files in the repository.

    Args:
        owner_repo (str): The GitHub repository in the format 'owner/repo'.
        clone_to_folder (str, optional): The target folder to clone the repository into. Defaults to a temporary folder.

    Returns:
        Mapping: A mapping of the files in the repository.


    >>> owner_repo_files = github_repo_text_aggregate('thorwhalen/hubcap')  # doctest: +SKIP

    """
    # If no clone_to_folder is provided, create a temporary folder
    if clone_to_folder is None:
        clone_to_folder = tempfile.mkdtemp()

    # Construct the git clone command
    # TODO: Use the git function?
    clone_command = f"git clone https://github.com/{owner_repo}.git {clone_to_folder}"
    subprocess.check_call(clone_command, shell=True)

    # If the folder_to_mapping is a string, use the key_filtered_text_files function
    # with the string as the key pattern
    if isinstance(folder_to_mapping, str):
        key_filter_pattern = folder_to_mapping
        folder_to_mapping = partial(
            key_filtered_text_files, key_pattern=key_filter_pattern
        )

    # Create a mapping for the files in the target folder
    mapping = folder_to_mapping(clone_to_folder)

    if extra_key_filter:
        if isinstance(extra_key_filter, str):
            extra_key_filter = re.compile(extra_key_filter).search
        mapping = filt_iter(mapping, filt=extra_key_filter)

    return mapping


def github_repo_text_aggregate(
    owner_repo,
    clone_to_folder=None,
    *,
    folder_to_mapping: Union[Callable[[str], Mapping], str] = _filtered_py_and_md_files,
    extra_key_filter=_does_not_start_with_docsrc_or_setup,
    kv_to_text: KvToText = kv_to_python_aware_markdown,
):
    """
    Clone a git repository and aggregate all file contents into a string.

    Args:
        owner_repo (str): The GitHub repository in the format 'owner/repo'.
        clone_to_folder (str, optional): The target folder to clone the repository into. Defaults to a temporary folder.

    Returns:
        str: A string with all file contents.


    >>> aggregate = github_repo_text_aggregate('thorwhalen/hubcap')  # doctest: +SKIP

    """
    # Create the mapping from the repository
    mapping = github_repo_mapping(
        owner_repo,
        clone_to_folder=clone_to_folder,
        folder_to_mapping=folder_to_mapping,
        extra_key_filter=extra_key_filter,
    )
    # Create the markdown string from the mapping
    markdown_output = text_from_mapping(mapping, kv_to_text)
    return markdown_output
