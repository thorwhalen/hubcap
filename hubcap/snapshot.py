"""Incremental snapshot of GitHub orgs: issues, PRs and discussions with all comments.

``snapshot_github(["my-org"], store=...)`` writes, per item, a markdown file with front
matter, plus ``index.jsonl`` (one line per item) and ``raw.jsonl`` (the API payloads).
Re-runs are cheap: a per-repo ``updated_at`` high-water mark is kept in a *state* store
and only newer items are fetched.

Three seams, each one keyword argument:

- ``client``: where the data comes from (default :class:`GithubClient`, REST +
  GraphQL via ``requests``). Anything with the same four methods works, which is also
  how the tests run offline.
- ``store``: where files go, any ``MutableMapping[str, str]`` (default: a folder, via
  ``dol.TextFiles``).
- ``render``: ``(kind, repo, item) -> str``, the markdown strategy.

>>> render_markdown('issues', 'o/r', {'number': 1, 'title': 'T', 'body': 'B',
...     'state': 'open', 'user': {'login': 'u'}, 'updated_at': '2026-01-01T00:00:00Z',
...     'html_url': 'u', 'comments_data': []}).startswith('---')
True
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable, Iterator, MutableMapping
from typing import Any, Optional, Protocol

KINDS = ("issues", "pulls", "discussions")
INDEX_KEY = "index.jsonl"
RAW_KEY = "raw.jsonl"
STATE_KEY = "since"
API_ROOT = "https://api.github.com"
PER_PAGE = 100

_DISCUSSIONS_QUERY = """
query($owner: String!, $name: String!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    discussions(first: 25, after: $cursor, orderBy: {field: UPDATED_AT, direction: DESC}) {
      pageInfo { hasNextPage endCursor }
      nodes {
        number title body url createdAt updatedAt author { login }
        category { name }
        comments(first: 50) {
          pageInfo { hasNextPage endCursor }
          nodes {
            id body createdAt author { login }
            replies(first: 50) { nodes { body createdAt author { login } } }
          }
        }
      }
    }
  }
}
"""

_MORE_COMMENTS_QUERY = """
query($owner: String!, $name: String!, $number: Int!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    discussion(number: $number) {
      comments(first: 50, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id body createdAt author { login }
          replies(first: 50) { nodes { body createdAt author { login } } }
        }
      }
    }
  }
}
"""


class SnapshotClient(Protocol):
    """What :func:`snapshot_github` needs from GitHub. Implement it to go offline."""

    def repos(self, org: str) -> Iterable[str]:
        """Full names (``org/name``) of the org's repositories."""

    def issues(self, repo: str, since: str) -> Iterable[dict]:
        """Issues *and* PRs (PRs carry a ``pull_request`` key) updated since *since*."""

    def comments(self, repo: str, item: dict) -> Iterable[dict]:
        """Comments of an issue/PR; for PRs also review comments (``path`` set)."""

    def discussions(self, repo: str, since: str) -> Iterable[dict]:
        """Discussions updated since *since*, each with nested ``comments_data``."""


class GithubClient:
    """The default client: REST for issues/PRs, GraphQL for discussions.

    The token is resolved lazily from the usual env vars (see
    :func:`hubcap.tools.get_github_token`); constructing the client needs none.
    """

    def __init__(self, token: Optional[str] = None, *, session=None):
        self._token = token
        self._session = session

    @property
    def session(self):
        if self._session is None:
            import requests

            self._session = requests.Session()
        return self._session

    @property
    def token(self) -> str:
        if self._token is None:
            from hubcap.tools import _require_github_token

            self._token = _require_github_token()
        return self._token

    def _get(self, path: str, **params) -> Iterator[dict]:
        url: Optional[str] = f"{API_ROOT}{path}"
        params = {"per_page": PER_PAGE, **params}
        while url:
            r = self.session.get(
                url,
                params=params,
                headers={"Authorization": f"Bearer {self.token}"},
            )
            r.raise_for_status()
            yield from r.json()
            url = r.links.get("next", {}).get("url")
            params = {}  # the next link already carries them

    def _graphql(self, query: str, **variables) -> dict:
        r = self.session.post(
            f"{API_ROOT}/graphql",
            json={"query": query, "variables": variables},
            headers={"Authorization": f"Bearer {self.token}"},
        )
        r.raise_for_status()
        data = r.json()
        if data.get("errors"):
            raise RuntimeError(f"GraphQL errors: {data['errors']}")
        return data["data"]

    def repos(self, org):
        for r in self._get(f"/orgs/{org}/repos", type="all"):
            yield r["full_name"]

    def issues(self, repo, since):
        params = dict(state="all", sort="updated", direction="asc")
        if since:
            params["since"] = since
        yield from self._get(f"/repos/{repo}/issues", **params)

    def comments(self, repo, item):
        n = item["number"]
        yield from self._get(f"/repos/{repo}/issues/{n}/comments")
        if "pull_request" in item:
            yield from self._get(f"/repos/{repo}/pulls/{n}/comments")

    def discussions(self, repo, since):
        owner, name = repo.split("/", 1)
        cursor = None
        while True:
            page = self._graphql(
                _DISCUSSIONS_QUERY, owner=owner, name=name, cursor=cursor
            )["repository"]["discussions"]
            for d in page["nodes"]:
                if since and d["updatedAt"] <= since:
                    return  # ordered newest-first: everything after is older
                d["comments_data"] = self._all_discussion_comments(owner, name, d)
                yield d
            if not page["pageInfo"]["hasNextPage"]:
                return
            cursor = page["pageInfo"]["endCursor"]

    def _all_discussion_comments(self, owner, name, discussion) -> list[dict]:
        comments = list(discussion["comments"]["nodes"])
        info = discussion["comments"]["pageInfo"]
        while info["hasNextPage"]:
            page = self._graphql(
                _MORE_COMMENTS_QUERY,
                owner=owner,
                name=name,
                number=discussion["number"],
                cursor=info["endCursor"],
            )["repository"]["discussion"]["comments"]
            comments += page["nodes"]
            info = page["pageInfo"]
        return comments


