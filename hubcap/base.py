"""Base objects"""

from functools import cached_property, partial
from operator import attrgetter
from typing import Mapping
from dol import KvReader, wrap_kvs
from dol.util import format_invocation

import github
from github import GithubException
from github.Auth import Token, Login

from hubcap.util import (
    RepoSpec,
    ensure_repo_obj,
    Github,
    Repository,
    Discussions,
)
from hubcap.constants import repo_collection_names


NotSet = github.GithubObject.NotSet


class ResourceNotFound(Exception):
    """Raised when a resource is not found"""


class RepositoryNotFound(github.UnknownObjectException, ResourceNotFound):
    """Raised when a repository is not found"""


def decoded_contents(content_file):
    return content_file.decoded_content
    # from base64 import b64decode
    # return b64decode(content_file.content).decode()


# TODO: Enable user parametrization of how to find token
#  Use: config2py
def find_github_token():
    import os

    return os.environ.get('HUBCAP_GITHUB_TOKEN', None) or os.environ.get(
        'GITHUB_TOKEN', None
    )


def find_user_name():
    import os

    return os.environ.get('HUBCAP_GITHUB_TOKEN', None) or os.environ.get(
        'GITHUB_USERNAME', None
    )


# --------------------------------------------------------------------------------------
# RepoObjects


def identity(x):
    return x


class RepoObjects(KvReader):
    def __init__(
        self,
        repo: RepoSpec,
        get_objs,
        *,
        objs_to_items=enumerate,
        data_of_obj=identity,
        get_objs_kwargs=None,
    ):
        self.repo = ensure_repo_obj(repo)
        self.get_objs = get_objs
        self.data_of_obj = data_of_obj
        self.get_objs_kwargs = dict(get_objs_kwargs or {})

        if isinstance(objs_to_items, str):
            key_attr = objs_to_items
            _get_key = attrgetter(key_attr)
            self.objs_to_items = lambda x: zip(map(_get_key, x), x)
        else:
            assert callable(
                objs_to_items
            ), 'issue_objs_to_itemskey must be a str or callable'
            self.objs_to_items = objs_to_items

    @cached_property
    def _objs(self):
        return {
            k: v
            for k, v in self.objs_to_items(
                self.get_objs(self.repo, **self.get_objs_kwargs)
            )
        }

    def __iter__(self):
        yield from self._objs

    def __getitem__(self, k):
        return self.data_of_obj(self._objs[k])

    # def __repr__(self):
    #     return f"{type(self).__name__}({self.repo}, {self.get_objs}, ...)"


from hubcap.util import repo_collections_configs

dflt_repo_kwargs = {
    k: {'objs_to_items': v} for k, v in repo_collections_configs.items()
}
dflt_repo_kwargs['issues']['get_objs_kwargs'] = (('state', 'open'),)


def repo_objects_instance(repo, object_name: str) -> Mapping:
    if object_name == 'issues':
        return Issues(repo)
    elif object_name == 'discussions':
        return Discussions(repo)
    elif object_name in repo_collection_names:
        return RepoObjects(
            repo,
            get_objs=getattr(Repository, f'get_{object_name}'),
            **dflt_repo_kwargs.get(object_name, {}),
        )
    else:
        raise KeyError(f'Unknown object name: {object_name}')


class RepoReader(KvReader):
    repo_collection_names = sorted(set(repo_collection_names) | {'discussions'})

    # TODO: Separate error handling concern: https://github.com/i2mint/i2/issues/45
    def __init__(self, repo: RepoSpec):
        try:
            self.repo = ensure_repo_obj(repo)
        except github.UnknownObjectException as e:
            if next(iter(e.args), None) == 404:
                raise RepositoryNotFound(f'Repository not found: {repo}')
            else:
                raise

    def __getitem__(self, k):
        return repo_objects_instance(self.repo, k)

    def __iter__(self):
        yield from self.repo_collection_names

    def __contains__(self, k):
        return k in self.repo_collection_names

    def __repr__(self):
        return f'{type(self).__name__}("{self.repo.full_name}")'


# Extras -----------------------------------------------------------------------------


class IssueCommentsBase(KvReader):
    """Base Mapping interface to repository issue comments (object)"""

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


@wrap_kvs(obj_of_data=attrgetter('body'))
class IssueComments(IssueCommentsBase):
    """Mapping interface to repository issue comments' body"""


class IssueContents(KvReader):
    """Mapping interface to repository issue contents"""

    def __init__(self, issue_obj):
        self.src = issue_obj

    def __iter__(self):
        yield from ('body', 'comments')

    def __getitem__(self, k):
        if k == 'comments':
            return IssueComments(self.src)
        else:
            return self.src.body

    def __repr__(self):
        return format_invocation(self.__class__.__name__, (self.src,))


