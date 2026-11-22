"""Offline tests of the project-reference conversions in ``hubcap.casting`` (no registry, no network)."""

import pytest

from hubcap.casting import (
    components_to_https_url,
    components_to_ssh_url,
    components_to_stub,
    git_folder_to_proj_folder,
    normalize_project,
    proj_folder_to_git_folder,
    stub_to_components,
    to_github_stub,
    to_github_url,
)

COMPONENTS = {"username": "i2mint", "repository": "dol"}


def test_stub_and_components_round_trip():
    assert stub_to_components("i2mint/dol", None) == COMPONENTS
    assert components_to_stub(COMPONENTS, None) == "i2mint/dol"


def test_stub_with_extra_slash_keeps_it_in_the_repository():
    assert stub_to_components("a/b/c", None) == {"username": "a", "repository": "b/c"}


def test_components_to_urls():
    assert components_to_https_url(COMPONENTS, None) == "https://github.com/i2mint/dol"
    assert components_to_ssh_url(COMPONENTS, None) == "git@github.com:i2mint/dol.git"


def test_identity_edges_between_local_folder_kinds():
    assert proj_folder_to_git_folder("/x", None) == "/x"
    assert git_folder_to_proj_folder("/x", None) == "/x"


@pytest.mark.parametrize(
    "project",
    [
        "i2mint/dol",
        "https://github.com/i2mint/dol/tree/master",
        "git@github.com:i2mint/dol.git",
    ],
)
def test_every_remote_form_normalizes_to_the_same_stub(project):
    assert to_github_stub(project) == "i2mint/dol"


def test_normalize_to_urls_and_components():
    assert normalize_project("i2mint/dol", to_kind="url_components") == COMPONENTS
    assert to_github_url("i2mint/dol") == "git@github.com:i2mint/dol.git"
    assert to_github_url("i2mint/dol", ssh=False) == "https://github.com/i2mint/dol"


def test_an_undetectable_reference_raises():
    with pytest.raises(Exception, match="Could not detect kind"):
        normalize_project("not a project at all ///", to_kind="github_stub")
