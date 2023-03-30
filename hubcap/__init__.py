"""
The simplest facade to github data

Warning: You'll need to have a github api token (google it if you don't have one;
it's easy to get). You'll have to specify this token when making hubcap objects,
or put it in an environmental variable under the name `HUBCAP_GITHUB_TOKEN` or
`GITHUB_TOKEN`

>>> from hubcap import GitHubReader
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
"""


from github import GithubException, Github, ContentFile
from hubcap.base import find_github_token, GitHubReader, Branches, BranchDir
from hubcap.util import get_repository_info, cached_github_object