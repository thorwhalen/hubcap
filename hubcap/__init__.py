r"""
The simplest facade to github data.

Warning: You'll need to have a github api token (google it if you don't have one;
it's easy to get). You'll have to specify this token when making hubcap objects,
or put it in an environmental variable under the name `HUBCAP_GITHUB_TOKEN` or
`GITHUB_TOKEN`


# Example usage

## RepoReader

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

## hub function

The high level function `hub` is the simplest way to get started. It's a
function that takes a path to a github resource and returns a mapping to that
resource. The mapping is lazy, so it's only when you access a key that the
resource is actually fetched from github.

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

### Access issues

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

### Access discussions

>>> discussions = hub('thorwhalen/hubcap/discussions')  # doctest: +SKIP
>>> 2 in discussions  # doctest: +SKIP
True
>>> discussion = discussions[2]    # doctest: +SKIP
>>> discussion['title']    # doctest: +SKIP
'Root interface of hubcap'


## GithubReader

One of the main classes is `GithubReader`. It's a mapping that connects to a
github user or organization, and returns a mapping of repositories. The
repositories are also mappings, that return mappings of branches, and so on.

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

You also have other useful objects, like `Issues`, `IssueComments`, `Discussions`, etc.   


"""

from github import GithubException, Github, ContentFile
from hubcap.base import (
    RepoReader,
    GithubReader,
    find_github_token,
    Branches,
    BranchDir,
    Issues,
    IssueComments,
    GitHubReader,  # backcompatibility alias of GithubReader
)
from hubcap.util import (
    get_repository_info,
    cached_github_object,
    Discussions,
    git_clone,
    git_wiki_clone,
    create_markdown_from_jdict,  # Creates a markdown representation of a discussion (metadata json-dict).
    replace_relative_urls,  # replace relative urls with absolute ones
    parse_github_url,  #  parse a GitHub URL and returns a dict of its components
    generate_github_url,  # generate a GitHub URL from the provided components dict.
    transform_github_url,  # transform a GitHub URL to another type, updating components as needed.
)
from hubcap.tools import hub, notebook_to_markdown
from hubcap.repo_slurp import repo_text_aggregate
