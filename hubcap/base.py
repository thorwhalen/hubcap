"""Base objects"""
from functools import cached_property, partial
from operator import attrgetter
from dol import KvReader
from github import GithubException, Github
import github

from dol.util import format_invocation
from hubcap.util import RepoSpec, ensure_repo_obj

NotSet = github.GithubObject.NotSet


def decoded_contents(content_file):
    return content_file.decoded_content
    # from base64 import b64decode
    # return b64decode(content_file.content).decode()


# TODO: Enable user parametrization of how to find token
#  Use: config2py
def find_github_token():
    import os

    return os.environ.get("HUBCAP_GITHUB_TOKEN", None) or os.environ.get(
        "GITHUB_TOKEN", None
    )


def find_user_name():
    import os

    return os.environ.get("HUBCAP_GITHUB_TOKEN", None) or os.environ.get(
        "GITHUB_USERNAME", None
    )


# TODO: use signature arithmetic
# @kv_decorator
class GithubReader(KvReader):
    """
    a Store that can access a GitHub account
    """

    def __init__(
        self,
        account_name: str = None,
        content_file_extractor=decoded_contents,
        *,
        login_or_token=None,
        password=None,
        jwt=None,
        base_url="https://api.github.com",
        timeout=15,
        user_agent="PyGithub/Python",
        per_page=30,
        verify=True,
        retry=None,
        get_repos_kwargs=(),
    ):
        # TODO: Not sure what the rules are with account_name and login_or_token
        #  So only using a search-if-not-given strategy if account_name is None
        # account_name = account_name or find_user_name()

        login_or_token = login_or_token or find_github_token()
        if login_or_token is None:
            assert isinstance(
                account_name, str
            ), "account_name must be given (and a str)"

        _github = Github(
            login_or_token=login_or_token,
            password=password,
            jwt=jwt,
            base_url=base_url,
            timeout=timeout,
            user_agent=user_agent,
            per_page=per_page,
            verify=verify,
            retry=retry,
        )
        self._github = _github
        self.src = (
            _github.get_user(account_name) if account_name else _github.get_user()
        )
        self.content_file_extractor = content_file_extractor
        self.get_repos_kwargs = dict(get_repos_kwargs)

    def __iter__(self):
        for x in self.src.get_repos(**self.get_repos_kwargs):
            org, name = x.full_name.split("/")
            if org == self.src.login:
                yield name

    def __getitem__(self, k):
        """Retrieves a given repository
        :param k: str
        :rtype: :class:`github.Repository.Repository`
        """
        try:
            repository = self.src.get_repo(k)
        except GithubException as e:
            raise KeyError(f"Key doesn't exist: {k}")
        return Branches(repository, self.content_file_extractor)

    def __contains__(self, k):
        if self.get(k, None) is None:
            return False
        return True

    def __repr__(self):
        return format_invocation(
            self.__class__.__name__,
            (self.src, self.content_file_extractor),
        )


GitHubReader = GithubReader  # backcompatibility alias


class Branches(KvReader):
    def __init__(self, repo: RepoSpec, content_file_extractor=decoded_contents):
        self.src = ensure_repo_obj(repo)
        self.content_file_extractor = content_file_extractor
        # self._con = repo  # same as this.

    def __iter__(self):
        yield from (x.name for x in self.src.get_branches())

    def __getitem__(self, k):
        # return self.src.get_branch(k) # should not give only the branch
        # return self.src.get_contents("", ref = k)
        return BranchDir(
            self.src,
            branch_name=k,
            path="",
            content_file_extractor=self.content_file_extractor,
        )

    def __repr__(self):
        return format_invocation(
            self.__class__.__name__,
            (self.src, self.content_file_extractor),
        )


class BranchDir(KvReader):
    def __init__(
        self,
        repo: RepoSpec,
        branch_name,
        path="",
        content_file_extractor=decoded_contents,
    ):
        self.src = ensure_repo_obj(repo)
        self.branch_name = branch_name
        self.path = path
        self.content_file_extractor = content_file_extractor

    def __iter__(self):
        yield from (
            self.path + "/" + x.name + ("/" if x.type == "dir" else "")
            for x in self.src.get_contents(self.path, ref=self.branch_name)
        )
        # yield from (x.name for x in self.src.get_contents(self.subpath, ref=self.branch_name))

    def __getitem__(self, k):
        if k.endswith("/"):
            k = k[:-1]  # remove the / suffix
        t = self.src.get_contents(k)
        # TODO: There is an inefficiency here in the isinstance(t, list) case
        if isinstance(
            t, list
        ):  # TODO: ... you already have the content_files in t, so don't need to call API again.
            return self.__class__(
                self.src,
                self.branch_name,
                k,
                self.content_file_extractor,
            )
        else:
            return self.content_file_extractor(t)

    def __repr__(self):
        return format_invocation(
            self.__class__.__name__,
            (
                self.src,
                self.branch_name,
                self.path,
                self.content_file_extractor,
            ),
        )
        # return f"{self.__class__.__name__}({self.src}, {self.branch_name})"


