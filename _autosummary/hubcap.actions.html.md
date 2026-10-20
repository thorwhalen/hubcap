# hubcap.actions

GitHub Actions and CI status utilities.

This module provides functions for checking GitHub Actions workflow status and CI results.

### Functions

| [`actions_info`](#hubcap.actions.actions_info)([repo, per_page, token])           | Github actions runs info: dataframe of workflow runs sorted by last updated.   |
|--------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------|
| [`ci_status`](#hubcap.actions.ci_status)([user, hours_ago, token])             | Get a dict of CI conclusions for all recently updated repos for a user/org.    |
| [`date_selection_lidx`](#hubcap.actions.date_selection_lidx)(df[, hours_ago, ...])       | Filter DataFrame rows by date threshold.                                       |
| [`get_action_ci_status`](#hubcap.actions.get_action_ci_status)(repos[, hours_ago, token]) | Get a table of CI status for repositories.                                     |
| [`get_headers`](#hubcap.actions.get_headers)(token)                              | Get HTTP headers for GitHub API requests.                                      |
| [`get_last_build_status`](#hubcap.actions.get_last_build_status)([repo, token])            | Check the most recent GitHub Actions status of a repo.                         |
| [`get_token`](#hubcap.actions.get_token)([token, environ_name])                | Resolves token from parameter or environment variable.                         |
| [`repos_info`](#hubcap.actions.repos_info)([user, token])                       | List repos and their info as a DataFrame.                                      |

### hubcap.actions.actions_info(repo='thorwhalen/graze', per_page=10, token=None, \*\*params)

Github actions runs info: dataframe of workflow runs sorted by last updated.

* **Parameters:**
  * **repo** – Repository in ‘owner/repo’ format
  * **per_page** – Number of workflow runs to retrieve
  * **token** – GitHub API token
  * **\*\*params** – Additional query parameters
* **Returns:**
  DataFrame of workflow runs with columns like ‘id’, ‘name’,
  : ’status’, ‘conclusion’, ‘created_at’, ‘updated_at’, etc.
* **Return type:**
  pd.DataFrame

### Example

```pycon
>>> actions = actions_info('i2mint/mongodol')
>>> actions.shape
(10, 30)
>>> list(actions.columns[:5])
['id', 'name', 'node_id', 'head_branch', 'head_sha']
```

### hubcap.actions.ci_status(user='thorwhalen', hours_ago=24, token=None, \*\*params)

Get a dict of CI conclusions for all recently updated repos for a user/org.

* **Parameters:**
  * **user** – GitHub username or organization name
  * **hours_ago** – Only check repos updated within this many hours ago
  * **token** – GitHub API token
  * **\*\*params** – Additional parameters for repos_info
* **Returns:**
  Mapping of ‘owner/repo’ names to their CI conclusions
* **Return type:**
  [*dict*](https://docs.python.org/3/builtins/stdtypes.html#dict)

### Example

```pycon
>>> statuses = ci_status('i2mint', hours_ago=24)
>>> statuses
{'i2mint/py2mqtt': 'failure',
 'i2mint/mongodol': 'success',
 'i2mint/dol': 'success'}
```

### hubcap.actions.date_selection_lidx(df, hours_ago=24, date_column='updated_at', op=<built-in function gt>)

Filter DataFrame rows by date threshold.

Helper function to create a boolean index for rows with dates that satisfy
a comparison operator relative to a threshold.

* **Parameters:**
  * **df** – DataFrame with a date column
  * **hours_ago** – Number of hours ago for the threshold
  * **date_column** – Name of the column containing dates
  * **op** – Comparison operator (default: operator.gt for “greater than”)
* **Returns:**
  Boolean array for indexing rows that match the criteria
* **Return type:**
  np.ndarray

### Example

```pycon
>>> df = pd.DataFrame({'updated_at': ['2024-01-01', '2024-01-15']})
>>> recent_idx = date_selection_lidx(df, hours_ago=24*30)
>>> df.iloc[recent_idx]
```

### hubcap.actions.get_action_ci_status(repos, hours_ago=8760, token=None)

Get a table of CI status for repositories.

* **Parameters:**
  * **repos** – DataFrame with repository info (must have ‘full_name’ and ‘updated_at’ columns)
  * **hours_ago** – Only check repos updated within this many hours ago
  * **token** – GitHub API token
* **Returns:**
  Series mapping repo names to their CI conclusions
* **Return type:**
  pd.Series

### Example

```pycon
>>> repos = repos_info('i2mint')
>>> ci_statuses = get_action_ci_status(repos, hours_ago=24*30)
>>> ci_statuses
full_name
i2mint/dol        success
i2mint/creek      success
dtype: object
```

### hubcap.actions.get_headers(token)

Get HTTP headers for GitHub API requests.

* **Parameters:**
  **token** – GitHub API token
* **Returns:**
  Headers dictionary with Authorization and Accept fields
* **Return type:**
  [*dict*](https://docs.python.org/3/builtins/stdtypes.html#dict)

### hubcap.actions.get_last_build_status(repo='thorwhalen/graze', token=None, \*\*params)

Check the most recent GitHub Actions status of a repo.

* **Parameters:**
  * **repo** – Repository in ‘owner/repo’ format
  * **token** – GitHub API token
  * **\*\*params** – Additional query parameters
* **Returns:**
  The conclusion of the last workflow run (e.g., ‘success’,
  : ’failure’, ‘cancelled’, ‘skipped’), or None if no runs found.
* **Return type:**
  [*str*](https://docs.python.org/3/builtins/stdtypes.html#str) or *None*

### Example

```pycon
>>> status = get_last_build_status('thorwhalen/hubcap')
>>> status in ('success', 'failure', None)
True
```

### hubcap.actions.get_token(token=None, environ_name='GITHUB_TOKEN')

Resolves token from parameter or environment variable.

* **Parameters:**
  * **token** – GitHub API token. If None, will look in environment variable.
  * **environ_name** – Name of environment variable to check for token.
* **Returns:**
  GitHub API token
* **Return type:**
  [*str*](https://docs.python.org/3/builtins/stdtypes.html#str)
* **Raises:**
  [**KeyError**](https://docs.python.org/3/builtins/exceptions.html#KeyError) – If token is None and environment variable is not set.

### hubcap.actions.repos_info(user='thorwhalen', token=None, \*\*params)

List repos and their info as a DataFrame.

* **Parameters:**
  * **user** – GitHub username or organization name
  * **token** – GitHub API token
  * **\*\*params** – Additional query parameters for the API call
* **Returns:**
  DataFrame with repository information, indexed by full_name
* **Return type:**
  pd.DataFrame

### Example

```pycon
>>> repos = repos_info('i2mint')
>>> repos.shape
(60, 78)
>>> list(repos.columns[:5])
['id', 'node_id', 'name', 'full_name', 'private']
```