# TODO: Figure out how to make Issues and Workflows (pickable) classes automatically
#   (The instances can be made from repo_objects_instance)
class Issues(RepoObjects):
    """
    Mapping interface to repository issues.

    :param repo: The repository to get issues from
    :param get_objs: The function to get the issues
    :param objs_to_items: A function to get the key-value pairs from the issue objects
    :param data_of_obj: A function to get the data from the issue object.
        Default is attrgetter('body'). Use identity to get the whole issue object.
    :param get_objs_kwargs: The keyword arguments to pass to the get_objs function

    The default of data_of_obj is `IssueContents`, which will give a mapping
    interface to the body and comments of the issue.
    """

    def __init__(
        self,
        repo: RepoSpec,
        get_objs=Repository.get_issues,
        *,
        objs_to_items='number',
        data_of_obj=identity,  # IssueContents,
        get_objs_kwargs=(('state', 'open'),),
    ):
        super().__init__(
            repo,
            get_objs=get_objs,
            objs_to_items=objs_to_items,
            data_of_obj=data_of_obj,
            get_objs_kwargs=get_objs_kwargs,
        )


class Workflows(RepoObjects):
    def __init__(
        self,
        repo: RepoSpec,
        get_objs=Repository.get_workflows,
        *,
        objs_to_items='id',
        data_of_obj=identity,
        get_objs_kwargs=(),
    ):
        super().__init__(
            repo,
            get_objs=get_objs,
            objs_to_items=objs_to_items,
            data_of_obj=data_of_obj,
            get_objs_kwargs=get_objs_kwargs,
        )


# --------------------------------------------------------------------------------------
# GithubReader


# TODO: use signature arithmetic
# @kv_decorator
class GithubReader(KvReader):
    """
    a Store that can access a GitHub account.

    You need to specify a token in auth, or in the environment variable 
    HUBCAP_GITHUB_TOKEN or GITHUB_TOKEN.

    The iteration is defined to be the repositories of the account_name 
    (could be organization name). 
    """

    def __init__(
        self,
        account_name: str = None,
        content_file_extractor=decoded_contents,
        *,
        auth=None,
        jwt=None,
        base_url='https://api.github.com',
        timeout=15,
        user_agent='PyGithub/Python',
        per_page=30,
        verify=True,
        retry=None,
        get_repos_kwargs=(),
        login_or_token=None,  # deprecated
        password=None,  # deprecated
    ):
        # TODO: Not sure what the rules are with account_name and login_or_token
        #  So only using a search-if-not-given strategy if account_name is None
        # account_name = account_name or find_user_name()

        if auth is None and login_or_token is not None:
            if password is not None:
                auth = Login(login_or_token, password)
            else:
                token = login_or_token
                auth = Token(token)
        else:
            auth = auth or find_github_token()

        if auth is not None:
            # TODO: This forces token use. Should we allow for login/password use?
            auth = Token(auth)
        else:
            assert isinstance(
                account_name, str
            ), 'account_name must be given (and a str)'

        _github = Github(
            auth=auth,
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
            org, name = x.full_name.split('/')
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
            self.__class__.__name__, (self.src, self.content_file_extractor),
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
            path='',
            content_file_extractor=self.content_file_extractor,
        )

    def __repr__(self):
        return format_invocation(
            self.__class__.__name__, (self.src, self.content_file_extractor),
        )


class BranchDir(KvReader):
    def __init__(
        self,
        repo: RepoSpec,
        branch_name,
        path='',
        content_file_extractor=decoded_contents,
    ):
        self.src = ensure_repo_obj(repo)
        self.branch_name = branch_name
        self.path = path
        self.content_file_extractor = content_file_extractor

    def __iter__(self):
        yield from (
            self.path + '/' + x.name + ('/' if x.type == 'dir' else '')
            for x in self.src.get_contents(self.path, ref=self.branch_name)
        )
        # yield from (x.name for x in self.src.get_contents(self.subpath, ref=self.branch_name))

    def __getitem__(self, k):
        if k.endswith('/'):
            k = k[:-1]  # remove the / suffix
        t = self.src.get_contents(k)
        # TODO: There is an inefficiency here in the isinstance(t, list) case
        if isinstance(
            t, list
        ):  # TODO: ... you already have the content_files in t, so don't need to call API again.
            return self.__class__(
                self.src, self.branch_name, k, self.content_file_extractor,
            )
        else:
            return self.content_file_extractor(t)

    def __repr__(self):
        return format_invocation(
            self.__class__.__name__,
            (self.src, self.branch_name, self.path, self.content_file_extractor,),
        )
        # return f"{self.__class__.__name__}({self.src}, {self.branch_name})"


# --------------------------------------------------------------------------------------
# Not used, but for principle:


def _content_file_isfile(content_file):
    return content_file.type == 'file'


def _content_file_isdir(content_file):
    return content_file.type == 'dir'


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
        base_url='https://api.github.com',
        timeout=15,
        user_agent='PyGithub/Python',
        per_page=30,
        verify=True,
        retry=None,
        pool_size=None,
    ):
        assert isinstance(account_name, str), 'account_name must be given (and a str)'
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
            org, name = x.full_name.split('/')
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
            self.__class__.__name__, (self.src, self.content_file_extractor),
        )
