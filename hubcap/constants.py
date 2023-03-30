"""A place to put constants, defaults, types..."""


from typing import Any, Literal, Tuple, Dict, Iterable, Union, Callable, NewType
from datetime import datetime

from github.Repository import Repository


# --------------------------------------------------------------------------- #
# Some functions to help create the constants


def _non_callable_non_dundered_attrs(obj: Any) -> Tuple[str]:
    return tuple(
        x for x in dir(obj) if not x.startswith("_") and not callable(getattr(obj, x))
    )


def _non_callable_non_dundered_attrs_of_repo_type() -> Tuple[str]:
    return _non_callable_non_dundered_attrs(Repository)


def _last_commit_date(repo: Repository):
    return (
        datetime.strptime(
            repo.updated_at.strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S"
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

_dflt_repo_props = "name full_name description stargazers_count forks_count watchers_count html_url".split()

DFLT_REPO_INFO = tuple(
    [*zip(_dflt_repo_props, _dflt_repo_props), ("last_commit_date", _last_commit_date)]
)
