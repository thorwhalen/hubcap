"""Useful examples of code using hubcap behind the scenes.

THe functions herein could be useful to you, but their intended purpose is to demo
how you can use ``hubcap``, so we suggest you look at their code.

List repositories for a given user or organization, along with 78 fields of info.

>>> from hubcap.examples import repos_info, actions_info
>>>
>>> repos = repos_info('i2mint')  # doctest: +SKIP
>>> print(repos.shape)   # doctest: +SKIP
(60, 78)
>>> repos.head()  # doctest: +SKIP
                         id                           node_id       name  ... watchers  default_branch                                        permissions
full_name                                                                 ...
i2mint/py2mqtt    425694616                      R_kgDOGV-VmA    py2mqtt  ...        0            main  {'admin': True, 'maintain': True, 'push': True...
i2mint/mongodol   341721959  MDEwOlJlcG9zaXRvcnkzNDE3MjE5NTk=   mongodol  ...        0          master  {'admin': True, 'maintain': True, 'push': True...
i2mint/dol        299438731  MDEwOlJlcG9zaXRvcnkyOTk0Mzg3MzE=        dol  ...        4          master  {'admin': True, 'maintain': True, 'push': True...
i2mint/stream2py  238989487  MDEwOlJlcG9zaXRvcnkyMzg5ODk0ODc=  stream2py  ...        2          master  {'admin': True, 'maintain': True, 'push': True...
i2mint/creek      321448350  MDEwOlJlcG9zaXRvcnkzMjE0NDgzNTA=      creek  ...        0          master  {'admin': True, 'maintain': True, 'push': True...

[5 rows x 78 columns]
>>> list(repos.columns)   # doctest: +SKIP
['id', 'node_id', 'name', 'full_name', 'private', 'owner', 'html_url', 'description',
'fork', 'url', 'forks_url', 'keys_url', 'collaborators_url', 'teams_url', 'hooks_url
', 'issue_events_url', 'events_url', 'assignees_url', 'branches_url', 'tags_url',
'blobs_url', 'git_tags_url', 'git_refs_url', 'trees_url', 'statuses_url', 'languages_url
', 'stargazers_url', 'contributors_url', 'subscribers_url', 'subscription_url',
'commits_url', 'git_commits_url', 'comments_url', 'issue_comment_url', 'contents_url',
'compare_url', 'merges_url', 'archive_url', 'downloads_url', 'issues_url', 'pulls_url',
'milestones_url', 'notifications_url', 'labels_url', 'releases_url', 'deployments_url
', 'created_at', 'updated_at', 'pushed_at', 'git_url', 'ssh_url', 'clone_url', 'svn_url',
'homepage', 'size', 'stargazers_count', 'watchers_count', 'language', 'has_issue
s', 'has_projects', 'has_downloads', 'has_wiki', 'has_pages', 'forks_count',
'mirror_url', 'archived', 'disabled', 'open_issues_count', 'license', 'allow_forking',
'is_template', 'topics', 'visibility', 'forks', 'open_issues', 'watchers',
'default_branch', 'permissions']


Get info about github actions for a given repository.

>>> actions = actions_info('i2mint/mongodol')   # doctest: +SKIP
>>> print(actions.shape)   # doctest: +SKIP
(10, 30)
>>> actions.head()    # doctest: +SKIP
           id                    name  ...                                         repository                                    head_repository
0  1468986198  Continuous Integration  ...  {'id': 341721959, 'node_id': 'MDEwOlJlcG9zaXRv...  {'id': 341721959, 'node_id': 'MDEwOlJlcG9zaXRv...
1  1445456774  Continuous Integration  ...  {'id': 341721959, 'node_id': 'MDEwOlJlcG9zaXRv...  {'id': 341721959, 'node_id': 'MDEwOlJlcG9zaXRv...
2  1437461380  Continuous Integration  ...  {'id': 341721959, 'node_id': 'MDEwOlJlcG9zaXRv...  {'id': 341721959, 'node_id': 'MDEwOlJlcG9zaXRv...
3  1343133456  Continuous Integration  ...  {'id': 341721959, 'node_id': 'MDEwOlJlcG9zaXRv...  {'id': 341721959, 'node_id': 'MDEwOlJlcG9zaXRv...
4  1262878182  Continuous Integration  ...  {'id': 341721959, 'node_id': 'MDEwOlJlcG9zaXRv...  {'id': 341721959, 'node_id': 'MDEwOlJlcG9zaXRv...

[5 rows x 30 columns]
>>>
>>> list(actions.columns)   # doctest: +SKIP
['id', 'name', 'node_id', 'head_branch', 'head_sha', 'run_number', 'event', 'status',
'conclusion', 'workflow_id', 'check_suite_id', 'check_suite_node_id', 'url', 'html_url',
'pull_requests', 'created_at', 'updated_at', 'run_attempt', 'run_started_at',
'jobs_url', 'logs_url', 'check_suite_url', 'artifacts_url', 'cancel_url', 'rerun_url',
'previous_attempt_url', 'workflow_url', 'head_commit', 'repository', 'head_repository']
>>>


Find most recently changed repositories and check if their CI failed or not.

>>> from hubcap.examples import date_selection_lidx
>>> updated_recently = repos.iloc
...     [date_selection_lidx(repos, hours_ago=24)]  # doctest: +SKIP
>>> {repo: get_last_build_status(repo)
...     for repo in updated_recently['full_name']}  # doctest: +SKIP
{'i2mint/py2mqtt': 'failure',
 'i2mint/mongodol': 'success',
 'i2mint/dol': 'success',
 'i2mint/stream2py': 'success',
 'i2mint/creek': 'success'}

Note: You can get this directly using the `ci_status` function

>>> from hubcap.examples import ci_status
>>> ci_status('i2mint', hours_ago=24)  # doctest: +SKIP
{'i2mint/py2mqtt': 'failure',
 'i2mint/mongodol': 'success',
 'i2mint/dol': 'success',
 'i2mint/stream2py': 'success',
 'i2mint/creek': 'success'}

"""

from hubcap.scrap.direct_github_api import (
    repos_info,
    actions_info,
    date_selection_lidx,
    get_last_build_status,
    ci_status,
)
