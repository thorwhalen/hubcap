"""Tools to slurp a repo's information """

# TODO: This module is a bit of a mess. It should be cleaned up and reorganized.
#  It should also be tested.
#  There's some light caching functionality for files and wiki
#  (via explicitly giving a folder as the repo) but it is not consistent.
#  Better use graze, or something like it, for cachine.
#  What we'd want is to be able to just speak the language of urls, and let the module
#  take care of caching what it clones (or in the case of discussions, downloads)

import os
from typing import Mapping, Union, Literal
from hubcap.util import (
    ensure_github_url,
    git_clone,
    git_wiki_clone,
)
from hubcap.base import RepoReader, ResourceNotFound, NotSet


# -------------------------------------------------------------------------------------
# markdown utils

from typing import Callable, KT, VT, Iterable

KvToText = Callable[[KT, VT], str]


def kv_to_python_aware_markdown(k, v):
    """Puts .py content in a code block, and returns a markdown formatted string."""
    if k.endswith('.py'):
        # if it's a python file, we'll put it in a code block
        v = f'```python\n{v}\n```\n'
    return f'## {k}\\n\\n{v}\\n\\n'


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
    return '\n'.join(_text_segments_from_mapping(mapping, kv_to_text))


def add_offset_to_headers(markdown_text: str, offset: int = 0) -> str:
    r"""
    Returns the same text but where the (markdown) headers have been offset by `offset`.

    It works by adding `offset` number of '#' to the start of each header line.

    If the offset causes a header level to become zero or negative, it is ignored (remains the same).

    Comments (lines starting with '#') in code blocks are not affected by the offset.

    >>> add_offset_to_headers("## Header 1\n\n### Header 2\n\n#### Header 3", 1)
    '### Header 1\n\n#### Header 2\n\n##### Header 3'
    >>> add_offset_to_headers("## Header 1\n\n### Header 2\n\n#### Header 3", -1)
    '# Header 1\n\n## Header 2\n\n### Header 3'

    Note that comments in code blocks are not affected:

    >>> add_offset_to_headers("```\n# Not a header\n```", 1)
    '```\n# Not a header\n```'

    >>> add_offset_to_headers("## Header 1\n\n```\n# Not a header\n```\n\n### Header 2", 1)
    '### Header 1\n\n```\n# Not a header\n```\n\n#### Header 2'
    """

    def offset_header_line(line: str):
        if line.startswith('#'):
            header_level = line.count('#', 0, line.find(' '))
            new_level = header_level + offset
            if new_level > 0:
                return '#' * new_level + line[header_level:]
            else:
                return line
        return line

    in_code_block = False

    def _result_lines():
        nonlocal in_code_block
        for line in markdown_text.split('\n'):
            if line.startswith('```'):
                in_code_block = not in_code_block
                yield line
            elif in_code_block:
                yield line
            else:
                yield offset_header_line(line)

    return '\n'.join(_result_lines())


def _ensure_callable_processor(processor, if_true=lambda x: x, if_false=lambda x: None):
    """
    Ensures that the given processor is a callable. If the processor is a boolean,
    it returns a default callable based on the boolean value.

    Args:
        processor (bool or callable): The processor to ensure is callable.
        if_true (callable): The callable to use if the processor is True.
        if_false (callable): The callable to use if the processor is False.

    Returns:
        callable: The ensured callable processor.

    Raises:
        ValueError: If the processor is neither a boolean nor a callable.

    Examples:
        >>> _ensure_callable_processor(True)("test")
        'test'

        >>> _ensure_callable_processor(False)("test")

        >>> _ensure_callable_processor(lambda x: x.upper())("test")
        'TEST'

        >>> _ensure_callable_processor("not callable")
        Traceback (most recent call last):
            ...
        ValueError: not callable is not a callable
    """
    if processor is True:
        return if_true
    elif processor is False:
        return if_false
    elif callable(processor):
        return processor
    else:
        raise ValueError(f'{processor} is not a callable')


def _markdown_lines(notebook, process_code, process_markdown, process_output):
    """Helper function to yield markdown lines from a notebook."""
    process_code = _ensure_callable_processor(process_code)
    process_markdown = _ensure_callable_processor(process_markdown)
    process_output = _ensure_callable_processor(process_output)

    for cell in notebook.cells:
        if cell.cell_type == 'markdown':
            processed = process_markdown(cell.source)
            if processed is not None:
                yield processed
        elif cell.cell_type == 'code':
            processed_code = process_code(cell.source)
            if processed_code is not None:
                yield f'```python\n{processed_code}\n```'
            for output in cell.get('outputs', []):
                if output.output_type == 'stream':
                    text = output.text
                elif output.output_type == 'error':
                    text = ''.join(output.traceback)
                elif output.output_type == 'execute_result':
                    text = output.data.get('text/plain', '')
                else:
                    continue
                processed_output = process_output(text)
                if processed_output is not None:
                    yield f'```\n{processed_output}\n```'


