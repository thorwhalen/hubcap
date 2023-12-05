"""A place to put constants, defaults, types..."""


from typing import Any, Literal, Tuple, Dict, Iterable, Union, Callable, NewType
from datetime import datetime

from github.Repository import Repository
from dol.signatures import Sig

# --------------------------------------------------------------------------- #
# Some functions to help create the constants


def _non_callable_non_dundered_attrs(obj: Any) -> Tuple[str]:
    return tuple(
        x for x in dir(obj) if not x.startswith('_') and not callable(getattr(obj, x))
    )


def _non_callable_non_dundered_attrs_of_repo_type() -> Tuple[str]:
    return _non_callable_non_dundered_attrs(Repository)


def _last_commit_date(repo: Repository):
    return (
        datetime.strptime(
            repo.updated_at.strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S'
        )
        .date()
        .isoformat()
    )


# --------------------------------------------------------------------------- #

# RepoProperty is a string that is a valid Repository property
repo_props = _non_callable_non_dundered_attrs_of_repo_type()
RepoProperty = Literal[repo_props]
RepoFunc = Callable[[Repository], Any]  # A function whose input is a Repository
RepoPropSpec = Union[RepoProperty, RepoFunc]  # A repo property or function on repo
# The normal way is to specify RepoInfo with a dict,
#  but iterable of items allows us to define a immutable default repo_info, so:
RepoInfo = Union[
    Dict[str, RepoProperty],  # {field: prop_spec, ...}
    Iterable[Tuple[str, RepoProperty]],  # [(field, prop_spec), ...]
    str,  # "prop1 prop2 ..."
]

_dflt_repo_props = 'name full_name description stargazers_count forks_count watchers_count html_url'.split()

DFLT_REPO_INFO = tuple(
    [*zip(_dflt_repo_props, _dflt_repo_props), ('last_commit_date', _last_commit_date)]
)


def repo_collection_names_():
    """
    List of the names of the objects that can be retrieved from a repository
    (e.g. commits, contributors, issues, pull_requests, releases, tags, etc.)
    These names are extracted by taking all the method names of the
    `github.Repository` class that start with `get_` and end with `s`,
    and removing the `get_` prefix.
    """
    repo_object_names = {
        k for k in dir(Repository) if k.startswith('get_') and k.endswith('s')
    }
    repo_object_names = {
        k[len('get_') :]
        for k in repo_object_names
        if Sig(getattr(Repository, k)).n_required == 1
    }
    return repo_object_names - set(dir(dict))


# tuple.__doc__ is read-only, so had to subclass to give my variable a doc
_tuple = type('_tuple', (tuple,), {'__doc__': repo_collection_names_.__doc__})
repo_collection_names = _tuple(sorted(repo_collection_names_()))

# TODO: When in 3.11, change to Literal[*repo_collection_names]
RepoCollectionNames = Literal[repo_collection_names]  # type: ignore
