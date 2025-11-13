# Implementation Summary: Local Repository Artifacts Caching

## Overview
Implemented a comprehensive caching mechanism for hubcap that provides Mapping interfaces to locally cached repository artifacts (info, discussions, and issues).

## Changes Made

### 1. Added Caching to Discussions Class (hubcap/util.py)
- Added `cache` and `refresh` parameters to `Discussions.__init__()`
- When `cache=True`, data is stored in `{repo_cache_dir}/{full_name}/discussions/{number}.json`
- Updated `__getitem__()` to check cache first when `refresh=False`
- Always caches fetched data when `cache=True`

### 2. Added Caching to Issues Class (hubcap/base.py)
- Added necessary imports: `os`, `ensure_full_name`, `JsonFiles`, `repo_cache_dir`
- Added `cache` and `refresh` parameters to `Issues.__init__()`
- When `cache=True`, data is stored in `{repo_cache_dir}/{full_name}/issues/{number}.json`
- Overrode `__getitem__()` to implement cache checking and updating

### 3. Created LocalRepoArtifacts Class (hubcap/tools.py)
- `LocalRepoArtifacts` class with three mapping attributes:
  - `.info` - Maps repo full names to their info.json
  - `.discussions` - Maps repo full names to their discussions (as nested mappings)
  - `.issues` - Maps repo full names to their issues (as nested mappings)
- Created helper classes:
  - `_RepoInfoMapping` - For cached repository info
  - `_RepoArtifactMapping` - Base class for artifact mappings
  - `_DiscussionsMapping` - For cached discussions
  - `_IssuesMapping` - For cached issues
- Created default instance: `local_repo_artifacts = LocalRepoArtifacts(refresh=False)`

### 4. Updated Exports (hubcap/__init__.py)
- Exported `LocalRepoArtifacts` class
- Exported `local_repo_artifacts` instance

### 5. Updated Documentation (README.md)
- Added comprehensive "Cached Repository Artifacts" section
- Documented usage of `local_repo_artifacts`
- Explained `refresh` parameter behavior
- Documented direct caching with `Discussions` and `Issues`
- Described cache location and structure
- Added examples for all use cases

### 6. Bug Fixes
- Fixed typo in `tools.py`: changed `relpath` to `path` in `_raw_url()` function

## Usage Examples

```python
from hubcap import local_repo_artifacts, LocalRepoArtifacts, Discussions, Issues

# Use default cached artifacts (refresh=False)
info = local_repo_artifacts.info['thorwhalen/hubcap']
discussions = local_repo_artifacts.discussions['thorwhalen/hubcap']
issues = local_repo_artifacts.issues['thorwhalen/hubcap']

# Create custom instance with refresh=True
fresh = LocalRepoArtifacts(refresh=True)
fresh_info = fresh.info['thorwhalen/hubcap']

# Direct caching with Discussions
discussions = Discussions('thorwhalen/hubcap', cache=True, refresh=False)
discussion_2 = discussions[2]  # Cached after first access

# Direct caching with Issues  
issues = Issues('thorwhalen/hubcap', cache=True, refresh=True)
issue_4 = issues[4]  # Always fetches fresh and updates cache
```

## Cache Structure

```
~/.local/share/hubcap/repos/
├── thorwhalen/
│   └── hubcap/
│       ├── info.json
│       ├── discussions/
│       │   ├── 1.json
│       │   ├── 2.json
│       │   └── ...
│       └── issues/
│           ├── 4.json
│           ├── 5.json
│           └── ...
```

## Design Decisions

1. **Separation of Concerns**: Caching logic is separate from core functionality - it's opt-in via `cache=True`
2. **Flexible Refresh**: `refresh` parameter allows control over when to fetch fresh data
3. **Mapping Interface**: All artifacts accessible via familiar dict-like interface
4. **Modular Design**: Each artifact type has its own mapping class for extensibility
5. **SSOT**: Cache location defined once in `util.py` and reused everywhere
6. **Backwards Compatible**: Existing code continues to work without changes

## Testing

Created `test_caching.py` to verify:
- LocalRepoArtifacts instantiation
- Access to info, discussions, and issues
- Direct caching with Discussions and Issues classes
