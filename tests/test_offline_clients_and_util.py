"""Offline tests: the GitHub REST/GraphQL client with a fake session, and pure util helpers."""

import pytest

from hubcap import util
from hubcap.snapshot import GithubClient


class _Resp:
    def __init__(self, payload, links=None, status=200):
        self._payload, self.links, self.status = payload, links or {}, status

    def raise_for_status(self):
        if self.status >= 400:
            raise RuntimeError(f"HTTP {self.status}")

    def json(self):
        return self._payload


class _Session:
    def __init__(self, gets=(), posts=()):
        self.gets, self.posts = list(gets), list(posts)
        self.calls = []

    def get(self, url, params=None, headers=None):
        self.calls.append(("get", url, params, headers))
        return self.gets.pop(0)

    def post(self, url, json=None, headers=None):
        self.calls.append(("post", url, json, headers))
        return self.posts.pop(0)


def test_get_follows_next_links_and_sends_token():
    s = _Session(
        gets=[
            _Resp([{"full_name": "o/a"}], links={"next": {"url": "http://next"}}),
            _Resp([{"full_name": "o/b"}]),
        ]
    )
    c = GithubClient("tok", session=s)
    assert list(c.repos("o")) == ["o/a", "o/b"]
    assert s.calls[0][3] == {"Authorization": "Bearer tok"}
    assert s.calls[0][2]["per_page"] == 100
    assert s.calls[1][1] == "http://next" and s.calls[1][2] == {}


def test_issues_since_and_comments_for_prs():
    s = _Session(gets=[_Resp([{"number": 1}])])
    c = GithubClient("t", session=s)
    assert list(c.issues("o/r", "2026-01-01")) == [{"number": 1}]
    assert s.calls[0][2]["since"] == "2026-01-01"

    s = _Session(gets=[_Resp([{"id": 1}]), _Resp([{"id": 2}])])
    c = GithubClient("t", session=s)
    got = list(c.comments("o/r", {"number": 5, "pull_request": {}}))
    assert got == [{"id": 1}, {"id": 2}]
    assert s.calls[1][1].endswith("/pulls/5/comments")


def test_graphql_error_raises():
    s = _Session(posts=[_Resp({"errors": ["boom"]})])
    with pytest.raises(RuntimeError, match="GraphQL errors"):
        GithubClient("t", session=s)._graphql("query")


def _disc(number, updated, more=False):
    return {
        "number": number,
        "updatedAt": updated,
        "comments": {
            "nodes": [{"id": "c1"}],
            "pageInfo": {"hasNextPage": more, "endCursor": "x"},
        },
    }


def test_discussions_paginate_and_stop_at_since():
    page = {
        "repository": {
            "discussions": {
                "nodes": [_disc(2, "2026-03-01", more=True), _disc(1, "2025-01-01")],
                "pageInfo": {"hasNextPage": False, "endCursor": None},
            }
        }
    }
    more = {
        "repository": {
            "discussion": {
                "comments": {
                    "nodes": [{"id": "c2"}],
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                }
            }
        }
    }
    s = _Session(posts=[_Resp({"data": page}), _Resp({"data": more})])
    out = list(GithubClient("t", session=s).discussions("o/r", "2026-01-01"))
    assert [d["number"] for d in out] == [2]  # the older one stops the scan
    assert [c["id"] for c in out[0]["comments_data"]] == ["c1", "c2"]


def test_token_and_session_are_lazy(monkeypatch):
    c = GithubClient()
    assert c._session is None and c._token is None
    assert c.session is c.session
    monkeypatch.setattr("hubcap.tools._require_github_token", lambda: "zzz")
    assert c.token == "zzz"


def test_url_helpers():
    sep = util.path_sep
    assert util.ensure_slash_suffix("a") == "a" + sep
    assert util.ensure_slash_suffix("a" + sep) == "a" + sep
    assert util.ensure_no_slash_suffix("a" + sep * 2) == "a"
    assert util.ensure_url_suffix("https://github.com/o/r/") == "o/r"
    assert util.ensure_full_name("github.com/o/r") == "o/r"
    with pytest.raises(ValueError):
        util.ensure_full_name("o/r/extra")
    assert util.ensure_github_url("o/r") == "https://github.com/o/r"


def test_folder_to_clone_into(tmp_path):
    assert util.ensure_folder_to_clone_into(str(tmp_path)) == str(tmp_path)
    import os

    assert os.path.isdir(util.ensure_folder_to_clone_into())


def test_parse_and_generate_github_url_roundtrip():
    p = util.parse_github_url("https://github.com/o/r/blob/main/a/b.py")
    assert p["url_type"] == "file" and p["path"] == "a/b.py"
    assert "url_type" not in util.parse_github_url(
        "https://github.com/o/r", include_url_type=False
    )
    with pytest.raises(ValueError):
        util.parse_github_url("https://example.com/nothing")


def test_raise_if_error_and_itemgetter():
    assert util._raise_if_error({"data": 1}) == {"data": 1}
    with pytest.raises(RuntimeError, match="a\nb"):
        util._raise_if_error({"errors": [{"message": "a"}, {"message": "b"}]})
    assert util.defaulted_itemgetter({"k": 1}, "k", 0) == 1
    assert util.defaulted_itemgetter({}, "k", 0) == 0
