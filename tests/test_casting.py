"""Tests for ``hubcap.casting``'s project-root registry and name resolution.

The registry (:func:`~hubcap.casting.register_project_root` and friends) defines
*where* a bare project name is looked up. Resolution results are cached for
speed, and these tests pin down the contract that the cache must never
contradict the registry, nor the filesystem, it derives from.
"""

import pytest

from hubcap.casting import (
    _find_project_by_name,
    get_project_roots,
    register_project_root,
    set_project_roots,
    to_local_path,
    unregister_project_root,
)

#: A project name that is never present before a test creates it.
ABSENT_PROJECT_NAME = "a_project_that_does_not_exist_yet"


def test_registering_a_root_makes_its_projects_discoverable(
    project_roots, make_project, tmp_path
):
    """A lookup that missed before registration must succeed after it.

    Regression test: the lookup cache used to memoize the miss, so registering
    the root that *contains* the project had no effect for the rest of the
    process.
    """
    root = tmp_path / "projects"
    project = make_project(root, ABSENT_PROJECT_NAME)

    # Before registering the root, the project is (correctly) not found.
    assert _find_project_by_name(ABSENT_PROJECT_NAME) is None

    project_roots(str(root))

    assert _find_project_by_name(ABSENT_PROJECT_NAME) == str(project)


def test_normalize_project_after_registering_root(
    project_roots, make_project, tmp_path
):
    """The public conversion API sees a newly registered root too.

    This is the user-visible face of the same defect: ``to_local_path`` raised
    "not found in registered roots. Searched: [<the very root that holds it>]".
    """
    root = tmp_path / "projects"
    project = make_project(root, ABSENT_PROJECT_NAME)

    with pytest.raises(ValueError):
        to_local_path(ABSENT_PROJECT_NAME)

    project_roots(str(root))

    assert to_local_path(ABSENT_PROJECT_NAME) == str(project)


def test_unregistering_a_root_hides_its_projects(
    project_roots, make_project, tmp_path
):
    """A project stops resolving once the root that held it is unregistered."""
    root = tmp_path / "projects"
    make_project(root, ABSENT_PROJECT_NAME)
    project_roots(str(root))

    assert _find_project_by_name(ABSENT_PROJECT_NAME) is not None

    unregister_project_root(str(root))

    assert _find_project_by_name(ABSENT_PROJECT_NAME) is None


def test_project_created_after_a_failed_lookup_is_found(
    project_roots, make_project, tmp_path
):
    """A project appearing on disk after a miss is found (misses aren't memoized).

    Cloning a repo into an already-registered root must not require restarting
    the process for hubcap to see it.
    """
    root = tmp_path / "projects"
    root.mkdir()
    project_roots(str(root))

    assert _find_project_by_name(ABSENT_PROJECT_NAME) is None

    project = make_project(root, ABSENT_PROJECT_NAME)

    assert _find_project_by_name(ABSENT_PROJECT_NAME) == str(project)


def test_folder_without_git_is_not_a_project(project_roots, tmp_path):
    """A plain folder under a registered root is not resolvable as a project."""
    root = tmp_path / "projects"
    (root / ABSENT_PROJECT_NAME).mkdir(parents=True)
    project_roots(str(root))

    assert _find_project_by_name(ABSENT_PROJECT_NAME) is None


def test_set_project_roots_replaces_the_registry(project_roots, tmp_path):
    """``set_project_roots`` is the single write path: it replaces, not appends."""
    root = tmp_path / "projects"
    root.mkdir()
    project_roots(str(root))
    assert str(root) in get_project_roots()

    set_project_roots([])

    assert get_project_roots() == []


def test_register_project_root_rejects_non_directories(project_roots, tmp_path):
    """Registering a path that is not a directory fails loudly."""
    missing = tmp_path / "nope"

    with pytest.raises(ValueError, match="Not a directory"):
        register_project_root(str(missing))
