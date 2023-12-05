"""Functions that talk directly to api
"""
import os
import requests
import pandas as pd

DFLT_GITHUB_TOKEN_ENVIRON_NAME = 'GITHUB_TOKEN'
DFLT_USER = 'thorwhalen'
DFLT_REPO = 'thorwhalen/graze'


def get_token(token=None, environ_name=DFLT_GITHUB_TOKEN_ENVIRON_NAME):
    """Resolves token"""
    return token or os.environ[environ_name]


def get_headers(token):
    return {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.github.v3+json',
    }


def _repos_info(
    user=DFLT_USER,
    sort='updated',
    direction='desc',
    per_page=100,
    page=1,
    token=None,
    **params,
):
    """List repos and their info: raw response object"""

    token = get_token(token)
    params = dict(params, sort=sort, direction=direction, per_page=per_page, page=page)
    r = requests.get(
        f'https://api.github.com/users/{user}/repos',
        params=params,
        headers=get_headers(token),
    )
    return r


def repos_info(user=DFLT_USER, token=None, **params):
    """List repos and their info: dataframe"""
    r = _repos_info(user, token=token, **params)
    df = pd.DataFrame(r.json()).set_index('full_name', drop=False)
    return df


def _actions_info(repo=DFLT_REPO, per_page=10, token=None, **params):
    """Github actions runs info: raw response object"""
    token = get_token(token)
    params = dict(params, per_page=per_page)
    return requests.get(
        f'https://api.github.com/repos/{repo}/actions/runs',
        params=params,
        headers=get_headers(token),
    )


def actions_info(repo=DFLT_REPO, per_page=10, token=None, **params):
    """Github actions runs info: dataframe of workflow runs sorted by last updated"""
    r = _actions_info(repo, per_page=per_page, token=token, **params)
    workflow_runs = r.json().get('workflow_runs', [])
    df = pd.DataFrame(workflow_runs).sort_values('updated_at', ascending=False)
    return df


def get_last_build_status(repo=DFLT_REPO, token=None, **params):
    """Check on github actions status of a repo """

    r = _actions_info(repo, per_page=1, token=token, **params)
    runs_docs = r.json().get('workflow_runs', [])
    # no suitable status was found for a previous build, so the status is "None"
    if not runs_docs:
        return None
    conclusion = runs_docs[0]['conclusion']
    #     print(f">>> previous run found with conclusion={conclusion}")
    return conclusion


def get_action_ci_status(repos, hours_ago=24 * 365):
    """Get a table of CI status (failure or success or None) for some repositories"""
    import pandas as pd

    updated_recently = repos.iloc[date_selection_lidx(repos, hours_ago=hours_ago)]
    cis = {repo: get_last_build_status(repo) for repo in updated_recently['full_name']}
    return pd.Series(cis)


from operator import gt
from datetime import datetime, timedelta


def date_selection_lidx(df, hours_ago=24, date_column='updated_at', op=gt):
    thresh_date = datetime.now() - timedelta(hours=hours_ago)
    date = f'_{date_column}'
    df = df.copy()
    df[date] = pd.to_datetime(df[date_column])
    df = df.set_index(date, drop=False)
    return op(df[date], str(thresh_date)).values


def ci_status(user=DFLT_USER, hours_ago=24, token=None, **params):
    """Get a dict of CI "conclusions" for all recently updated repos for a user/org"""
    repos = repos_info(user, token=token, **params)
    updated_recently_lidx = date_selection_lidx(repos, hours_ago=hours_ago)
    updated_recently = repos.iloc[updated_recently_lidx]
    return {repo: get_last_build_status(repo) for repo in updated_recently['full_name']}


# def check_status_changed(status):
#     # NOTE: last_status==None is always considered a change. This is intentional
#     last_status = get_last_build_status()
#     res = last_status != status
#     if res:
#         print(f'status change detected (old={last_status}, new={status})')
#     else:
#         print(f'no status change detected (old={last_status}, new={status})')
#     return res
