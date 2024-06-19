# hubcap
A [dol](https://github.com/i2mint/dol) (i.e. dict-like) interface to github

To install:	```pip install hubcap```


# Examples

## Basics

The simplest facade to github data.

Interact with github like you'd interact with a `dict` object.

Warning: You'll need to have a github api token (google it if you don't have one;
it's easy to get). You'll have to specify this token when making hubcap objects,
or put it in an environmental variable under the name `GITHUB_TOKEN` or `HUBCAP_GITHUB_TOKEN` 
(useful since github actions doesn't allow you to have env variables starting with `GITHUB`).


```python
>>> s = GitHubReader('thorwhalen')  # connnecting to a particular user/organization
>>> list(s)  # doctest: +SKIP
['agen',
 'aix',
 ...
 'viral',
 'wealth',
 'wrapt']
>>> 'a_non_existing_repository_name' in s
False
>>> 'hubcap' in s  # of course, this will be true, it's what you're using now!
True
>>> repo = s['hubcap']
>>> list(repo)
['master']
>>> branch = repo['master']
>>> list(branch)  # doctest: +NORMALIZE_WHITESPACE
['/.gitattributes',
 '/.github/',
 '/.gitignore',
 '/LICENSE',
 '/README.md',
 '/docsrc/',
 '/hubcap/',
 '/setup.cfg',
 '/setup.py']
>>> content = branch['/setup.cfg']
>>> print(content[:32].decode())
[metadata]
name = hubcap
version
```


## Listing repositories and information about them


List repositories for a given user or organization, along with 78 fields of info.

```python
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

```


Get info about github actions for a given repository.

```python
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
```


Find most recently changed repositories and check if their CI failed or not.

```python
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
```


Note: You can get this directly using the `ci_status` function

```python
>>> from hubcap.examples import ci_status
>>> ci_status('i2mint', hours_ago=24)  # doctest: +SKIP
{'i2mint/py2mqtt': 'failure',
 'i2mint/mongodol': 'success',
 'i2mint/dol': 'success',
 'i2mint/stream2py': 'success',
 'i2mint/creek': 'success'}
```


## RepoReader

```python
>>> from hubcap import RepoReader
>>> r = RepoReader('thorwhalen/test_repo')
>>> sorted(r)  # doctest: +SKIP
['artifacts', 'assignees', 'autolinks', 'branches', 'codescan_alerts', 'collaborators', 
'comments', 'commits', 'contributors', 'deployments', 'discussions', 'downloads', 
'environments', 'events', 'forks', 'git_refs', 'hooks', 'issues', 'issues_comments', 
'issues_events', 'labels', 'languages', 'milestones', 'network_events', 
'notifications', 'pending_invitations', 'projects', 'pulls', 'pulls_comments', 
'pulls_review_comments', 'releases', 'repository_advisories', 'secrets', 
'self_hosted_runners', 'stargazers', 'stargazers_with_dates', 'stats_contributors', 
'subscribers', 'tags', 'teams', 'top_paths', 'top_referrers', 'topics', 'variables', 
'watchers', 'workflow_runs', 'workflows']
>>>
>>> 'issues' in r
True
>>> issues = r['issues']
>>> sorted(issues)
[4, 5]
>>> issue_obj = issues[4]
>>> issue_obj
Issue(title="Test Issue A", number=4)
>>> sorted([attr for attr in dir(issue_obj) if not attr.startswith('_')])  # doctest: +SKIP
['CHECK_AFTER_INIT_FLAG', 'active_lock_reason', 'add_to_assignees', 'add_to_labels', 
'as_pull_request', 'assignee', 'assignees', 'body', 'closed_at', 'closed_by', 
'comments', 'comments_url', 'create_comment', 'create_reaction', 'created_at', 
'delete_labels', 'delete_reaction', 'edit', 'etag', 'events_url', 'get__repr__', 
'get_comment', 'get_comments', 'get_events', 'get_labels', 'get_reactions', 
'get_timeline', 'html_url', 'id', 'labels', 'labels_url', 'last_modified', 'lock', 
'locked', 'milestone', 'number', 'pull_request', 'raw_data', 'raw_headers', 
'remove_from_assignees', 'remove_from_labels', 'repository', 'setCheckAfterInitFlag', 
'set_labels', 'state', 'state_reason', 'title', 'unlock', 'update', 'updated_at', 
'url', 'user']
>>> issue_obj.number
4
>>> issue_obj.state
'open'
>>> issue_obj.labels
[Label(name="documentation"), Label(name="enhancement")]
>>> # title of issue
>>> issue_obj.title
'Test Issue A'
>>> # content of issue
>>> issue_obj.body
'Contents of Test Issue A'
>>>
>>> issue_obj.comments
2
>>>
>>> list(issue_obj.get_comments())  # doctest: +NORMALIZE_WHITESPACE
[IssueComment(user=NamedUser(login="thorwhalen"), id=1801792378), 
IssueComment(user=NamedUser(login="thorwhalen"), id=1801792855)]
>>> issue_comment = issue_obj.get_comment(1801792378)
>>> issue_comment.body
'Comment 1 of Test Issue A'
>>>
>>> 'discussions' in r
True
>>> discussions = r['discussions']  # doctest: +SKIP
>>> sorted(discussions)  # doctest: +SKIP
[1, 2, 3]
```


## hub function

The high level function `hub` is the simplest way to get started. It's a
function that takes a path to a github resource and returns a mapping to that
resource. The mapping is lazy, so it's only when you access a key that the
resource is actually fetched from github.

```python
>>> repositories = hub('thorwhalen')
>>> 'hubcap' in repositories
True
>>> hubcap_repo = repositories['hubcap']
>>>
>>> repo = hub('thorwhalen/hubcap')
>>> 'master' in repo
True
>>> master_files = repo['master']
>>>
>>> files = hub('thorwhalen/hubcap/master')
>>> '/README.md' in files
True
>>> '/hubcap/' in files
True
>>> hubcap_files = files['/hubcap/']
>>> '/hubcap/base.py' in hubcap_files
True
```

### Access issues

```python
>>> issues = hub('thorwhalen/hubcap/issues')
>>> 3 in issues  # there's a "number 3" issue
True
>>> issue = issues[3]
>>> issue.title
'Test Issue'
>>> issue.body
'This is just a test issue to test that hubcap can see it.\r\n'
>>> issue.comments  # meaning "number of comments"
1
```

### Access discussions

```python
>>> discussions = hub('thorwhalen/hubcap/discussions')  # doctest: +SKIP
>>> # get a list of discussion (keys)
>>> list(discussions)  # doctest: +SKIP
[2, ...]
>>> # the discussion 2 should be included in that list
>>> 2 in discussions  # doctest: +SKIP
True
>>> discussion = discussions[2]   # doctest: +SKIP
>>> discussion  # doctest: +SKIP
{'number': 2,
 'title': 'Root interface of hubcap',
 'body': 'Every time I need to do something with `hubcap` ...',
 'author': {'login': 'thorwhalen'},
 'createdAt': '2023-11-07T09:30:59Z',
 'updatedAt': '2023-12-05T08:25:39Z',
 'comments': [{'body': 'Further it would be nice if we ...',
   'author': 'thorwhalen',
   'replies': []}]}
>>> discussion['title']    # doctest: +SKIP
'Root interface of hubcap'
```

Here's a nice trick for those want to download a discussion in a nice readable format, 
for you, or some AI, to look through. 

```python 
>>> from hubcap import create_markdown_from_jdict
>>> markdown_string = create_markdown_from_jdict(discussion)  # doctest: +SKIP
>>> print(markdown_string)  # doctest: +SKIP
# Root interface of hubcap
<BLANKLINE>
Every time I need to do something with `hubcap` I need to look up how it works again. 
<BLANKLINE>
That's negative points
```

## GithubReader

One of the main classes is `GithubReader`. It's a mapping that connects to a
github user or organization, and returns a mapping of repositories. The
repositories are also mappings, that return mappings of branches, and so on.

```python
>>> from hubcap import GithubReader
>>> s = GithubReader('thorwhalen')  # connnecting to a particular user/organization
>>> list(s)  # doctest: +SKIP
['agen',
 'aix',
 ...
 'viral',
 'wealth',
 'wrapt']
>>> 'a_non_existing_repository_name' in s
False
>>> 'hubcap' in s  # of course, this will be true, it's what you're using now!
True
>>> repo = s['hubcap']
>>> list(repo)
['master']
>>> branch = repo['master']
>>> list(branch)  # doctest: +NORMALIZE_WHITESPACE
['/.gitattributes', '/.github/', '/.gitignore', '/LICENSE',
'/README.md', '/docsrc/', '/hubcap/', '/misc/', '/setup.cfg', '/setup.py']
>>> content = branch['/setup.cfg']
>>> print(content[:32].decode())
[metadata]
name = hubcap
version

>>> from hubcap import get_repository_info
>>> info = get_repository_info('thorwhalen/hubcap')
>>> list(info)  # doctest: +NORMALIZE_WHITESPACE
['name', 'full_name', 'description', 'stargazers_count',
'forks_count', 'watchers_count', 'html_url', 'last_commit_date']
>>> info['name']
'hubcap'
>>> info['html_url']
'https://github.com/thorwhalen/hubcap'
>>> info['stargazers_count'] >= 1
True
```

You also have other useful objects, like `Issues`, `IssueComments`, `Discussions`, etc.   


## github_repo_text_aggregate

```python
>>> owner_repo_files = github_repo_text_aggregate('thorwhalen/hubcap')  # doctest: +SKIP
>>> markdown_output = github_repo_text_aggregate(owner_repo_files)  # doctest: +SKIP
```


# Recipes

## Clone to temp folder and get store (mapping) of files

```python
from hubcap import git_clone, git_wiki_clone
from dol import TextFiles, filt_iter, Pipe

repo_py_files = Pipe(
    git_clone, TextFiles, filt_iter(filt=lambda x: x.endswith('.py'))
)
repo_wiki_files = Pipe(git_wiki_clone, TextFiles)
```

```python
py_files = repo_py_files('i2mint/dol')
len(py_files)
# 37
```

```python
wiki_files = repo_wiki_files('i2mint/dol')
list(wiki_files)
# ['Recipes.md',
#  'Critiques-and-their-comebacks.md',
#  'Home.md',
#  'Mapping-Views.md']
```