# --- Rendering -----------------------------------------------------------------


def _login(obj: Optional[dict]) -> str:
    return (obj or {}).get("login") or "ghost"


def _author(item: dict) -> str:
    return _login(item.get("user") or item.get("author"))


def _comment_block(c: dict, *, indent: int = 0) -> str:
    where = f" on `{c['path']}`" if c.get("path") else ""
    head = f"**{_author(c)}**{where} ({c.get('created_at') or c.get('createdAt', '')})"
    body = (c.get("body") or "").strip()
    out = [f"{head}\n\n{body}\n"]
    for reply in (c.get("replies") or {}).get("nodes", []):
        out.append(_comment_block(reply, indent=indent + 1))
    text = "\n".join(out)
    return "\n".join(("> " * indent) + line for line in text.splitlines()) if indent else text


def render_markdown(kind: str, repo: str, item: dict) -> str:
    """Markdown with front matter for one issue, PR or discussion (default renderer)."""
    title = str(item.get("title") or "").replace('"', "'")
    front = {
        "repo": repo,
        "kind": kind,
        "number": item["number"],
        "title": f'"{title}"',
        "state": item.get("state") or (item.get("category") or {}).get("name", ""),
        "author": _author(item),
        "updated_at": item.get("updated_at") or item.get("updatedAt", ""),
        "url": item.get("html_url") or item.get("url", ""),
    }
    lines = ["---", *(f"{k}: {v}" for k, v in front.items()), "---", ""]
    lines += [f"# {item.get('title') or ''}", "", (item.get("body") or "").strip(), ""]
    comments = item.get("comments_data") or []
    if comments:
        lines += ["## Comments", ""]
        lines += [_comment_block(c) for c in comments]
    return "\n".join(lines) + "\n"


# --- The snapshot ---------------------------------------------------------------


def _item_updated(item: dict) -> str:
    return item.get("updated_at") or item.get("updatedAt") or ""


def _default_store(root: str) -> MutableMapping:
    from dol import TextFiles

    return TextFiles(root)


def snapshot_github(
    targets: Iterable[str],
    *,
    store: MutableMapping | str = "github_snapshot",
    state: Optional[MutableMapping] = None,
    client: Optional[SnapshotClient] = None,
    render: Callable[[str, str, dict], str] = render_markdown,
    kinds: Iterable[str] = KINDS,
    full: bool = False,
) -> dict[str, int]:
    """Snapshot every repo of the given orgs (``"org"``) or repos (``"org/name"``).

    :param store: a ``MutableMapping[str, str]`` or a folder path (default folder
        ``github_snapshot``). Keys are ``<repo>/<kind>/<number>.md`` plus
        ``raw/<repo>/<kind>/<number>.json``, ``index.jsonl`` and ``raw.jsonl``.
    :param state: where the per-repo ``updated_at`` marks live; defaults to a
        ``.state.json`` entry inside *store*, so the folder is self-contained.
    :param full: ignore the marks and refetch everything.
    :return: counts of items written per kind.

    The state mark is advanced only after a repo's items were all written, so a crash
    re-fetches (idempotently overwriting) rather than skipping.
    """
    if isinstance(store, str):
        store = _default_store(store)
    client = client or GithubClient()
    state = store if state is None else state
    state_key = ".state.json"
    marks: dict[str, dict[str, str]] = {}
    if not full and state_key in state:
        marks = json.loads(state[state_key])
    index: dict[str, dict] = {}
    if INDEX_KEY in store:
        index = {
            e["key"]: e
            for e in map(json.loads, filter(None, store[INDEX_KEY].splitlines()))
        }
    kinds = tuple(kinds)
    counts = {k: 0 for k in kinds}

    repos: list[str] = []
    for target in targets:
        repos += [target] if "/" in target else list(client.repos(target))

    for repo in repos:
        repo_marks = marks.setdefault(repo, {})

        def write(kind: str, item: dict) -> None:
            key = f"{repo}/{kind}/{item['number']}"
            store[f"{key}.md"] = render(kind, repo, item)
            store[f"raw/{key}.json"] = json.dumps(item, sort_keys=True)
            index[key] = dict(
                key=key,
                repo=repo,
                kind=kind,
                number=item["number"],
                title=item.get("title"),
                updated_at=_item_updated(item),
            )
            counts[kind] += 1

        if "issues" in kinds or "pulls" in kinds:
            since = repo_marks.get("issues", "")
            newest = since
            for issue in client.issues(repo, since):
                kind = "pulls" if "pull_request" in issue else "issues"
                newest = max(newest, _item_updated(issue))
                if kind not in kinds:
                    continue
                issue = {**issue, "comments_data": list(client.comments(repo, issue))}
                write(kind, issue)
            repo_marks["issues"] = newest
        if "discussions" in kinds:
            since = repo_marks.get("discussions", "")
            newest = since
            for d in client.discussions(repo, since):
                newest = max(newest, _item_updated(d))
                write("discussions", d)
            repo_marks["discussions"] = newest
        state[state_key] = json.dumps(marks, sort_keys=True)

    store[INDEX_KEY] = "".join(json.dumps(e) + "\n" for e in index.values())
    store[RAW_KEY] = "".join(
        store[f"raw/{key}.json"] + "\n" for key in index if f"raw/{key}.json" in store
    )
    return counts
