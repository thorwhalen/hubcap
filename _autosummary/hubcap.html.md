# hubcap

The simplest facade to github data.

#### WARNING
You’ll need to have a github api token (google it if you don’t have one;
it’s easy to get). You’ll have to specify this token when making hubcap objects,
or put it in an environmental variable under the name `HUBCAP_GITHUB_TOKEN` or
`GITHUB_TOKEN`

### Example usage

### RepoReader

```pycon
>>> from hubcap import RepoReader
>>> r = RepoReader('thorwhalen/test_repo')
>>> sorted(r)
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
>>> sorted([attr for attr in dir(issue_obj) if not attr.startswith('_')])
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
>>> list(issue_obj.get_comments())
[IssueComment(user=NamedUser(login="thorwhalen"), id=1801792378),
IssueComment(user=NamedUser(login="thorwhalen"), id=1801792855)]
>>> issue_comment = issue_obj.get_comment(1801792378)
>>> issue_comment.body
'Comment 1 of Test Issue A'
>>>
>>> 'discussions' in r
True
>>> discussions = r['discussions']
>>> sorted(discussions)
[1, 2, 3]
```

## hub function

The high level function `hub` is the simplest way to get started. It’s a
function that takes a path to a github resource and returns a mapping to that
resource. The mapping is lazy, so it’s only when you access a key that the
resource is actually fetched from github.

```pycon
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

```pycon
>>> issues = hub('thorwhalen/hubcap/issues')
>>> 3 in issues  # there's a "number 3" issue
True
>>> issue = issues[3]
>>> issue.title
'Test Issue'
>>> issue.body
'This is just a test issue to test that hubcap can see it.\r\n'
>>> issue.comments  # meaning "number of comments"
2
```

### Access discussions

```pycon
>>> discussions = hub('thorwhalen/hubcap/discussions')
>>> 2 in discussions
True
>>> discussion = discussions[2]
>>> discussion['title']
'Root interface of hubcap'
```

### GithubReader

One of the main classes is `GithubReader`. It’s a mapping that connects to a
github user or organization, and returns a mapping of repositories. The
repositories are also mappings, that return mappings of branches, and so on.

```pycon
>>> from hubcap import GithubReader
>>> s = GithubReader('thorwhalen')  # connnecting to a particular user/organization
>>> list(s)
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
>>> 'master' in repo and 'gh-pages' in repo
True
>>> branch = repo['master']
>>> list(branch)
['/.gitattributes', '/.github/', '/.gitignore', ...]
>>> content = branch['/pyproject.toml']
>>> print(content[:14].decode())
[build-system]
```

```pycon
>>> from hubcap import get_repository_info
>>> info = get_repository_info('thorwhalen/hubcap')
>>> list(info)
['name', 'full_name', 'description', ...]
>>> info['name']
'hubcap'
>>> info['html_url']
'https://github.com/thorwhalen/hubcap'
>>> info['stargazers_count'] >= 1
True
```

You also have other useful objects, like `Issues`, `IssueComments`, `Discussions`, etc.

### Modules

| [`actions`](hubcap.actions.html.md#module-hubcap.actions)       | GitHub Actions and CI status utilities.                                             |
|--------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------|
| [`base`](hubcap.base.html.md#module-hubcap.base)             | Base objects                                                                        |
| [`casting`](hubcap.casting.html.md#module-hubcap.casting)       | Transformation graph for GitHub project references with flexible input handling.    |
| [`constants`](hubcap.constants.html.md#module-hubcap.constants)   | A place to put constants, defaults, types...                                        |
| [`repo_slurp`](hubcap.repo_slurp.html.md#module-hubcap.repo_slurp) | Tools to slurp a repo's information                                                 |
| [`snapshot`](hubcap.snapshot.html.md#module-hubcap.snapshot)     | Incremental snapshot of GitHub orgs: issues, PRs and discussions with all comments. |
| [`tools`](hubcap.tools.html.md#module-hubcap.tools)           | A medley of tools for Hubcap.                                                       |
| [`util`](hubcap.util.html.md#module-hubcap.util)             | Utils for hubcap.                                                                   |
