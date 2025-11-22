# Flexible Project Reference Casting

The `hubcap.casting` module provides automatic conversion between different representations of GitHub projects using a transformation graph powered by `i2.castgraph`.

## Quick Start

### 1. Register Your Project Roots

First, tell hubcap where your local projects are:

```python
from hubcap.casting import register_project_root

register_project_root('/Users/me/projects')
register_project_root('/Users/me/work/repos')
```

Or use the helper if you're using priv:

```bash
python -m priv.setup_hubcap_casting
```

### 2. Use Flexible Inputs

Now all these work interchangeably:

```python
from hubcap.casting import to_local_path, to_github_url, to_github_stub

# Simple project name
to_local_path("dol")  
# → '/Users/me/projects/dol'

# GitHub stub (org/repo)
to_local_path("i2mint/dol")
# → '/Users/me/projects/dol'

# HTTPS URL
to_local_path("https://github.com/i2mint/dol")
# → '/Users/me/projects/dol'

# SSH URL  
to_local_path("git@github.com:i2mint/dol.git")
# → '/Users/me/projects/dol'

# Convert to GitHub URL
to_github_url("dol", ssh=True)
# → 'git@github.com:i2mint/dol.git'

to_github_url("dol", ssh=False)  
# → 'https://github.com/i2mint/dol'

# Get org/repo stub
to_github_stub("https://github.com/i2mint/dol/tree/master")
# → 'i2mint/dol'
```

## Supported Kinds

The transformation graph supports these kinds of project references:

| Kind | Example | Description |
|------|---------|-------------|
| `proj_name` | `"dol"` | Simple project name |
| `github_stub` | `"i2mint/dol"` | Org/repo format |
| `github_https_url` | `"https://github.com/i2mint/dol"` | HTTPS URL |
| `github_ssh_url` | `"git@github.com:i2mint/dol.git"` | SSH URL |
| `local_proj_folder` | `"/Users/me/projects/dol"` | Local filesystem path |
| `local_git_folder` | `"/Users/me/projects/dol"` | Alias for local_proj_folder |
| `url_components` | `{'username': 'i2mint', 'repository': 'dol'}` | Parsed URL dict |

## Using the Ingress Decorator

The `ingress` decorator automatically converts function arguments to the required type. It supports four different usage patterns:

### Pattern 1: Kind with explicit argument name

```python
from hubcap.casting import project_kinds

@project_kinds.ingress('local_proj_folder', 'project_path')
def analyze_project(project_path: str, depth: int = 1):
    """Transform the 'project_path' argument specifically."""
    with open(f"{project_path}/README.md") as f:
        return f.read()
```

### Pattern 2: Kind only (transforms first argument)

```python
@project_kinds.ingress('local_proj_folder')
def analyze_project(project_path: str):
    """Accepts any project reference, gets local path automatically."""
    # project_path is now guaranteed to be a local folder path
    with open(f"{project_path}/README.md") as f:
        return f.read()
```

### Pattern 3: Attribute syntax with argument name

```python
@project_kinds.ingress.local_proj_folder('project_path')
def analyze_project(project_path: str, depth: int = 1):
    """Uses attribute access for better IDE autocomplete."""
    with open(f"{project_path}/README.md") as f:
        return f.read()
```

### Pattern 4: Attribute syntax on first argument

```python
@project_kinds.ingress.local_proj_folder
def analyze_project(project_path: str):
    """Cleanest syntax when transforming the first argument."""
    with open(f"{project_path}/README.md") as f:
        return f.read()
```

All patterns accept any project reference format:

```python
# All these work with any of the decorator patterns above:
analyze_project("dol")
analyze_project("i2mint/dol")  
analyze_project("https://github.com/i2mint/dol")
analyze_project("/Users/me/projects/dol")
```

**Tip**: Use attribute syntax (Pattern 3 or 4) when you want IDE autocomplete for available kinds.

### Advanced: Passing Context

You can pass context information through transformations:

```python
@project_kinds.ingress('github_https_url', context={'include_branch': True})
def get_project_url(url: str):
    """Context is passed to transformation functions if needed."""
    return url
```

## Advanced: Direct Transformation

For custom transformations, use `normalize_project`:

```python
from hubcap.casting import normalize_project

# Convert to any kind
normalize_project("dol", to_kind='github_stub')
# → 'i2mint/dol'

normalize_project("dol", to_kind='url_components')
# → {'username': 'i2mint', 'repository': 'dol'}

normalize_project(
    "git@github.com:i2mint/dol.git", 
    to_kind='github_https_url'
)
# → 'https://github.com/i2mint/dol'
```

## Configuration

Project roots are stored in hubcap's configuration:

```python
from hubcap.casting import get_project_roots, unregister_project_root

# View registered roots
print(get_project_roots())

# Remove a root
unregister_project_root('/Users/me/old/path')
```

## How It Works

1. **Registration**: You register root folders containing your projects
2. **Discovery**: The system looks one level deep for folders with `.git`
3. **Transformation**: A graph of conversion functions connects all the kinds
4. **Automatic**: Input type is detected and converted to what you need

The transformation graph automatically:
- Detects input format using predicates
- Finds the shortest path to the target format
- Applies necessary transformations
- Caches results for performance

## Integration with git_ops

The `priv.git_ops` module now uses hubcap's casting for all project references:

```python
from priv.git_ops import local_path_for_project, github_url_for

# All these work:
local_path_for_project("dol")
local_path_for_project("i2mint/dol")
local_path_for_project("https://github.com/i2mint/dol")
```
