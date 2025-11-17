"""GitHub Actions and CI status utilities.

This module provides functions for checking GitHub Actions workflow status and CI results.
"""

import os
from operator import gt
from datetime import datetime, timedelta
import requests
import pandas as pd

DFLT_GITHUB_TOKEN_ENVIRON_NAME = "GITHUB_TOKEN"
DFLT_USER = "thorwhalen"
DFLT_REPO = "thorwhalen/graze"


def get_token(token=None, environ_name=DFLT_GITHUB_TOKEN_ENVIRON_NAME):
    """Resolves token from parameter or environment variable.

    Args:
        token: GitHub API token. If None, will look in environment variable.
        environ_name: Name of environment variable to check for token.

    Returns:
        str: GitHub API token

    Raises:
        KeyError: If token is None and environment variable is not set.
    """
    return token or os.environ[environ_name]


def get_headers(token):
    """Get HTTP headers for GitHub API requests.

    Args:
        token: GitHub API token

    Returns:
        dict: Headers dictionary with Authorization and Accept fields
    """
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
    }


def _repos_info(
    user=DFLT_USER,
    sort="updated",
    direction="desc",
    per_page=100,
    page=1,
    token=None,
    **params,
):
    """List repos and their info: raw response object.

    Args:
        user: GitHub username or organization name
        sort: Sort field (e.g., 'updated', 'created', 'pushed', 'full_name')
        direction: Sort direction ('asc' or 'desc')
        per_page: Number of results per page (max 100)
        page: Page number to retrieve
        token: GitHub API token
        **params: Additional query parameters

    Returns:
        requests.Response: Raw response object from GitHub API
    """
    token = get_token(token)
    params = dict(params, sort=sort, direction=direction, per_page=per_page, page=page)
    r = requests.get(
        f"https://api.github.com/users/{user}/repos",
        params=params,
        headers=get_headers(token),
    )
    return r


def repos_info(user=DFLT_USER, token=None, **params):
    """List repos and their info as a DataFrame.

    Args:
        user: GitHub username or organization name
        token: GitHub API token
        **params: Additional query parameters for the API call

    Returns:
        pd.DataFrame: DataFrame with repository information, indexed by full_name

    Example:
        >>> repos = repos_info('i2mint')  # doctest: +SKIP
        >>> repos.shape  # doctest: +SKIP
        (60, 78)
        >>> list(repos.columns[:5])  # doctest: +SKIP
        ['id', 'node_id', 'name', 'full_name', 'private']
    """
    r = _repos_info(user, token=token, **params)
    df = pd.DataFrame(r.json()).set_index("full_name", drop=False)
    return df


def _actions_info(repo=DFLT_REPO, per_page=10, token=None, **params):
    """Github actions runs info: raw response object.

    Args:
        repo: Repository in 'owner/repo' format
        per_page: Number of workflow runs to retrieve
        token: GitHub API token
        **params: Additional query parameters

    Returns:
        requests.Response: Raw response object from GitHub API
    """
    token = get_token(token)
    params = dict(params, per_page=per_page)
    return requests.get(
        f"https://api.github.com/repos/{repo}/actions/runs",
        params=params,
        headers=get_headers(token),
    )


def actions_info(repo=DFLT_REPO, per_page=10, token=None, **params):
    """Github actions runs info: dataframe of workflow runs sorted by last updated.

    Args:
        repo: Repository in 'owner/repo' format
        per_page: Number of workflow runs to retrieve
        token: GitHub API token
        **params: Additional query parameters

    Returns:
        pd.DataFrame: DataFrame of workflow runs with columns like 'id', 'name',
            'status', 'conclusion', 'created_at', 'updated_at', etc.

    Example:
        >>> actions = actions_info('i2mint/mongodol')  # doctest: +SKIP
        >>> actions.shape  # doctest: +SKIP
        (10, 30)
        >>> list(actions.columns[:5])  # doctest: +SKIP
        ['id', 'name', 'node_id', 'head_branch', 'head_sha']
    """
    r = _actions_info(repo, per_page=per_page, token=token, **params)
    workflow_runs = r.json().get("workflow_runs", [])
    df = pd.DataFrame(workflow_runs).sort_values("updated_at", ascending=False)
    return df


