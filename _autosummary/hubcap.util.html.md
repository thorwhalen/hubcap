# hubcap.util

Utils for hubcap.

### Functions

| [`cached_github_object`](#hubcap.util.cached_github_object)()                            | Returns a cached authenticated GitHub client using the default token.                |
|----------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| [`create_markdown_from_discussion_jdict`](#hubcap.util.create_markdown_from_discussion_jdict)(jdict)      | Creates a markdown representation of a discussion or issue (metadata json-dict).     |
| [`create_markdown_from_jdict`](#hubcap.util.create_markdown_from_jdict)(jdict)                 | Creates a markdown representation of a discussion or issue (metadata json-dict).     |
| `defaulted_itemgetter`(d, k, default)                                                              |                                                                                      |
| [`ensure_folder_to_clone_into`](#hubcap.util.ensure_folder_to_clone_into)([...])                | Return a folder to clone into.                                                       |
| [`ensure_full_name`](#hubcap.util.ensure_full_name)(repo)                            | Ensure we have a full name (user/repo string)                                        |
| [`ensure_github_url`](#hubcap.util.ensure_github_url)(user_repo_str[, prefix])        | Ensure a string to a github url                                                      |
| `ensure_no_slash_suffix`(s)                                                                        |                                                                                      |
| [`ensure_repo_obj`](#hubcap.util.ensure_repo_obj)(repo)                             | Ensure a Repository object.                                                          |
| `ensure_slash_suffix`(s)                                                                           |                                                                                      |
| [`ensure_url_suffix`](#hubcap.util.ensure_url_suffix)(url)                            | Ensure a url suffix, that is, get rid of the (...)github.com prefix.                 |
| [`generate_github_url`](#hubcap.util.generate_github_url)(components[, url_type, ...])  | Generates a GitHub URL from the provided components dictionary.                      |
| [`get_repository_info`](#hubcap.util.get_repository_info)(repo[, repo_info, ...])       | Get info about a repository.                                                         |
| [`git`](#hubcap.util.git)([command, work_tree, git_dir, ...])           | Launch git commands.                                                                 |
| [`git_clone`](#hubcap.util.git_clone)(repo[, clone_to_folder, branch])        | Clone a GitHub repository, optionally specifying a branch.                           |
| `git_wiki_clone`(repo[, clone_to_folder, ...])                                                     |                                                                                      |
| [`github_file_contents`](#hubcap.util.github_file_contents)(file_url, \*[, egress])      | Fetches the contents of a file from a GitHub repository.                             |
| [`github_json_deserializer`](#hubcap.util.github_json_deserializer)(data)                    | Decode JSON bytes back to Python objects.                                            |
| [`github_json_serializer`](#hubcap.util.github_json_serializer)(obj)                       | Prepare objects for JSON serialization, handling GitHub API objects and datetime.    |
| `github_object`([token])                                                                           |                                                                                      |
| `github_repo_object`(repo_stub, \*[, token])                                                       |                                                                                      |
| `github_token`([token])                                                                            |                                                                                      |
| `is_url_components`(d)                                                                             |                                                                                      |
| [`parse_github_url`](#hubcap.util.parse_github_url)(url, \*[, include_url_type])     | Parses a GitHub URL and returns a dictionary of its components.                      |
| [`replace_relative_urls`](#hubcap.util.replace_relative_urls)(markdown_str, root_url, \*) | Replace relative URLs in a markdown string with absolute URLs based on the root_url. |
| [`transform_github_url`](#hubcap.util.transform_github_url)(url[, target_url_type])      | Transforms a GitHub URL to another type, updating components as needed.              |

### Classes

| [`Discussions`](#hubcap.util.Discussions)(repo, \*[, token, ...])   |    |
|----------------------------------------------------------------------------------------|----|

### *class* hubcap.util.Discussions(repo, , token=None, discussion_fields=('number', 'title', 'body', 'author', 'createdAt', 'updatedAt', 'comments'), \_max_discussions=100, \_max_comments=100, \_max_replies=100, cache=False, refresh=True)

Bases: `KvReader`

#### get_value(path, on_error=<function raise_on_error>, \*, sep=None, key_transformer=None, get_value=functools.partial(<function defaulted_itemgetter>, default={}), caught_errors=(<class 'Exception'>, ))

Get elements of a mapping through a path to be called recursively.

* **Parameters:**
  * **obj** ([`Any`](https://docs.python.org/3/library/typing.html#typing.Any)) – The object to get the path from
  * **path** – The path to get
  * **on_error** ([`Union`](https://docs.python.org/3/library/typing.html#typing.Union)[[`Callable`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Callable)[[[`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)], [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)], [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – The error handler to use (default: raise_on_error)
  * **sep** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`Callable`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Callable) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Determines a path is transforms into a tuple of keys.
    If it’s a string, `lambda path: path.split(sep)` is used.
    If not, it should be a function which takes in a path object and returns an iterable of keys.
  * **key_transformer** – A function to transform the keys of the path
  * **get_value** ([`Callable`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Callable)) – A function to get the value of a key in a mapping
  * **caught_errors** – The errors to catch (default: Exception)

It will

- split a path into keys (if sep is given, or if path is a string, will use ‘.’ as a separator by default)
- if key_transformer is given, apply to each key
- consider string keys that are numeric as ints (convenient for lists)
- get items also as attributes (attributes are checked for first for string keys)
- catch all exceptions (that are subclasses of `Exception`)

```pycon
>>> class A:
...      an_attribute = 42
>>> path_get([1, [4, 5, {'a': A}], 3], [1, 2, 'a', 'an_attribute'])
42
```

By default, if `path` is a string, it will be split on `sep`,
which is `'.'` by default.

```pycon
>>> path_get([1, [4, 5, {'a': A}], 3], '1.2.a.an_attribute')
42
```

#### NOTE
The underlying engine is `dol._paths_core.path_get_core` (shared with
`add_path_get`), but `path_get` has defaults and flexible input processing
for more convenience. For “first of several keys that exists” (not a path),
see `dol.util.chain_get`.

#### NOTE
`path_get` contains some ready-made `OnErrorType` functions in its
attributes. For example, see how we can make `path_get` have the same behavior
as `dict.get` by passing `path_get.return_none_on_error` as `on_error`:

```pycon
>>> dd = path_get({}, 'no.keys', on_error=path_get.return_none_on_error)
>>> dd is None
True
```

For example, `path_get.raise_on_error`,
`path_get.return_none_on_error`, and `path_get.return_empty_tuple_on_error`.

### hubcap.util.cached_github_object()

Returns a cached authenticated GitHub client using the default token.

### hubcap.util.create_markdown_from_discussion_jdict(jdict)

Creates a markdown representation of a discussion or issue (metadata json-dict).

Headers are used to separate the different sections.

This is meant to be applied to json exports of github discussions or issues.

#### NOTE
For issues, the ‘comments’ field is just a count (int), not the actual
comment data. For discussions, ‘comments’ is a list of comment objects with
their full data including replies.

### hubcap.util.create_markdown_from_jdict(jdict)

Creates a markdown representation of a discussion or issue (metadata json-dict).

Headers are used to separate the different sections.

This is meant to be applied to json exports of github discussions or issues.

#### NOTE
For issues, the ‘comments’ field is just a count (int), not the actual
comment data. For discussions, ‘comments’ is a list of comment objects with
their full data including replies.

### hubcap.util.ensure_folder_to_clone_into(folder_to_clone_into=None)

Return a folder to clone into. If not provided, create a temporary folder.

### hubcap.util.ensure_full_name(repo)

Ensure we have a full name (user/repo string)

```pycon
>>> ensure_full_name('https://www.github.com/thorwhalen/hubcap')
'thorwhalen/hubcap'
>>> ensure_full_name('github.com/thorwhalen/hubcap/')
'thorwhalen/hubcap'
>>> ensure_full_name('thorwhalen/hubcap')
'thorwhalen/hubcap'
```

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### hubcap.util.ensure_github_url(user_repo_str, prefix='https://github.com/')

Ensure a string to a github url

```pycon
>>> ensure_github_url('https://www.github.com/thorwhalen/hubcap')
'https://github.com/thorwhalen/hubcap'
>>> ensure_github_url('https://github.com/github.com/thorwhalen/hubcap/')
'https://github.com/thorwhalen/hubcap'
```

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### hubcap.util.ensure_repo_obj(repo)

Ensure a Repository object.

```pycon
>>> ensure_repo_obj('thorwhalen/hubcap')
Repository(full_name="thorwhalen/hubcap")
>>> repo = ensure_repo_obj('https://github.com/thorwhalen/hubcap')
>>> repo
Repository(full_name="thorwhalen/hubcap")
```

And if we pass in a `Repository` object, we just get it back:

```pycon
>>> ensure_repo_obj(repo)
Repository(full_name="thorwhalen/hubcap")
```

* **Return type:**
  `Repository`

### hubcap.util.ensure_url_suffix(url)

Ensure a url suffix, that is, get rid of the (…)github.com prefix.

```pycon
>>> ensure_url_suffix('https://www.github.com/thorwhalen/hubcap/README.md')
'thorwhalen/hubcap/README.md'
>>> ensure_url_suffix('www.github.com/thorwhalen/hubcap/README.md')
'thorwhalen/hubcap/README.md'
>>> ensure_url_suffix('thorwhalen/hubcap/README.md')
'thorwhalen/hubcap/README.md'
```

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### hubcap.util.generate_github_url(components, url_type=None, , prefer_explicit_url_type=True, ignore_extra_keys=True)

Generates a GitHub URL from the provided components dictionary.

* **Parameters:**
  * **components** ([`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`Literal`](https://docs.python.org/3/library/typing.html#typing.Literal)[`'branch'`, `'issue_number'`, `'path'`, `'pr_number'`, `'repository'`, `'username'`], [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – A dictionary containing the URL components.
  * **url_type** ([`Literal`](https://docs.python.org/3/library/typing.html#typing.Literal)[`'fully_qualified_raw'`, `'file'`, `'raw_file'`, `'tree_path'`, `'branch'`, `'issue'`, `'pull_request'`, `'releases'`, `'repository'`, `'clone_url'`]) – The type of the URL to generate.
  * **prefer_explicit_url_type** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – If True, the url_type argument takes
    precedence over the ‘url_type’ key in components.
    This is needed because by default, `parse_github_url` includes the
    ‘url_type’ key, so if you want to easily generate a URL from its
    components, you need an easy way to tell the function to ignore that
    particular key, overriding it with the `url_type` argument.
  * **ignore_extra_keys** ([*bool*](https://docs.python.org/3/builtins/functions.html#bool)) – If True, extra keys in the components dictionary
* **Returns:**
  The generated GitHub URL.
* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)
* **Raises:**
  [**ValueError**](https://docs.python.org/3/builtins/exceptions.html#ValueError) – If the components are insufficient to generate a URL.

### Examples

```pycon
>>> components = {
...     'url_type': 'repository',
...     'username': 'torvalds',
...     'repository': 'linux',
... }
>>> generate_github_url(components)
'https://github.com/torvalds/linux'
```

```pycon
>>> components = {
...     'url_type': 'branch',
...     'username': 'torvalds',
...     'repository': 'linux',
...     'branch': 'master',
... }
>>> generate_github_url(components)
'https://github.com/torvalds/linux/tree/master'
```

```pycon
>>> components = {
...     'url_type': 'file',
...     'username': 'torvalds',
...     'repository': 'linux',
...     'branch': 'master',
...     'path': 'README.md',
... }
>>> generate_github_url(components)
'https://github.com/torvalds/linux/blob/master/README.md'
```

```pycon
>>> components = {
...     'url_type': 'raw_file',
...     'username': 'torvalds',
...     'repository': 'linux',
...     'branch': 'master',
...     'path': 'README.md',
... }
>>> generate_github_url(components)
'https://raw.githubusercontent.com/torvalds/linux/master/README.md'
```

```pycon
>>> components = {
...     'url_type': 'issue',
...     'username': 'torvalds',
...     'repository': 'linux',
...     'issue_number': '1',
... }
>>> generate_github_url(components)
'https://github.com/torvalds/linux/issues/1'
```

```pycon
>>> components = {
...     'url_type': 'pull_request',
...     'username': 'torvalds',
...     'repository': 'linux',
...     'pr_number': '1',
... }
>>> generate_github_url(components)
'https://github.com/torvalds/linux/pull/1'
```

```pycon
>>> components = {
...     'url_type': 'releases',
...     'username': 'torvalds',
...     'repository': 'linux',
... }
>>> generate_github_url(components)
'https://github.com/torvalds/linux/releases'
```

```pycon
>>> components = {
...     'url_type': 'clone_url',
...     'username': 'username',
...     'repository': 'repo',
... }
>>> generate_github_url(components)
'git@github.com:username/repo.git'
```

### hubcap.util.get_repository_info(repo, repo_info=(('name', 'name'), ('full_name', 'full_name'), ('description', 'description'), ('open_issues_count', 'open_issues_count'), ('size', 'size'), ('updated_at', 'updated_at'), ('stargazers_count', 'stargazers_count'), ('forks_count', 'forks_count'), ('watchers_count', 'watchers_count'), ('html_url', 'html_url'), ('last_commit_date', <function \_last_commit_date>)), \*, refresh=True, token=None, use_auth=True)

Get info about a repository.

```pycon
>>> info = get_repository_info('thorwhalen/hubcap')
```

This gives us a `dict` with default info fields:

```pycon
>>> list(info)
['name', 'full_name', 'description', ...]
>>> info['name']
'hubcap'
>>> info['html_url']
'https://github.com/thorwhalen/hubcap'
>>> info['stargazers_count'] >= 1
True
```

We can also specify a custom `repo_info` get different info.

You can specify a space separated string of repo properties:

```pycon
>>> get_repository_info('thorwhalen/hubcap', 'name html_url')
{'name': 'hubcap', 'html_url': 'https://github.com/thorwhalen/hubcap'}
```

Note that you have a list of valid repo properties in `constants.repo_props`,
which is dynamically generated from the `github.Repository.Repository` class:

```pycon
>>> from hubcap.constants import repo_props
>>> len(repo_props) >= 90
True
```

If you want to give the fields different names, or use a function to compute some
custom information based on the repo you can specify a  dict of
`{field: prop_spec, ...}` values where `prop_spec` is either a valid repo
property or a function to compute the value (the function needs to take a
`Repository` as its first and only required argument).

```pycon
>>> get_repository_info(
...     'thorwhalen/hubcap',
...     {'name': 'name', 'has stars': lambda repo: repo.stargazers_count > 0}
... )
{'name': 'hubcap', 'has stars': True}
```

* **Parameters:**
  * **repo** (`Repository`) – Repository object or string identifier
  * **repo_info** ([`Union`](https://docs.python.org/3/library/typing.html#typing.Union)[[`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Literal`](https://docs.python.org/3/library/typing.html#typing.Literal)[`'CHECK_AFTER_INIT_FLAG'`, `'allow_auto_merge'`, `'allow_forking'`, `'allow_merge_commit'`, `'allow_rebase_merge'`, `'allow_squash_merge'`, `'allow_update_branch'`, `'anonymous_access_enabled'`, `'api_version'`, `'archive_url'`, `'archived'`, `'assignees_url'`, `'blobs_url'`, `'branches_url'`, `'clone_url'`, `'code_of_conduct'`, `'collaborators_url'`, `'comments_url'`, `'commits_url'`, `'compare_url'`, `'completed'`, `'contents_url'`, `'contributors_url'`, `'created_at'`, `'custom_properties'`, `'default_branch'`, `'delete_branch_on_merge'`, `'deployments_url'`, `'description'`, `'disabled'`, `'downloads_url'`, `'etag'`, `'events_url'`, `'fork'`, `'forks'`, `'forks_count'`, `'forks_url'`, `'full_name'`, `'git_commits_url'`, `'git_refs_url'`, `'git_tags_url'`, `'git_url'`, `'has_discussions'`, `'has_downloads'`, `'has_issues'`, `'has_pages'`, `'has_projects'`, `'has_wiki'`, `'homepage'`, `'hooks_url'`, `'html_url'`, `'id'`, `'is_template'`, `'issue_comment_url'`, `'issue_events_url'`, `'issues_url'`, `'keys_url'`, `'labels_url'`, `'language'`, `'languages_url'`, `'last_modified'`, `'last_modified_datetime'`, `'license'`, `'master_branch'`, `'merge_commit_message'`, `'merge_commit_title'`, `'merges_url'`, `'milestones_url'`, `'mirror_url'`, `'name'`, `'network_count'`, `'node_id'`, `'notifications_url'`, `'open_issues'`, `'open_issues_count'`, `'organization'`, `'owner'`, `'parent'`, `'permissions'`, `'private'`, `'pulls_url'`, `'pushed_at'`, `'raw_data'`, `'raw_headers'`, `'releases_url'`, `'requester'`, `'role_name'`, `'security_and_analysis'`, `'size'`, `'source'`, `'squash_merge_commit_message'`, `'squash_merge_commit_title'`, `'ssh_url'`, `'stargazers_count'`, `'stargazers_url'`, `'starred_at'`, `'statuses_url'`, `'subscribers_count'`, `'subscribers_url'`, `'subscription_url'`, `'svn_url'`, `'tags_url'`, `'teams_url'`, `'temp_clone_token'`, `'template_repository'`, `'topics'`, `'trees_url'`, `'updated_at'`, `'url'`, `'use_squash_pr_title_as_default'`, `'visibility'`, `'watchers'`, `'watchers_count'`, `'web_commit_signoff_required'`]], [`Iterable`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Iterable)[[`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Literal`](https://docs.python.org/3/library/typing.html#typing.Literal)[`'CHECK_AFTER_INIT_FLAG'`, `'allow_auto_merge'`, `'allow_forking'`, `'allow_merge_commit'`, `'allow_rebase_merge'`, `'allow_squash_merge'`, `'allow_update_branch'`, `'anonymous_access_enabled'`, `'api_version'`, `'archive_url'`, `'archived'`, `'assignees_url'`, `'blobs_url'`, `'branches_url'`, `'clone_url'`, `'code_of_conduct'`, `'collaborators_url'`, `'comments_url'`, `'commits_url'`, `'compare_url'`, `'completed'`, `'contents_url'`, `'contributors_url'`, `'created_at'`, `'custom_properties'`, `'default_branch'`, `'delete_branch_on_merge'`, `'deployments_url'`, `'description'`, `'disabled'`, `'downloads_url'`, `'etag'`, `'events_url'`, `'fork'`, `'forks'`, `'forks_count'`, `'forks_url'`, `'full_name'`, `'git_commits_url'`, `'git_refs_url'`, `'git_tags_url'`, `'git_url'`, `'has_discussions'`, `'has_downloads'`, `'has_issues'`, `'has_pages'`, `'has_projects'`, `'has_wiki'`, `'homepage'`, `'hooks_url'`, `'html_url'`, `'id'`, `'is_template'`, `'issue_comment_url'`, `'issue_events_url'`, `'issues_url'`, `'keys_url'`, `'labels_url'`, `'language'`, `'languages_url'`, `'last_modified'`, `'last_modified_datetime'`, `'license'`, `'master_branch'`, `'merge_commit_message'`, `'merge_commit_title'`, `'merges_url'`, `'milestones_url'`, `'mirror_url'`, `'name'`, `'network_count'`, `'node_id'`, `'notifications_url'`, `'open_issues'`, `'open_issues_count'`, `'organization'`, `'owner'`, `'parent'`, `'permissions'`, `'private'`, `'pulls_url'`, `'pushed_at'`, `'raw_data'`, `'raw_headers'`, `'releases_url'`, `'requester'`, `'role_name'`, `'security_and_analysis'`, `'size'`, `'source'`, `'squash_merge_commit_message'`, `'squash_merge_commit_title'`, `'ssh_url'`, `'stargazers_count'`, `'stargazers_url'`, `'starred_at'`, `'statuses_url'`, `'subscribers_count'`, `'subscribers_url'`, `'subscription_url'`, `'svn_url'`, `'tags_url'`, `'teams_url'`, `'temp_clone_token'`, `'template_repository'`, `'topics'`, `'trees_url'`, `'updated_at'`, `'url'`, `'use_squash_pr_title_as_default'`, `'visibility'`, `'watchers'`, `'watchers_count'`, `'web_commit_signoff_required'`]]], [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Info fields to return (default returns standard fields)
  * **refresh** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – If True, fetches fresh data from GitHub and caches it.
    If False, returns cached data if available, otherwise fetches and caches.
  * **token** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – GitHub token for authentication. If None and use_auth=True, will use
    token from environment variables or config.
  * **use_auth** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – If True (default), uses authenticated requests to avoid rate limits.
    Set to False to make unauthenticated requests.

### hubcap.util.git(command='status', , work_tree=None, git_dir=None, suppress_errors=False)

Launch git commands.

* **Parameters:**
  * **command** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – git command (e.g. ‘status’, ‘branch’, ‘commit -m “blah”’, ‘push’, etc.)
  * **work_tree** – The work_tree directory (i.e. where the project is)
  * **git_dir** – The .git directory (usually, and by default, will be taken to be “{work_tree}/.git/”
  * **suppress_errors** – If True, suppress errors and return an empty string or None.
* **Returns:**
  What ever the command line returns (decoded to string), or an empty string/None if errors are suppressed.

### hubcap.util.git_clone(repo, clone_to_folder=None, branch=None)

Clone a GitHub repository, optionally specifying a branch.

* **Parameters:**
  * **repo** – Repository URL or identifier
  * **clone_to_folder** – Local folder to clone into (creates temp folder if None)
  * **branch** – Optional branch name to clone (clones default branch if None)
* **Returns:**
  Path to the cloned repository folder

### hubcap.util.github_file_contents(file_url, \*, egress=<function <lambda>>)

Fetches the contents of a file from a GitHub repository.

* **Parameters:**
  * **file_url** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – The URL of the file to fetch (doesn’t have to be a raw file!)
  * **egress** ([`Callable`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Callable)) – A function to extract the contents of the file object. By default, it
    decodes the file object’s content as UTF-8, but if it’s bytes you want,
    don’t decode those bytes, and if it’s the “file object” you want, just
    use `egress=lambda x: x`.
* **Returns:**
  The contents of the file as a string.
* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)
* **Raises:**
  [**Exception**](https://docs.python.org/3/builtins/exceptions.html#Exception) – If the repository, file, or branch does not exist, or access is denied.

```pycon
>>> file_string = github_file_contents('https://github.com/thorwhalen/hubcap/blob/master/pyproject.toml')
>>> print(file_string[:14])
[build-system]
```

### hubcap.util.github_json_deserializer(data)

Decode JSON bytes back to Python objects.

### hubcap.util.github_json_serializer(obj)

Prepare objects for JSON serialization, handling GitHub API objects and datetime.

Handles datetime objects and other common GitHub API types by recursively
converting them to JSON-serializable types, then encoding to JSON bytes.

```pycon
>>> from datetime import datetime, timezone
>>> dt = datetime(2021, 1, 15, 22, 34, 10, tzinfo=timezone.utc)
>>> result = github_json_serializer(dt)
>>> result
b'"2021-01-15T22:34:10+00:00"'
>>> github_json_serializer({'created_at': dt, 'name': 'test'})
b'{"created_at": "2021-01-15T22:34:10+00:00", "name": "test"}'
```

### hubcap.util.parse_github_url(url, , include_url_type=True)

Parses a GitHub URL and returns a dictionary of its components.

The returned dict includes a “url_type” field that indicates the type of the URL.

* **Parameters:**
  **url** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – The GitHub URL to parse.
* **Returns:**
  A dictionary containing the parsed components.
* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)
* **Raises:**
  [**ValueError**](https://docs.python.org/3/builtins/exceptions.html#ValueError) – If the URL cannot be parsed.

### Examples

```pycon
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
```

### hubcap.util.replace_relative_urls(markdown_str, root_url, , relative_url_pattern='(!?\\\\[.\*?\\\\]\\\\()((?!http[s]?://|ftp://|mailto:|#|/)[^)]\*)(\\\\))|(<img\\\\s+[^>]\*src=")((?!http[s]?://|ftp://|mailto:|#|/)[^"]\*)(")')

Replace relative URLs in a markdown string with absolute URLs based on the root_url.

This is useful, for example, to solve problems like when pypi renders markdown and
images are not shown because they are relative URLs.
See [issue]()

* **Parameters:**
  * **markdown_str** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – The markdown content containing URLs.
  * **root_url** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str)) – The base URL to resolve relative URLs against.
* **Returns:**
  The markdown content with relative URLs replaced by absolute URLs.
* **Return type:**
  [*str*](https://docs.python.org/3/builtins/stdtypes.html#str)

### Examples

```pycon
>>> markdown_str = '''
... [With dot](./page)
... ![With double dot](../image.png)
... ![](relative/path/to/image.png)
... [Absolute Link](http://example.com)
... <img src="path/to/image" width="320">
... '''
>>> root_url = 'http://mysite.com/docs'
>>> print(replace_relative_urls(markdown_str, root_url))

[With dot](http://mysite.com/docs/page)
![With double dot](http://mysite.com/image.png)
![](http://mysite.com/docs/relative/path/to/image.png)
[Absolute Link](http://example.com)
<img src="http://mysite.com/docs/path/to/image" width="320">
```

### hubcap.util.transform_github_url(url, target_url_type='raw_file', \*\*extras)

Transforms a GitHub URL to another type, updating components as needed.

* **Parameters:**
  * **url** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – The original GitHub URL.
  * **target_url_type** ([`Literal`](https://docs.python.org/3/library/typing.html#typing.Literal)[`'fully_qualified_raw'`, `'file'`, `'raw_file'`, `'tree_path'`, `'branch'`, `'issue'`, `'pull_request'`, `'releases'`, `'repository'`, `'clone_url'`]) – The desired URL type.
  * **\*\*extras** – Additional components to update in the URL.
* **Returns:**
  The transformed GitHub URL.
* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)
* **Raises:**
  [**ValueError**](https://docs.python.org/3/builtins/exceptions.html#ValueError) – If the URL cannot be parsed or transformed.

### Examples

```pycon
>>> transform_github_url('https://github.com/torvalds/linux', 'clone_url')
'git@github.com:torvalds/linux.git'
```

```pycon
>>> transform_github_url('https://github.com/torvalds/linux/blob/master/README.md', 'raw_file')
'https://raw.githubusercontent.com/torvalds/linux/master/README.md'
```

```pycon
>>> transform_github_url('https://github.com/torvalds/linux/issues/1', 'pull_request', pr_number='42')
'https://github.com/torvalds/linux/pull/42'
```

```pycon
>>> transform_github_url('git@github.com:torvalds/linux.git', 'file', branch='master', path='README.md')
'https://github.com/torvalds/linux/blob/master/README.md'
```
