# Hubcap Caching Feature - Complete Guide

## Overview

Hubcap now includes a comprehensive caching mechanism for repository artifacts. This feature allows you to work with GitHub data locally without repeatedly fetching from the API, improving performance and reducing API rate limit concerns.

## Quick Start

```python
from hubcap import local_repo_artifacts

# Access cached repository info
info = local_repo_artifacts.info['thorwhalen/hubcap']
print(info['name'])  # 'hubcap'

# Access cached discussions
discussions = local_repo_artifacts.discussions['thorwhalen/hubcap']
for num, discussion in discussions.items():
    print(f"{num}: {discussion['title']}")

# Access cached issues
issues = local_repo_artifacts.issues['thorwhalen/hubcap']
for num, issue in issues.items():
    print(f"{num}: {issue['title']}")
```

## Architecture

### Core Components

1. **Caching in Discussions Class** (`hubcap/util.py`)
   - Added `cache` and `refresh` parameters
   - Stores data in `{cache_dir}/{org}/{repo}/discussions/{number}.json`

2. **Caching in Issues Class** (`hubcap/base.py`)
   - Added `cache` and `refresh` parameters
   - Stores data in `{cache_dir}/{org}/{repo}/issues/{number}.json`

3. **LocalRepoArtifacts Class** (`hubcap/tools.py`)
   - Provides unified interface to all cached artifacts
   - Three main attributes: `info`, `discussions`, `issues`
   - Each attribute is a mapping interface

### Mapping Hierarchy

```
LocalRepoArtifacts
├── .info: _RepoInfoMapping
│   └── ['org/repo'] → dict (info.json)
├── .discussions: _DiscussionsMapping
│   └── ['org/repo'] → dict[int, dict]
│       └── [discussion_number] → dict
└── .issues: _IssuesMapping
    └── ['org/repo'] → dict[int, dict]
        └── [issue_number] → dict
```

## Usage Patterns

### Pattern 1: Using local_repo_artifacts (Recommended)

```python
from hubcap import local_repo_artifacts

# Default instance uses cache without refresh
info = local_repo_artifacts.info['thorwhalen/hubcap']
discussions = local_repo_artifacts.discussions['thorwhalen/hubcap']
issues = local_repo_artifacts.issues['thorwhalen/hubcap']
```

### Pattern 2: Custom LocalRepoArtifacts Instance

```python
from hubcap import LocalRepoArtifacts

# Always fetch fresh data
fresh = LocalRepoArtifacts(refresh=True)
info = fresh.info['thorwhalen/hubcap']

# Use cached data only
cached = LocalRepoArtifacts(refresh=False)
info = cached.info['thorwhalen/hubcap']
```

### Pattern 3: Direct Class Usage

```python
from hubcap import Discussions, Issues

# Discussions with caching
discussions = Discussions(
    'thorwhalen/hubcap',
    cache=True,      # Enable caching
    refresh=False    # Use cached data when available
)
discussion = discussions[2]

# Issues with caching and refresh
issues = Issues(
    'thorwhalen/hubcap',
    cache=True,      # Enable caching
    refresh=True,    # Always fetch fresh data
    get_objs_kwargs=(('state', 'all'),)  # Fetch all issues
)
issue = issues[3]
```

## Cache Behavior

### The `refresh` Parameter

- `refresh=False` (default for `local_repo_artifacts`)
  - Checks cache first
  - Only fetches from GitHub if cache doesn't exist
  - Fast, but may return stale data

- `refresh=True`
  - Always fetches from GitHub
  - Updates cache with fresh data
  - Slower, but ensures up-to-date data

### The `cache` Parameter

- `cache=False` (default for Discussions/Issues)
  - No caching, always fetch from GitHub
  - No local storage

- `cache=True`
  - Enables local storage
  - Respects `refresh` parameter for fetch behavior

## Cache Location

### Default Location

- **Linux/Mac**: `~/.local/share/hubcap/repos/`
- **Windows**: `%LOCALAPPDATA%\hubcap\repos\`

### Custom Location

Set the `HUBCAP_DATA_FOLDER` environment variable:

```bash
export HUBCAP_DATA_FOLDER="/path/to/custom/cache"
```

### Structure

```
repos/
└── {org}/
    └── {repo}/
        ├── info.json
        ├── discussions/
        │   ├── 1.json
        │   ├── 2.json
        │   └── ...
        └── issues/
            ├── 3.json
            ├── 4.json
            └── ...
