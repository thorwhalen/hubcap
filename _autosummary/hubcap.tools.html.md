# hubcap.tools

A medley of tools for Hubcap.

### Functions

| [`copy_discussion`](#hubcap.tools.copy_discussion)(source_discussion_url, ...)       | Copies a discussion from a source URL to a target repository URL.                              |
|----------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| [`create_discussion`](#hubcap.tools.create_discussion)(repo_id, title, body, ...)      | Creates a new discussion in the target repository.                                             |
| [`create_discussion_comment`](#hubcap.tools.create_discussion_comment)(discussion_id, body)    | Adds a comment to an existing discussion.                                                      |
| [`get_author_commits`](#hubcap.tools.get_author_commits)(repo, author_email, ...)       | Fetches GitHub commits for a specific author within a given date range.                        |
| [`get_ci_info`](#hubcap.tools.get_ci_info)(repo, \*[, refresh, token])           | Get CI (GitHub Actions) info for a repository, with caching.                                   |
| [`get_discussion_data`](#hubcap.tools.get_discussion_data)(owner, repo_name, ...)        | Fetches the full JSON data for a discussion, including comments, using the GitHub GraphQL API. |
| [`get_github_token`](#hubcap.tools.get_github_token)()                                | Return a GitHub token from common env var names, or None if not set.                           |
| [`get_repository_id`](#hubcap.tools.get_repository_id)(owner, repo_name)               | Gets the GraphQL node ID of a repository.                                                      |
| `hub`(path)                                                                                        |                                                                                                |
| [`notebook_to_markdown`](#hubcap.tools.notebook_to_markdown)(notebook_path[, ...])        | Convert a Jupyter notebook to Markdown and optionally post-process the output.                 |
| [`parse_github_discussion_url`](#hubcap.tools.parse_github_discussion_url)(discussion_url)       | Parses a GitHub discussion URL to extract owner, repo, and discussion number.                  |
| [`parse_github_repo_url`](#hubcap.tools.parse_github_repo_url)(repo_url)                   | Parses a GitHub repository URL to extract owner and repo name.                                 |
| [`postprocess_markdown_from_notebook`](#hubcap.tools.postprocess_markdown_from_notebook)(md_src, ...)   | Post-process Markdown content generated from a notebook.                                       |
| [`run_graphql_query`](#hubcap.tools.run_graphql_query)(query[, variables])             | Executes a GraphQL query against the GitHub API.                                               |
| [`team_repositories_action`](#hubcap.tools.team_repositories_action)(repositories, team, ...) | Add a list of repositories to a team with read permission                                      |

### Classes

| [`LocalRepoArtifacts`](#hubcap.tools.LocalRepoArtifacts)([refresh])   | Provides mapping interfaces to locally cached repository artifacts.   |
|----------------------------------------------------------------------------------|-----------------------------------------------------------------------|

### *class* hubcap.tools.LocalRepoArtifacts(refresh=False)

Bases: `KvReader`

Provides mapping interfaces to locally cached repository artifacts.

This class gives you access to cached repository information, discussions, and
issues through simple mapping interfaces. Data is cached locally and can be
refreshed on demand.

* **Parameters:**
  **refresh** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – If True, always fetch fresh data from GitHub and update cache.
  If False, use cached data when available.

#### info

Mapping interface to repository info (info.json for each repo)

#### discussions

Mapping interface to repository discussions

#### issues

Mapping interface to repository issues

#### ci

Mapping interface to repository CI (GitHub Actions) information

### Example

```pycon
>>> artifacts = LocalRepoArtifacts(refresh=False)
>>> # List available artifact types
>>> list(artifacts)
['info', 'discussions', 'issues', 'ci']
>>> # Access via attribute
>>> info = artifacts.info['thorwhalen/hubcap']
>>> # Or via mapping interface
>>> info = artifacts['info']['thorwhalen/hubcap']
>>> # Get cached discussions
>>> discussions = artifacts.discussions['thorwhalen/hubcap']
>>> # Access a specific discussion
>>> discussion_2 = discussions[2]
>>> # Get cached issues
>>> issues = artifacts.issues['thorwhalen/hubcap']
>>> # Get CI info
>>> ci_info = artifacts.ci['thorwhalen/hubcap']
>>> ci_info['current_state']  # True (success), False (failure), or None
True
```

The cache is stored in: {app_data_dir}/repos/{org}/{repo}/{artifact_type}/
For example:

> - Info: ~/.local/share/hubcap/repos/thorwhalen/hubcap/info.json
> - Discussions: ~/.local/share/hubcap/repos/thorwhalen/hubcap/discussions/1.json
> - Issues: ~/.local/share/hubcap/repos/thorwhalen/hubcap/issues/4.json
> - CI: ~/.local/share/hubcap/repos/thorwhalen/hubcap/ci_info.json

### hubcap.tools.add_repos_to_team(repositories, team, , action='add_to_repo', org, wait_s=1)

Add a list of repositories to a team with read permission

### hubcap.tools.copy_discussion(source_discussion_url, target_repo_url, , target_category_name='General')

Copies a discussion from a source URL to a target repository URL.
Attempts to preserve content and provide context for original authors/timestamps.

### hubcap.tools.create_discussion(repo_id, title, body, category_id)

Creates a new discussion in the target repository.

### hubcap.tools.create_discussion_comment(discussion_id, body)

Adds a comment to an existing discussion.

### hubcap.tools.get_author_commits(repo, author_email, days_range)

Fetches GitHub commits for a specific author within a given date range.

* **Parameters:**
  * **repo_name** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str)) – The repo_owner/repo_name in the format for a repo.
  * **author_email** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – The email address of the author to filter commits by.
  * **days_range** ([`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple) | [`int`](https://docs.python.org/3/builtins/functions.html#int)) – The date range for the commits.
    If an int, it’s the number of days back from today.
    If a tuple, it’s (start_date_str, end_date_str) in ‘YYYY-MM-DD’ format (inclusive).
* **Returns:**
  A list of dictionaries, where each dictionary represents a commit
  : and contains ‘sha’, ‘message’, ‘author_name’, ‘author_email’, ‘commit_date’.
    Returns an empty list if no commits are found or an error occurs.
* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)]

### hubcap.tools.get_ci_info(repo, , refresh=False, token=None)

Get CI (GitHub Actions) info for a repository, with caching.

Fetches the most recent GitHub Actions workflow runs and returns comprehensive
info along with the current CI state. Uses actions_info which gets runs sorted
by last updated, so we get the most recent regardless of time period.

* **Parameters:**
  * **repo** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Repository in ‘owner/repo’ format
  * **refresh** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – If True, fetches fresh data. If False, uses cached data when available.
  * **token** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – GitHub API token (optional, uses environment variable if not provided)
* **Returns:**
  Contains ‘actions’ (list of workflow runs) and ‘current_state’ (bool/None).
  : ’current_state’ is True for success, False for failure, None for no CI or cancelled.
* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### Example

```pycon
>>> ci = get_ci_info('thorwhalen/hubcap')
>>> ci['current_state']
True
>>> ci['actions'][0]['conclusion']
'success'
```

### hubcap.tools.get_discussion_data(owner, repo_name, discussion_number)

Fetches the full JSON data for a discussion, including comments,
using the GitHub GraphQL API.

### hubcap.tools.get_github_token()

Return a GitHub token from common env var names, or None if not set.

### hubcap.tools.get_repository_id(owner, repo_name)

Gets the GraphQL node ID of a repository.

### hubcap.tools.notebook_to_markdown(notebook_path, output_dir=None, repo_root_url=None, , image_relative_dir='')

Convert a Jupyter notebook to Markdown and optionally post-process the output.

* **Parameters:**
  * **notebook_path** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Path to the Jupyter notebook.
  * **output_dir** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Directory where the Markdown file will be written.
    If None, the Markdown is returned as a string.
  * **repo_root_url** ([`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict) | [`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Root URL for replacing relative paths in the Markdown.
  * **image_relative_dir** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – The (relative) directory where the images should be saved.
* **Returns:**
  The Markdown content, optionally post-processed.
* **Return type:**
  [*str*](https://docs.python.org/3/builtins/stdtypes.html#str)

Usage Examples

### Convert a notebook to Markdown and return as a string

```pycon
>>> markdown_string = notebook_to_markdown(
    notebook_path="example_notebook.ipynb",
    output_dir=None,  # Do not save to a file
    repo_root_url="https://github.com/username/repo/blob/main/",
    image_relative_dir="images"
)
```

### Post-process directly from a notebook file

```pycon
>>> notebook_to_markdown = post_process_markdown_generated_from_notebook(
    md_src="example_notebook.ipynb",
    repo_root_url="https://github.com/username/repo/blob/main/"
)
```

### hubcap.tools.parse_github_discussion_url(discussion_url)

Parses a GitHub discussion URL to extract owner, repo, and discussion number.

### hubcap.tools.parse_github_repo_url(repo_url)

Parses a GitHub repository URL to extract owner and repo name.

### hubcap.tools.postprocess_markdown_from_notebook(md_src, repo_root_url, md_trg=None)

Post-process Markdown content generated from a notebook.

* **Parameters:**
  * **md_src** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Markdown content, path to a Markdown file, or path to an ipynb file.
  * **repo_root_url** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Root URL for replacing relative paths.
  * **md_trg** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Path to save the post-processed Markdown.
* **Returns:**
  The post-processed Markdown content.
* **Return type:**
  [*str*](https://docs.python.org/3/builtins/stdtypes.html#str)

### hubcap.tools.rm_repos_from_team(repositories, team, , action='remove_from_repos', org, wait_s=1)

Add a list of repositories to a team with read permission

### hubcap.tools.run_graphql_query(query, variables=None)

Executes a GraphQL query against the GitHub API.

### hubcap.tools.team_repositories_action(repositories, team, , action, org, wait_s=1)

Add a list of repositories to a team with read permission
