# hubcap.repo_slurp

Tools to slurp a repo’s information

### Functions

| [`add_offset_to_headers`](#hubcap.repo_slurp.add_offset_to_headers)(markdown_text[, offset])   | Returns the same text but where the (markdown) headers have been offset by `offset`.           |
|---------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| [`all_decodable_text_folder_to_mapping`](#hubcap.repo_slurp.all_decodable_text_folder_to_mapping)(folder)     | A folder_to_mapping function that takes                                                        |
| `discussions_mapping`(repo[, ...])                                                                |                                                                                                |
| [`ensure_repo_folder`](#hubcap.repo_slurp.ensure_repo_folder)(repo[, clone_func, ...])      | Returns a local repo folder.                                                                   |
| [`github_repo_mapping`](#hubcap.repo_slurp.github_repo_mapping)(repo, \*[, kind, ...])       | Clone a git repository and make a mapping of the files in the repository.                      |
| `key_filtered_text_files`(folder, key_pattern)                                                    |                                                                                                |
| [`kv_to_python_aware_markdown`](#hubcap.repo_slurp.kv_to_python_aware_markdown)(k, v)                | Puts .py content in a code block, and returns a markdown formatted string.                     |
| [`notebook_to_markdown`](#hubcap.repo_slurp.notebook_to_markdown)(notebook, \*[, ...])        | Transforms a Jupyter notebook into a markdown string with control over cell processing.        |
| `repo_files_mapping`(repo, \*[, kv_to_text, ...])                                                 |                                                                                                |
| [`repo_text_aggregate`](#hubcap.repo_slurp.repo_text_aggregate)(repo[, kinds, ...])          | Clone a git repository and aggregate all file contents into a string.                          |
| [`text_from_mapping`](#hubcap.repo_slurp.text_from_mapping)(mapping[, kv_to_text])         | Creates a string from a given mapping with string keys and values using a formatting function. |
| `wiki_mapping`(repo[, local_repo_folder, ...])                                                    |                                                                                                |

### hubcap.repo_slurp.add_offset_to_headers(markdown_text, offset=0)

Returns the same text but where the (markdown) headers have been offset by `offset`.

It works by adding `offset` number of ‘#’ to the start of each header line.

If the offset causes a header level to become zero or negative, it is ignored (remains the same).

Comments (lines starting with ‘#’) in code blocks are not affected by the offset.

```pycon
>>> add_offset_to_headers("## Header 1\n\n### Header 2\n\n#### Header 3", 1)
'### Header 1\n\n#### Header 2\n\n##### Header 3'
>>> add_offset_to_headers("## Header 1\n\n### Header 2\n\n#### Header 3", -1)
'# Header 1\n\n## Header 2\n\n### Header 3'
```

Note that comments in code blocks are not affected:

```pycon
>>> add_offset_to_headers("```\n# Not a header\n```", 1)
'```\n# Not a header\n```'
```

```pycon
>>> add_offset_to_headers("## Header 1\n\n```\n# Not a header\n```\n\n### Header 2", 1)
'### Header 1\n\n```\n# Not a header\n```\n\n#### Header 2'
```

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### hubcap.repo_slurp.all_decodable_text_folder_to_mapping(folder)

A folder_to_mapping function that takes

### hubcap.repo_slurp.ensure_repo_folder(repo, clone_func=<function git_clone>, local_folder=None)

Returns a local repo folder.
Either the input repo is already a local “git” folder (which we return as is),
or a temporary folder to clone the repo into is returned.

If the repo is a GitHub URL with a branch and/or path specification,
(e.g., [https://github.com/user/repo/tree/branch/path](https://github.com/user/repo/tree/branch/path)), the function will:

- Clone the specified branch
- Return the path to the subfolder if a path is specified

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### hubcap.repo_slurp.github_repo_mapping(repo, \*, kind='files', repo_files_mapping=<function repo_files_mapping>)

Clone a git repository and make a mapping of the files in the repository.

* **Parameters:**
  * **repo** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – The GitHub repository in the format ‘owner/repo’ or github url.
  * **clone_to_folder** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str) *,* *optional*) – The target folder to clone the repository into. Defaults to a temporary folder.
* **Returns:**
  A mapping of the files in the repository.
* **Return type:**
  *Mapping*

```pycon
>>> repo_files = github_repo_mapping('thorwhalen/hubcap')
```

### hubcap.repo_slurp.kv_to_python_aware_markdown(k, v)

Puts .py content in a code block, and returns a markdown formatted string.

### hubcap.repo_slurp.notebook_to_markdown(notebook, , process_code=True, process_markdown=True, process_output=True, encoding='utf-8')

Transforms a Jupyter notebook into a markdown string with control over cell processing.

* **Parameters:**
  * **notebook** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`bytes`](https://docs.python.org/3/builtins/stdtypes.html#bytes)) – Path to (or bytes or str contents of) the Jupyter notebook.
  * **process_code** ([*bool*](https://docs.python.org/3/builtins/functions.html#bool) *or* *callable*) – Whether to include code cells or a callable to process them.
    Default is True.
  * **process_markdown** ([*bool*](https://docs.python.org/3/builtins/functions.html#bool) *or* *callable*) – Whether to include markdown cells or a callable to process them.
    Default is True.
  * **process_output** ([*bool*](https://docs.python.org/3/builtins/functions.html#bool) *or* *callable*) – Whether to include the output of code cells or a callable to process them.
    Default is True.
* **Returns:**
  The notebook content as a markdown string.
* **Return type:**
  [*str*](https://docs.python.org/3/builtins/stdtypes.html#str)

### hubcap.repo_slurp.repo_text_aggregate(repo, kinds=('files', 'wiki', 'discussions'), \*, github_repo_mapping=<function github_repo_mapping>, text_from_mapping=<function text_from_mapping>)

> Clone a git repository and aggregate all file contents into a string.

> Args:
> : repo (str): The GitHub repository in the format ‘owner/repo’ or github url.
>   kinds (Union[CloneKinds, Iterable[CloneKinds]], optional):
>   <br/>
>   > The kinds of content to aggregate. Defaults to (‘files’, ‘wiki’, ‘discussions’).

> Returns:
> : str: A string with all file contents.

> ```pycon
> >>> aggregate = repo_text_aggregate('thorwhalen/hubcap')
> >>> print(aggregate[:100])
> ## README.md
> ```

# hubcap
: A [dol](https://github.com/i2mint/dol) (i.e. dict-like) interface to github…

### hubcap.repo_slurp.text_from_mapping(mapping, kv_to_text=<function kv_to_python_aware_markdown>)

Creates a string from a given mapping with string keys and values using a formatting function.

* **Parameters:**
  * **mapping** ([`Mapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping)) – A mapping with string keys and values.
  * **kv_to_text** ([`Callable`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Callable)[[`KT`, `VT`], [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Function that takes a key and value and returns a string.
* **Returns:**
  A string aggregate of the values of the mapping.
* **Return type:**
  [*str*](https://docs.python.org/3/builtins/stdtypes.html#str)

### Example

```pycon
>>> example_mapping = {
...     "apple.txt": "Crumble",
...     "tit.md": "For tat.",
...     "state.cfg": "Of the art."
... }
>>> example_kv_to_text = lambda k, v: f"## {k}\n```\n{v}\n```"
>>> print(text_from_mapping(example_mapping, example_kv_to_text))
## apple.txt
```

```text
Crumble
```

## tit.md

```text
For tat.
```

## state.cfg

```text
Of the art.
```
