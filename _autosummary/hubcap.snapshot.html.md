# hubcap.snapshot

Incremental snapshot of GitHub orgs: issues, PRs and discussions with all comments.

`snapshot_github(["my-org"], store=...)` writes, per item, a markdown file with front
matter, plus `index.jsonl` (one line per item) and `raw.jsonl` (the API payloads).
Re-runs are cheap: a per-repo `updated_at` high-water mark is kept in a *state* store
and only newer items are fetched.

Three seams, each one keyword argument:

- `client`: where the data comes from (default [`GithubClient`](#hubcap.snapshot.GithubClient), REST +
  GraphQL via `requests`). Anything with the same four methods works, which is also
  how the tests run offline.
- `store`: where files go, any `MutableMapping[str, str]` (default: a folder, via
  `dol.TextFiles`).
- `render`: `(kind, repo, item) -> str`, the markdown strategy.

```pycon
>>> render_markdown('issues', 'o/r', {'number': 1, 'title': 'T', 'body': 'B',
...     'state': 'open', 'user': {'login': 'u'}, 'updated_at': '2026-01-01T00:00:00Z',
...     'html_url': 'u', 'comments_data': []}).startswith('---')
True
```

### Functions

| [`render_markdown`](#hubcap.snapshot.render_markdown)(kind, repo, item)                 | Markdown with front matter for one issue, PR or discussion (default renderer).   |
|----------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------|
| [`snapshot_github`](#hubcap.snapshot.snapshot_github)(targets, \*[, store, state, ...]) | Snapshot every repo of the given orgs (`"org"`) or repos (`"org/name"`).         |

### Classes

| [`GithubClient`](#hubcap.snapshot.GithubClient)([token, session])     | The default client: REST for issues/PRs, GraphQL for discussions.                          |
|-------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------|
| [`SnapshotClient`](#hubcap.snapshot.SnapshotClient)(\*args, \*\*kwargs) | What [`snapshot_github()`](#hubcap.snapshot.snapshot_github) needs from GitHub. |

### *class* hubcap.snapshot.GithubClient(token=None, , session=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

The default client: REST for issues/PRs, GraphQL for discussions.

The token is resolved lazily from the usual env vars (see
[`hubcap.tools.get_github_token()`](hubcap.tools.html.md#hubcap.tools.get_github_token)); constructing the client needs none.

### *class* hubcap.snapshot.SnapshotClient(\*args, \*\*kwargs)

Bases: [`Protocol`](https://docs.python.org/3/library/typing.html#typing.Protocol)

What [`snapshot_github()`](#hubcap.snapshot.snapshot_github) needs from GitHub. Implement it to go offline.

#### comments(repo, item)

Comments of an issue/PR; for PRs also review comments (`path` set).

* **Return type:**
  [`Iterable`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Iterable)[[`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)]

#### discussions(repo, since)

Discussions updated since *since*, each with nested `comments_data`.

* **Return type:**
  [`Iterable`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Iterable)[[`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)]

#### issues(repo, since)

Issues *and* PRs (PRs carry a `pull_request` key) updated since *since*.

* **Return type:**
  [`Iterable`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Iterable)[[`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)]

#### repos(org)

Full names (`org/name`) of the org’s repositories.

* **Return type:**
  [`Iterable`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Iterable)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

### hubcap.snapshot.render_markdown(kind, repo, item)

Markdown with front matter for one issue, PR or discussion (default renderer).

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### hubcap.snapshot.snapshot_github(targets, \*, store='github_snapshot', state=None, client=None, render=<function render_markdown>, kinds=('issues', 'pulls', 'discussions'), full=False)

Snapshot every repo of the given orgs (`"org"`) or repos (`"org/name"`).

* **Parameters:**
  * **store** ([`MutableMapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.MutableMapping) | [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – a `MutableMapping[str, str]` or a folder path (default folder
    `github_snapshot`). Keys are `<repo>/<kind>/<number>.md` plus
    `raw/<repo>/<kind>/<number>.json`, `index.jsonl` and `raw.jsonl`.
  * **state** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`MutableMapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.MutableMapping)]) – where the per-repo `updated_at` marks live; defaults to a
    `.state.json` entry inside *store*, so the folder is self-contained.
  * **full** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – ignore the marks and refetch everything.
* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`int`](https://docs.python.org/3/builtins/functions.html#int)]
* **Returns:**
  counts of items written per kind.

The state mark is advanced only after a repo’s items were all written, so a crash
re-fetches (idempotently overwriting) rather than skipping.