# TODO: Find a way to lazy load comments
# TODO: Refactor out logic common to other base objects
class Issues(KvReader):
    """Mapping interface to repository issues"""

    def __init__(
        self,
        repo: RepoSpec,
        *,
        issue_key: str = 'number',
        state="open",
        **issues_filt,
    ):
        """
        :param repo: :class:`github.Repository.Repository`
        :param issue_key: str, or callable that takes an iterable of issues and returns
            an iterable of (key, issue) pairs (e.g. `enumerate`).
            If str, then the attribute of the issue to use as the key.
        """
        self.src = ensure_repo_obj(repo)
        if isinstance(issue_key, str):
            key_attr = issue_key
            _get_key = attrgetter(key_attr)
            self._issue_key = lambda x: zip(map(_get_key, x), x)
        else:
            assert callable(issue_key), "issue_key must be a str or callable"
            self._issue_key = issue_key
        self.state = state
        self.issues_filt = issues_filt

    @cached_property
    def _issues(self):
        return {
            k: v
            for k, v in self._issue_key(
                self.src.get_issues(state=self.state, **self.issues_filt)
            )
        }

    def __iter__(self):
        yield from self._issues

    def __getitem__(self, k):
        return self._issues[k]


class IssueComments(KvReader):
    """Mapping interface to repository issue comments"""

    _comment_key = enumerate

    def __init__(self, issue_obj):
        self.src = issue_obj

    @cached_property
    def _comments(self):
        return {k: v for k, v in self._comment_key(self.src.get_comments())}

    def __iter__(self):
        yield from self._comments

    def __getitem__(self, k):
        return self._comments[k]


# Not used, but for principle:


def _content_file_isfile(content_file):
    return content_file.type == "file"


def _content_file_isdir(content_file):
    return content_file.type == "dir"


# from dol import kv_wrap
#
# BranchContent = kv_wrap.outcoming_vals(lambda x: x.contents if isinstance(x, ))

from github import PaginatedList


class PaginatedListDol:
    """Gives a Sized & Iterable & Reversible view of a paginated_list.
    That is, iterating over a PaginatedListDol
    """

    def __init__(self, paginated_list: PaginatedList):
        self.paginated_list = paginated_list

    def __iter__(self):
        for item in self.paginated_list:
            yield item

    def __len__(self):
        return self.paginated_list.totalCount

    def __reversed__(self):
        return PaginatedListDol(self.paginated_list.reversed)


class GitHubDol(KvReader):
    """
    a Store that can access a GitHub account
    """

    def __init__(
        self,
        account_name: str = None,
        content_file_extractor=decoded_contents,
        login_or_token=None,
        password=None,
        jwt=None,
        base_url="https://api.github.com",
        timeout=15,
        user_agent="PyGithub/Python",
        per_page=30,
        verify=True,
        retry=None,
        pool_size=None,
    ):
        assert isinstance(account_name, str), "account_name must be given (and a str)"
        login_or_token = login_or_token or find_github_token()

        _github = Github(
            login_or_token=login_or_token,
            password=password,
            jwt=jwt,
            base_url=base_url,
            timeout=timeout,
            user_agent=user_agent,
            per_page=per_page,
            verify=verify,
            retry=retry,
            pool_size=pool_size,
        )
        self._github = _github
        self.src = (
            _github.get_user(account_name) if account_name else _github.get_user()
        )
        self.content_file_extractor = content_file_extractor

    def __iter__(self):
        for x in self.src.get_repos():
            org, name = x.full_name.split("/")
            if org == self.src.login:
                yield name

    def __getitem__(self, k):
        """Retrieves a given repository
        :param k: str
        :rtype: :class:`github.Repository.Repository`
        """
        try:
            repository = self.src.get_repo(k)
        except GithubException as e:
            raise KeyError(f"Key doesn't exist: {k}")
        return Branches(repository, self.content_file_extractor)

    def __contains__(self, k):
        if self.get(k, None) is None:
            return False
        return True

    def __repr__(self):
        return format_invocation(
            self.__class__.__name__,
            (self.src, self.content_file_extractor),
        )