# TODO: Move to markdown utils module or package
# TODO: Write a few useful process_* functions to get useful markdown from code and output cells
#   For example, not including traceback in error outputs, or only including the last line of
#   output cells -- or not including scrap sections of code cells.
def notebook_to_markdown(
    notebook: Union[str, bytes],
    *,
    process_code=True,
    process_markdown=True,
    process_output=True,
    encoding='utf-8',
):
    """
    Transforms a Jupyter notebook into a markdown string with control over cell processing.

    Args:
        notebook: Path to (or bytes or str contents of) the Jupyter notebook.
        process_code (bool or callable): Whether to include code cells or a callable to process them.
                                         Default is True.
        process_markdown (bool or callable): Whether to include markdown cells or a callable to process them.
                                             Default is True.
        process_output (bool or callable): Whether to include the output of code cells or a callable to process them.
                                           Default is True.

    Returns:
        str: The notebook content as a markdown string.
    """
    import nbformat
    import io

    # Make a notebook object
    if os.path.isfile(notebook):
        with open(notebook, 'r', encoding=encoding) as f:
            notebook = nbformat.read(f, as_version=4)
    if isinstance(notebook, (bytes, str)):
        if isinstance(notebook, str):
            notebook = io.StringIO(notebook)
        elif isinstance(notebook, bytes):
            notebook = io.BytesIO(notebook)
        else:
            raise ValueError(f'Unsupported type for notebook: {type(notebook)}')
        notebook = nbformat.read(notebook, as_version=4)
    else:
        assert isinstance(notebook, nbformat.NotebookNode)

    return '\n\n'.join(
        filter(
            None,
            _markdown_lines(notebook, process_code, process_markdown, process_output),
        )
    )


# -------------------------------------------------------------------------------------
# github_repo_text_aggregate

import tempfile
import re
from functools import partial
from subprocess import CalledProcessError
from dol import TextFiles, wrap_kvs, filt_iter, Files


def _is_local_git_repo(repo: str):
    return os.path.isdir(repo) and os.path.isdir(os.path.join(repo, '.git'))


def ensure_repo_folder(repo: str, clone_func=git_clone):
    """Returns a local repo folder.
    Either the input repo is already a local "git" folder (which we return as is),
    or a temporary folder to clone the repo into is returned.
    """
    if os.path.isdir(repo):
        return repo
    elif ensure_github_url(repo):
        try:
            local_folder = tempfile.mkdtemp()
            clone_func(repo, local_folder)
            return local_folder
        except CalledProcessError:
            raise ResourceNotFound(
                f"Couldn't find a (or error cloning with {clone_func}) a resource at {repo}"
            )
    else:
        raise ResourceNotFound(f"Couldn't find a local git repo at {repo}")


def _decode_to_text_or_skip(obj, log_error_function=False):
    try:
        return obj.decode('utf-8')
    except UnicodeDecodeError:
        if log_error_function:
            # if log_error_function
            print(f'Error decoding {obj}')
        return None  # Note: None values will be skipped in text_from_mapping


def all_decodable_text_folder_to_mapping(folder):
    """A folder_to_mapping function that takes"""
    return wrap_kvs(Files(folder), obj_of_data=_decode_to_text_or_skip)


def key_filtered_text_files(folder, key_pattern):
    return filt_iter(TextFiles(folder), filt=re.compile(key_pattern).search)


_pattern_for_python_and_markdown_files = r'.*\.(py|md)$'

_filtered_py_and_md_files = partial(
    key_filtered_text_files, key_pattern=_pattern_for_python_and_markdown_files
)


def _does_not_start_with_docsrc_or_setup(key: KT):
    return not key.startswith('docsrc/') and not key.startswith('setup.')


# TODO: A lot more can be done to parametrize the construction of a discussion text
#   if and when more format flexibility is needed (for example, to enable parsing
#  (text-back-to-json) or a nicer text rendering of the discussion)
#  For formatting, may want to detect headers in content and modify according to
#  header_level.
def __discussion_json_to_text_segments(
    d: dict, header_level=2, offset_headers=True
) -> Iterable[str]:
    if offset_headers:
        if offset_headers is True:
            offset = header_level
        elif isinstance(offset_headers, int):
            offset = offset_headers
        else:
            raise ValueError(
                f'offset_headers must be an int or True, not {offset_headers}'
            )
        _offset_headers = partial(add_offset_to_headers, offset=offset)
    else:
        _offset_headers = lambda x: x

    yield _offset_headers(d['body']) + '\n\n'
    for comment_num, comment in enumerate(d['comments'], 1):
        yield '#' * (header_level + 1) + f' Comment {comment_num}\n\n'
        yield _offset_headers(comment['body']) + '\n\n'
        for reply in comment.get('replies', []):
            yield '#' * (header_level + 2) + f' Reply\n\n'
            yield _offset_headers(reply['body'] + '\n\n')


