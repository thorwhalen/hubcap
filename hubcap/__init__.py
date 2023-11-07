r"""
The simplest facade to github data.

Warning: You'll need to have a github api token (google it if you don't have one;
it's easy to get). You'll have to specify this token when making hubcap objects,
or put it in an environmental variable under the name `HUBCAP_GITHUB_TOKEN` or
`GITHUB_TOKEN`


# Example usage

## hubcap function

The high level function `hubcap` is the simplest way to get started. It's a
function that takes a path to a github resource and returns a mapping to that
resource. The mapping is lazy, so it's only when you access a key that the
resource is actually fetched from github.

>>> repositories = hubcap('thorwhalen')
>>> 'hubcap' in repositories
True
>>> hubcap_repo = repositories['hubcap']
>>>
>>> repo = hubcap('thorwhalen/hubcap')
>>> 'master' in repo
True
>>> master_files = repo['master']
>>>
>>> files = hubcap('thorwhalen/hubcap/master')
>>> '/README.md' in files
True
>>> '/hubcap/' in files
True
>>> hubcap_files = files['/hubcap/']
>>> '/hubcap/base.py' in hubcap_files
True

### Access issues

>>> issues = hubcap('thorwhalen/hubcap/issues')
>>> 3 in issues  # there's a "number 3" issue
>>> issue = issues[3]
>>> issue.title
'Test Issue'
>>> issue.body
'This is just a test issue to test that hubcap can see it.\r\n'
>>> issue.comments  # meaning "number of comments"
1

### Access discussions

>>> discussions = hubcap('thorwhalen/hubcap/discussions')
>>> 2 in discussions  # issue number 2 is in the discussions
True
>>> discussion = discussions[2]
>>> discussion['title']
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
    GithubReader,
    find_github_token,
    Branches,
    BranchDir,
    Issues,
    IssueComments,
    GitHubReader,  # backcompatibility alias of GithubReader
)
from hubcap.util import get_repository_info, cached_github_object, Discussions
from hubcap.tools import hubcap
