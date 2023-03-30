"""Base objects"""
from dol import KvReader
from github import GithubException, Github
import github

from dol.util import format_invocation

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


# TODO: use signature arithmetic
# @kv_decorator
class GitHubReader(KvReader):
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


class Branches(KvReader):
    def __init__(self, repository_obj, content_file_extractor=decoded_contents):
        self.src = repository_obj
        self.content_file_extractor = content_file_extractor
        # self._con = repository_obj  # same as this.

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
        repository_obj,
        branch_name,
        path="",
        content_file_extractor=decoded_contents,
    ):
        self.src = repository_obj
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