def get_last_build_status(repo=DFLT_REPO, token=None, **params):
    """Check the most recent GitHub Actions status of a repo.

    Args:
        repo: Repository in 'owner/repo' format
        token: GitHub API token
        **params: Additional query parameters

    Returns:
        str or None: The conclusion of the last workflow run (e.g., 'success',
            'failure', 'cancelled', 'skipped'), or None if no runs found.

    Example:
        >>> status = get_last_build_status('thorwhalen/hubcap')  # doctest: +SKIP
        >>> status in ('success', 'failure', None)  # doctest: +SKIP
        True
    """
    r = _actions_info(repo, per_page=1, token=token, **params)
    runs_docs = r.json().get("workflow_runs", [])
    # no suitable status was found for a previous build, so the status is "None"
    if not runs_docs:
        return None
    conclusion = runs_docs[0]["conclusion"]
    return conclusion


def date_selection_lidx(df, hours_ago=24, date_column="updated_at", op=gt):
    """Filter DataFrame rows by date threshold.

    Helper function to create a boolean index for rows with dates that satisfy
    a comparison operator relative to a threshold.

    Args:
        df: DataFrame with a date column
        hours_ago: Number of hours ago for the threshold
        date_column: Name of the column containing dates
        op: Comparison operator (default: operator.gt for "greater than")

    Returns:
        np.ndarray: Boolean array for indexing rows that match the criteria

    Example:
        >>> df = pd.DataFrame({'updated_at': ['2024-01-01', '2024-01-15']})  # doctest: +SKIP
        >>> recent_idx = date_selection_lidx(df, hours_ago=24*30)  # doctest: +SKIP
        >>> df.iloc[recent_idx]  # doctest: +SKIP
    """
    thresh_date = datetime.now() - timedelta(hours=hours_ago)
    date = f"_{date_column}"
    df = df.copy()
    df[date] = pd.to_datetime(df[date_column])
    df = df.set_index(date, drop=False)
    return op(df[date], str(thresh_date)).values


def get_action_ci_status(repos, hours_ago=24 * 365, token=None):
    """Get a table of CI status for repositories.

    Args:
        repos: DataFrame with repository info (must have 'full_name' and 'updated_at' columns)
        hours_ago: Only check repos updated within this many hours ago
        token: GitHub API token

    Returns:
        pd.Series: Series mapping repo names to their CI conclusions

    Example:
        >>> repos = repos_info('i2mint')  # doctest: +SKIP
        >>> ci_statuses = get_action_ci_status(repos, hours_ago=24*30)  # doctest: +SKIP
        >>> ci_statuses  # doctest: +SKIP
        full_name
        i2mint/dol        success
        i2mint/creek      success
        dtype: object
    """
    updated_recently = repos.iloc[date_selection_lidx(repos, hours_ago=hours_ago)]
    cis = {
        repo: get_last_build_status(repo, token=token)
        for repo in updated_recently["full_name"]
    }
    return pd.Series(cis)


def ci_status(user=DFLT_USER, hours_ago=24, token=None, **params):
    """Get a dict of CI conclusions for all recently updated repos for a user/org.

    Args:
        user: GitHub username or organization name
        hours_ago: Only check repos updated within this many hours ago
        token: GitHub API token
        **params: Additional parameters for repos_info

    Returns:
        dict: Mapping of 'owner/repo' names to their CI conclusions

    Example:
        >>> statuses = ci_status('i2mint', hours_ago=24)  # doctest: +SKIP
        >>> statuses  # doctest: +SKIP
        {'i2mint/py2mqtt': 'failure',
         'i2mint/mongodol': 'success',
         'i2mint/dol': 'success'}
    """
    repos = repos_info(user, token=token, **params)
    updated_recently_lidx = date_selection_lidx(repos, hours_ago=hours_ago)
    updated_recently = repos.iloc[updated_recently_lidx]
    return {
        repo: get_last_build_status(repo, token=token)
        for repo in updated_recently["full_name"]
    }
