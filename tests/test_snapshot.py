"""Offline tests for hubcap.snapshot: a fake client stands in for GitHub."""

import json

from hubcap.snapshot import snapshot_github


class FakeClient:
    def __init__(self):
        self.issue_calls = []
        self.items = [
            {"number": 1, "title": "bug", "body": "b", "state": "open",
             "user": {"login": "ann"}, "updated_at": "2026-01-01T00:00:00Z",
             "html_url": "https://x/1"},
            {"number": 2, "title": "pr", "body": "p", "state": "open",
             "pull_request": {}, "user": {"login": "bob"},
             "updated_at": "2026-01-02T00:00:00Z", "html_url": "https://x/2"},
        ]

    def repos(self, org):
        return [f"{org}/a"]

    def issues(self, repo, since):
        self.issue_calls.append(since)
        return [i for i in self.items if i["updated_at"] > since]

    def comments(self, repo, item):
        if item["number"] == 2:
            return [{"body": "nit", "user": {"login": "cy"}, "path": "f.py",
                     "created_at": "t"}]
        return []

    def discussions(self, repo, since):
        return [{"number": 3, "title": "d", "body": "db", "updatedAt": "2026-01-03T00:00:00Z",
                 "url": "https://x/3", "author": {"login": "di"}, "category": {"name": "Q"},
                 "comments_data": [{"body": "top", "author": {"login": "e"}, "createdAt": "t",
                                    "replies": {"nodes": [{"body": "re", "author": {"login": "f"},
                                                           "createdAt": "t"}]}}]}
                ] if since < "2026-01-03T00:00:00Z" else []


def test_snapshot_writes_markdown_index_and_raw():
    store, client = {}, FakeClient()
    counts = snapshot_github(["org"], store=store, client=client)
    assert counts == {"issues": 1, "pulls": 1, "discussions": 1}
    assert "org/a/issues/1.md" in store and "org/a/pulls/2.md" in store
    assert "on `f.py`" in store["org/a/pulls/2.md"]
    md = store["org/a/discussions/3.md"]
    assert "top" in md and "re" in md
    assert len(store["index.jsonl"].splitlines()) == 3
    assert all(json.loads(l) for l in store["raw.jsonl"].splitlines())


def test_rerun_is_incremental():
    store, client = {}, FakeClient()
    snapshot_github(["org/a"], store=store, client=client)
    counts = snapshot_github(["org/a"], store=store, client=client)
    assert client.issue_calls[-1] == "2026-01-02T00:00:00Z"
    assert counts == {"issues": 0, "pulls": 0, "discussions": 0}
    assert len(store["index.jsonl"].splitlines()) == 3  # earlier items stay indexed


def test_full_refetches_everything():
    store, client = {}, FakeClient()
    snapshot_github(["org/a"], store=store, client=client)
    counts = snapshot_github(["org/a"], store=store, client=client, full=True)
    assert counts["issues"] == 1 and counts["pulls"] == 1
