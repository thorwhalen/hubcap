"""Shared fixtures for the hubcap test suite.

The project-root registry that ``hubcap.casting`` uses to resolve a bare project
name into a local folder is *persisted* in the user's config store. Tests that
register roots must therefore be sandboxed, otherwise running the suite quietly
appends throw-away paths to the developer's real configuration (and leaks
registered roots from one test into the next).

The fixtures here provide that sandbox:

- ``project_roots``: snapshot/restore of the persisted registry, yielding the
  registration callable.
- ``make_project``: factory creating a minimal git-like project folder.
- ``registered_project``: a throw-away project inside a freshly registered root,
  ready to be resolved by name.
"""

from pathlib import Path

import pytest

from hubcap.casting import (
    get_project_roots,
    register_project_root,
    set_project_roots,
)

#: Name of the throw-away project created by the ``registered_project`` fixture.
TEST_PROJECT_NAME = "test_project"

#: README content written into projects made by ``make_project``, asserted on by tests.
TEST_PROJECT_README = "# Test Project\n\nThis is a test.\n"


@pytest.fixture
def project_roots():
    """Yield ``register_project_root``, restoring the persisted registry afterwards.

    Use this whenever a test needs to register a project root: the user's real
    configuration is snapshotted before the test and put back after it, so the
    suite never mutates it durably.
    """
    saved_roots = get_project_roots()
    try:
        yield register_project_root
    finally:
        set_project_roots(saved_roots)


@pytest.fixture
def make_project():
    """Yield a ``(parent, name) -> Path`` factory creating a minimal project folder.

    ``hubcap.casting`` recognises a local project by the presence of a ``.git``
    entry, so that marker is what makes the created folder discoverable. A
    README is written too, so tests can prove they read the right folder.
    """

    def make_project(parent: Path, name: str) -> Path:
        project = Path(parent) / name
        (project / ".git").mkdir(parents=True, exist_ok=True)
        (project / "README.md").write_text(TEST_PROJECT_README)
        return project

    return make_project


@pytest.fixture
def registered_project(project_roots, make_project, tmp_path) -> Path:
    """A throw-away project inside a registered root, resolvable by its folder name.

    Returns the project's path; its ``.name`` is what tests pass to hubcap.
    """
    root = tmp_path / "projects"
    root.mkdir()
    project = make_project(root, TEST_PROJECT_NAME)
    project_roots(str(root))
    return project