def _discussion_json_to_text(d: dict, header_level=2):
    return ''.join(__discussion_json_to_text_segments(d, header_level))


def discussions_mapping(repo, discussion_json_to_text=_discussion_json_to_text):
    repo_url = ensure_github_url(repo)
    discussions = RepoReader(repo_url)['discussions']

    def _gen():
        for key, d in discussions.items():
            yield f"Discussion {key}: {d['title']}", discussion_json_to_text(d)

    return dict(_gen())


def wiki_mapping(repo, local_repo_folder=None, default=NotSet, suppress_errors=True):
    try:
        local_repo_folder = ensure_repo_folder(
            repo, clone_func=partial(git_wiki_clone, suppress_errors=suppress_errors)
        )
        s = filt_iter(TextFiles(local_repo_folder), filt=re.compile(r'.*\.md$').search)
        return s
    except ResourceNotFound:
        if default is NotSet:
            raise
        return default


def repo_files_mapping(
    repo: str,
    *,
    kv_to_text: KvToText = kv_to_python_aware_markdown,
    folder_to_mapping: Union[Callable[[str], Mapping], str] = _filtered_py_and_md_files,
    extra_key_filter=_does_not_start_with_docsrc_or_setup,
):
    local_repo_folder = ensure_repo_folder(repo)

    # If the folder_to_mapping is a string, use the key_filtered_text_files function
    # with the string as the key pattern
    if isinstance(folder_to_mapping, str):
        key_filter_pattern = folder_to_mapping
        folder_to_mapping = partial(
            key_filtered_text_files, key_pattern=key_filter_pattern
        )

    # Create a mapping for the files in the target folder
    mapping = folder_to_mapping(local_repo_folder)

    if extra_key_filter:
        if isinstance(extra_key_filter, str):
            extra_key_filter = re.compile(extra_key_filter).search
        mapping = filt_iter(mapping, filt=extra_key_filter)

    mapping = wrap_kvs(mapping, postget=kv_to_text)

    return mapping


CloneKinds = Literal['files', 'wiki', 'discussions']


def github_repo_mapping(
    repo: str, *, kind: CloneKinds = 'files', repo_files_mapping=repo_files_mapping,
):
    r"""
    Clone a git repository and make a mapping of the files in the repository.

    Args:
        repo (str): The GitHub repository in the format 'owner/repo' or github url.
        clone_to_folder (str, optional): The target folder to clone the repository into. Defaults to a temporary folder.

    Returns:
        Mapping: A mapping of the files in the repository.


    >>> repo_files = github_repo_mapping('thorwhalen/hubcap')  # doctest: +SKIP

    """
    # repo = ensure_github_url(repo)

    # subprocess.check_call(clone_command, shell=True)
    if kind == 'discussions':
        return discussions_mapping(repo)
    elif kind == 'wiki':
        return wiki_mapping(repo, default={})
    elif kind == 'files':
        return repo_files_mapping(repo)
    else:
        raise ValueError(f"kind must be 'files' or 'wiki', not {kind}")


def repo_text_aggregate(
    repo,
    kinds: Union[CloneKinds, Iterable[CloneKinds]] = ('files', 'wiki', 'discussions'),
    *,
    github_repo_mapping=github_repo_mapping,
    text_from_mapping=text_from_mapping,
):
    """
    Clone a git repository and aggregate all file contents into a string.

    Args:
        repo (str): The GitHub repository in the format 'owner/repo' or github url.
        kinds (Union[CloneKinds, Iterable[CloneKinds]], optional):
            The kinds of content to aggregate. Defaults to ('files', 'wiki', 'discussions').

    Returns:
        str: A string with all file contents.


    >>> aggregate = repo_text_aggregate('thorwhalen/hubcap')  # doctest: +SKIP
    >>> print(aggregate[:100])  # doctest: +SKIP
    ## README.md\n\n# hubcap
    A [dol](https://github.com/i2mint/dol) (i.e. dict-like) interface to github...

    """
    text = ''
    for kind in kinds:
        mapping = github_repo_mapping(repo, kind=kind)
        text += text_from_mapping(mapping)
    return text
