"""Verify the four ingress decorator patterns documented in CASTING_GUIDE.md.

Each test decorates a function with ``project_kinds.ingress`` in one of the four
documented spellings and calls it with a bare project name, checking that the
name was resolved to *this test's* local project folder before the function body
ran. Asserting the full resolved path (not merely the name) is deliberate: it is
what catches a resolution cache handing back a stale folder.

The ``project`` fixture registers a throw-away project root for every test, so
resolution has something to find without touching the developer's real config.
"""

from pathlib import Path

import pytest

from hubcap.casting import project_kinds


@pytest.fixture(autouse=True)
def project(registered_project):
    """Make a throw-away project resolvable by name for every test in this module."""
    return registered_project


def test_pattern_1_explicit_arg_name(project):
    """Pattern 1: ``@graph.ingress('kind', 'arg_name')``."""

    @project_kinds.ingress('local_proj_folder', 'project_path')
    def analyze(project_path: str, depth: int = 1):
        return project_path, depth

    resolved, depth = analyze(project.name, depth=2)

    assert Path(resolved) == project
    assert depth == 2


def test_pattern_2_kind_only(project):
    """Pattern 2: ``@graph.ingress('kind')`` transforms the first argument."""

    @project_kinds.ingress('local_proj_folder')
    def analyze(project_path: str):
        return project_path

    assert Path(analyze(project.name)) == project


def test_pattern_3_attribute_with_arg(project):
    """Pattern 3: ``@graph.ingress.kind('arg_name')``."""

    @project_kinds.ingress.local_proj_folder('project_path')
    def analyze(project_path: str, depth: int = 1):
        return project_path, depth

    resolved, depth = analyze(project.name, depth=3)

    assert Path(resolved) == project
    assert depth == 3


def test_pattern_4_attribute_first_arg(project):
    """Pattern 4: ``@graph.ingress.kind``, the cleanest syntax."""

    @project_kinds.ingress.local_proj_folder
    def analyze(project_path: str):
        return project_path

    assert Path(analyze(project.name)) == project


def test_all_input_formats(project):
    """A decorated function accepts both a project name and a full project path."""

    @project_kinds.ingress.local_proj_folder
    def get_project_folder(project_path: str):
        return Path(project_path)

    assert get_project_folder(project.name) == project
    assert get_project_folder(str(project)) == project
