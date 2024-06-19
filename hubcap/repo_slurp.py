"""Tools to slurp a repo's information """

from typing import Mapping, Union, Literal
from hubcap.util import (
    ensure_github_url,
    git_clone,
    git_wiki_clone,
)

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


CloneKinds = Literal['files', 'wiki']

def github_repo_mapping(
    repo: str,
    clone_to_folder=None,
    *,
    folder_to_mapping: Union[Callable[[str], Mapping], str] = _filtered_py_and_md_files,
    extra_key_filter=None,
    kind: CloneKinds = 'files',
):
    r"""
    Clone a git repository and make a mapping of the files in the repository.

    Args:
        repo (str): The GitHub repository in the format 'owner/repo' or github url.
        clone_to_folder (str, optional): The target folder to clone the repository into. Defaults to a temporary folder.

    Returns:
        Mapping: A mapping of the files in the repository.


    >>> repo_files = github_repo_text_aggregate('thorwhalen/hubcap')  # doctest: +ELLIPSIS
    >>> print(repo_files[:100])  # doctest: +ELLIPSIS
    ## README.md\n\n# hubcap
    A [dol](https://github.com/i2mint/dol) (i.e. dict-like) interface to github...

    """
    # If no clone_to_folder is provided, create a temporary folder
    if clone_to_folder is None:
        clone_to_folder = tempfile.mkdtemp()

    repo = ensure_github_url(repo)

    # Construct the git clone command
    # TODO: Use the git function?
    # clone_command = f"git clone {repo} {clone_to_folder}"
    # import subprocess

    # subprocess.check_call(clone_command, shell=True)
    if kind == 'files':
        git_clone(repo, clone_to_folder)
    elif kind == 'wiki':
        git_wiki_clone(repo, clone_to_folder)
    else:
        raise ValueError(f"kind must be 'files' or 'wiki', not {kind}")

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


# def github_wiki_mapping(
#     repo,
#     clone_to_folder=None,
#     *,
#     folder_to_mapping: Union[Callable[[str], Mapping], str] = _filtered_py_and_md_files,
#     extra_key_filter=None,
# ):
#     r"""
#     Clone a git repository's wiki and make a mapping of the files in the repository.

#     Args:
#         repo (str): The GitHub repository in the format 'owner/repo'.
#         clone_to_folder (str, optional): The target folder to clone the repository into. Defaults to a temporary folder.

#     Returns:
#         Mapping: A mapping of the files in the repository.


#     """
#     # If no clone_to_folder is provided, create a temporary folder
#     if clone_to_folder is None:
#         clone_to_folder = tempfile.mkdtemp()

#     # Construct the git clone command

#     clone_command = f"git clone"
#     "git clone https://github.com/alice/my-project.wiki.git"


def github_repo_text_aggregate(
    repo,
    clone_to_folder=None,
    *,
    folder_to_mapping: Union[Callable[[str], Mapping], str] = _filtered_py_and_md_files,
    extra_key_filter=_does_not_start_with_docsrc_or_setup,
    kv_to_text: KvToText = kv_to_python_aware_markdown,
):
    """
    Clone a git repository and aggregate all file contents into a string.

    Args:
        repo (str): The GitHub repository in the format 'owner/repo' or github url.
        clone_to_folder (str, optional): The target folder to clone the repository into. Defaults to a temporary folder.

    Returns:
        str: A string with all file contents.


    >>> aggregate = github_repo_text_aggregate('thorwhalen/hubcap')  # doctest: +SKIP

    """
    # Create the mapping from the repository
    mapping = github_repo_mapping(
        repo,
        clone_to_folder=clone_to_folder,
        folder_to_mapping=folder_to_mapping,
        extra_key_filter=extra_key_filter,
    )
    # Create the markdown string from the mapping
    markdown_output = text_from_mapping(mapping, kv_to_text)
    return markdown_output