```

## API Reference

### LocalRepoArtifacts

```python
class LocalRepoArtifacts:
    """Provides mapping interfaces to locally cached repository artifacts."""
    
    def __init__(self, refresh: bool = False):
        """
        Args:
            refresh: If True, always fetch fresh data from GitHub.
                    If False, use cached data when available.
        """
```

**Attributes:**
- `info`: Mapping of `repo_name → info_dict`
- `discussions`: Mapping of `repo_name → discussions_dict`
- `issues`: Mapping of `repo_name → issues_dict`

### Discussions

```python
class Discussions(KvReader):
    def __init__(
        self,
        repo: RepoSpec,
        *,
        token: str | None = None,
        discussion_fields: tuple[str] = DFLT_DISCUSSION_FIELDS,
        cache: bool = False,
        refresh: bool = True,
        # ... other parameters
    ):
        """
        Args:
            repo: Repository identifier (e.g., 'org/repo')
            cache: Enable local caching
            refresh: If True, always fetch fresh data
        """
```

### Issues

```python
class Issues(RepoObjects):
    def __init__(
        self,
        repo: RepoSpec,
        *,
        cache: bool = False,
        refresh: bool = True,
        # ... other parameters
    ):
        """
        Args:
            repo: Repository identifier (e.g., 'org/repo')
            cache: Enable local caching
            refresh: If True, always fetch fresh data
        """
```

## Examples

### Example 1: Batch Processing with Cache

```python
from hubcap import LocalRepoArtifacts

# First run: fetches and caches data
artifacts = LocalRepoArtifacts(refresh=True)
repos = ['i2mint/dol', 'i2mint/creek', 'thorwhalen/hubcap']

for repo in repos:
    info = artifacts.info[repo]
    print(f"{repo}: {info['stargazers_count']} stars")

# Second run: uses cached data (much faster!)
cached = LocalRepoArtifacts(refresh=False)
for repo in repos:
    info = cached.info[repo]
    print(f"{repo}: {info['stargazers_count']} stars")
```

### Example 2: Periodic Refresh

```python
from hubcap import local_repo_artifacts, LocalRepoArtifacts
import time

# Use cached data for quick access
info = local_repo_artifacts.info['thorwhalen/hubcap']
print(f"Cached stargazers: {info['stargazers_count']}")

# Periodically refresh for updates
time.sleep(3600)  # Wait 1 hour
fresh = LocalRepoArtifacts(refresh=True)
info = fresh.info['thorwhalen/hubcap']
print(f"Fresh stargazers: {info['stargazers_count']}")
```

### Example 3: Discussion Analysis

```python
from hubcap import Discussions

# Cache discussions for offline analysis
discussions = Discussions(
    'thorwhalen/hubcap',
    cache=True,
    refresh=True  # Get latest discussions
)

# Analyze cached discussions
for num in discussions:
    discussion = discussions[num]
    comment_count = len(discussion.get('comments', []))
    print(f"Discussion {num}: {comment_count} comments")
```

## Performance Tips

1. **Use caching for repeated access**: Set `cache=True` when you'll access the same data multiple times
2. **Batch operations with refresh**: Use `refresh=True` once to update cache, then `refresh=False` for subsequent reads
3. **Monitor cache size**: The cache directory can grow large with many repositories
4. **Clear stale cache**: Manually delete old cache files when needed

## Troubleshooting

### Issue: Stale data being returned

**Solution**: Use `refresh=True` to force fresh fetch

```python
fresh = LocalRepoArtifacts(refresh=True)
info = fresh.info['org/repo']
```

### Issue: Cache not being created

**Solution**: Verify cache directory permissions

```python
from hubcap.util import repo_cache_dir
import os
print(f"Cache dir: {repo_cache_dir}")
print(f"Writable: {os.access(repo_cache_dir, os.W_OK)}")
```

### Issue: API rate limit errors

**Solution**: Use cached data to reduce API calls

```python
cached = LocalRepoArtifacts(refresh=False)
# This won't hit GitHub API if cache exists
info = cached.info['org/repo']
```

## Design Philosophy

The caching implementation follows these principles:

1. **Opt-in**: Caching is optional, default behavior unchanged
2. **Explicit control**: `cache` and `refresh` parameters provide clear control
3. **Mapping interface**: Consistent dict-like access pattern
4. **Modular**: Each artifact type independently cacheable
5. **SSOT**: Single source for cache configuration and location
6. **Backwards compatible**: Existing code continues to work without changes
