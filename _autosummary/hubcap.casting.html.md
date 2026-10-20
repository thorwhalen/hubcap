# hubcap.casting

Transformation graph for GitHub project references with flexible input handling.

This module provides automatic conversion between different representations of GitHub
projects using i2.castgraph. It integrates with hubcap’s URL parsing/generation and
supports user-configurable local project folder discovery.

## Supported Kinds

- **proj_name**: Simple project name (e.g., “dol”)
- **github_stub**: Org/repo format (e.g., “i2mint/dol”)
- **github_https_url**: HTTPS URLs (e.g., “[https://github.com/i2mint/dol](https://github.com/i2mint/dol)”)
- **github_ssh_url**: SSH URLs (e.g., “[git@github.com](mailto:git@github.com):i2mint/dol.git”)
- **local_git_folder**: Local path with .git folder
- **local_proj_folder**: Alias for local_git_folder
- **url_components**: Parsed URL components dict

## Configuration

Register your local project root folders in the hubcap config:

```pycon
>>> from hubcap.casting import register_project_root, get_project_roots
>>> register_project_root('/Users/me/projects/personal')
>>> register_project_root('/Users/me/work')
>>> get_project_roots()
['/Users/me/projects/personal', '/Users/me/work']
```

The system will search one level deep in these roots for folders containing .git.

## Usage with Ingress Decorator

```pycon
>>> from hubcap.casting import project_kinds
>>>
>>> @project_kinds.ingress('local_proj_folder')
... def process_project(project_path: str):
...     '''Accepts any project reference, gets local path.'''
...     return f"Processing {project_path}"
>>>
>>> process_project("dol")
>>> process_project("i2mint/dol")
>>> process_project("https://github.com/i2mint/dol")
```

## Direct Transformation

```pycon
>>> from hubcap.casting import normalize_project
>>>
>>> # From name to local path
>>> normalize_project("dol", to_kind='local_proj_folder')
'/Users/thorwhalen/Dropbox/py/proj/i/dol'
>>>
>>> # From URL to stub
>>> normalize_project(
...     "https://github.com/i2mint/dol/tree/master",
...     to_kind='github_stub'
... )
'i2mint/dol'
```

### Module Attributes

| [`PROJECT_ROOTS_SEPARATOR`](#hubcap.casting.PROJECT_ROOTS_SEPARATOR)   | Separator used to serialize the registered project roots in the config store.                                                                           |
|----------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------|
| [`GIT_FOLDER_NAME`](#hubcap.casting.GIT_FOLDER_NAME)           | Marker that identifies a folder as a git project (a folder in worktrees, a file in submodules/worktree links -- hence the existence, not isdir, check). |

### Functions

| [`components_to_https_url`](#hubcap.casting.components_to_https_url)(components, ctx)   | Generate HTTPS GitHub URL from components.                     |
|---------------------------------------------------------------------------------------------|----------------------------------------------------------------|
| [`components_to_ssh_url`](#hubcap.casting.components_to_ssh_url)(components, ctx)     | Generate SSH GitHub URL from components.                       |
| [`components_to_stub`](#hubcap.casting.components_to_stub)(components, ctx)        | Extract org/repo stub from URL components.                     |
| [`get_project_roots`](#hubcap.casting.get_project_roots)()                        | Get the list of registered project root folders.               |
| [`git_folder_to_proj_folder`](#hubcap.casting.git_folder_to_proj_folder)(folder, ctx)     | Identity: local_git_folder and local_proj_folder are the same. |
| [`https_url_to_components`](#hubcap.casting.https_url_to_components)(url, ctx)          | Parse HTTPS GitHub URL to components.                          |
| [`local_folder_to_proj_name`](#hubcap.casting.local_folder_to_proj_name)(folder, ctx)     | Extract project name from folder path.                         |
| [`local_folder_to_stub`](#hubcap.casting.local_folder_to_stub)(folder, ctx)          | Get org/repo stub from git remote URL.                         |
| [`normalize_project`](#hubcap.casting.normalize_project)(project, \*[, to_kind])  | Normalize any project reference to the desired kind.           |
| [`proj_folder_to_git_folder`](#hubcap.casting.proj_folder_to_git_folder)(folder, ctx)     | Identity: local_proj_folder and local_git_folder are the same. |
| [`proj_name_to_local_folder`](#hubcap.casting.proj_name_to_local_folder)(name, ctx)       | Find local project folder by searching registered roots.       |
| [`register_project_root`](#hubcap.casting.register_project_root)(root_path)           | Register a new project root folder.                            |
| [`set_project_roots`](#hubcap.casting.set_project_roots)(roots)                   | Replace the registered project roots with `roots`.             |
| [`ssh_url_to_components`](#hubcap.casting.ssh_url_to_components)(url, ctx)            | Parse SSH GitHub URL to components.                            |
| [`stub_to_components`](#hubcap.casting.stub_to_components)(stub, ctx)              | Convert org/repo stub to URL components.                       |
| [`stub_to_local_folder`](#hubcap.casting.stub_to_local_folder)(stub, ctx)            | Try to find local folder by searching for repo name.           |
| [`to_github_stub`](#hubcap.casting.to_github_stub)(project)                    | Convert any project reference to org/repo stub.                |
| [`to_github_url`](#hubcap.casting.to_github_url)(project, \*[, ssh])          | Convert any project reference to GitHub URL.                   |
| [`to_local_path`](#hubcap.casting.to_local_path)(project)                     | Convert any project reference to local folder path.            |
| [`unregister_project_root`](#hubcap.casting.unregister_project_root)(root_path)         | Remove a project root folder from the registry.                |

### hubcap.casting.GIT_FOLDER_NAME *= '.git'*

Marker that identifies a folder as a git project (a folder in worktrees, a
file in submodules/worktree links – hence the existence, not isdir, check).

### hubcap.casting.PROJECT_ROOTS_SEPARATOR *= '\\n'*

Separator used to serialize the registered project roots in the config store.

### hubcap.casting.components_to_https_url(components, ctx)

Generate HTTPS GitHub URL from components.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### hubcap.casting.components_to_ssh_url(components, ctx)

Generate SSH GitHub URL from components.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### hubcap.casting.components_to_stub(components, ctx)

Extract org/repo stub from URL components.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### hubcap.casting.get_project_roots()

Get the list of registered project root folders.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]
* **Returns:**
  List of absolute paths to project root directories

### Example

```pycon
>>> roots = get_project_roots()
>>> print(roots)
['/Users/me/projects', '/Users/me/work']
```

### hubcap.casting.git_folder_to_proj_folder(folder, ctx)

Identity: local_git_folder and local_proj_folder are the same.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### hubcap.casting.https_url_to_components(url, ctx)

Parse HTTPS GitHub URL to components.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### hubcap.casting.local_folder_to_proj_name(folder, ctx)

Extract project name from folder path.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### hubcap.casting.local_folder_to_stub(folder, ctx)

Get org/repo stub from git remote URL.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### hubcap.casting.normalize_project(project, , to_kind='local_proj_folder')

Normalize any project reference to the desired kind.

This allows flexible input handling - pass a project name, stub, URL, or path
and get it converted to whatever format you need.

* **Parameters:**
  * **project** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)) – Any valid project reference
  * **to_kind** ([`Literal`](https://docs.python.org/3/library/typing.html#typing.Literal)[`'local_proj_folder'`, `'local_git_folder'`, `'github_stub'`, `'proj_name'`, `'github_https_url'`, `'github_ssh_url'`, `'url_components'`]) – Target kind to convert to
* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path) | [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)
* **Returns:**
  The project reference in the desired format
* **Raises:**
  [**ValueError**](https://docs.python.org/3/builtins/exceptions.html#ValueError) – If the project cannot be found or converted

### Examples

```pycon
>>> # From simple name to path
>>> normalize_project("dol")
'/Users/thorwhalen/Dropbox/py/proj/i/dol'
```

```pycon
>>> # From URL to stub
>>> normalize_project(
...     "https://github.com/i2mint/dol/tree/master",
...     to_kind='github_stub'
... )
'i2mint/dol'
```

```pycon
>>> # From SSH URL to HTTPS URL
>>> normalize_project(
...     "git@github.com:i2mint/dol.git",
...     to_kind='github_https_url'
... )
'https://github.com/i2mint/dol'
```

### hubcap.casting.proj_folder_to_git_folder(folder, ctx)

Identity: local_proj_folder and local_git_folder are the same.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### hubcap.casting.proj_name_to_local_folder(name, ctx)

Find local project folder by searching registered roots.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### hubcap.casting.register_project_root(root_path)

Register a new project root folder.

Projects (folders with .git) one level below this root will be discoverable
by project name.

* **Parameters:**
  **root_path** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Absolute path to a directory containing project folders
* **Raises:**
  [**ValueError**](https://docs.python.org/3/builtins/exceptions.html#ValueError) – If `root_path` is not an existing directory
* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

### Example

```pycon
>>> register_project_root('/Users/me/projects')
>>> register_project_root('/Users/me/work/repos')
```

### hubcap.casting.set_project_roots(roots)

Replace the registered project roots with `roots`.

This is the *single write path* for the registry: `register_project_root`
and `unregister_project_root` both go through it, so anything that must
happen when the registry changes (currently, dropping the stale project
lookup cache) has exactly one place to live.

* **Parameters:**
  **roots** ([`Iterable`](https://docs.python.org/3/library/typing.html#typing.Iterable)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – The full list of project root paths to persist
* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

### Example

```pycon
>>> set_project_roots(['/Users/me/projects'])
```

### hubcap.casting.ssh_url_to_components(url, ctx)

Parse SSH GitHub URL to components.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### hubcap.casting.stub_to_components(stub, ctx)

Convert org/repo stub to URL components.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### hubcap.casting.stub_to_local_folder(stub, ctx)

Try to find local folder by searching for repo name.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### hubcap.casting.to_github_stub(project)

Convert any project reference to org/repo stub.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### hubcap.casting.to_github_url(project, , ssh=True)

Convert any project reference to GitHub URL.

* **Parameters:**
  * **project** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)) – Any project reference
  * **ssh** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – If True, return SSH URL; if False, return HTTPS URL
* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### hubcap.casting.to_local_path(project)

Convert any project reference to local folder path.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### hubcap.casting.unregister_project_root(root_path)

Remove a project root folder from the registry.

* **Parameters:**
  **root_path** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Path to remove from registered roots
* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)
