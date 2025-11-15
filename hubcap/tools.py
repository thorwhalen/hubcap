"""A medley of tools for Hubcap."""

from typing import Literal
from collections.abc import Iterable
import time
from functools import partial

from hubcap.base import GithubReader, RepoReader
from hubcap.constants import repo_collection_names
from hubcap.util import RepoSpec, ensure_url_suffix, _prep_git_clone_args


# TODO: Design horribly unclean. Once RepoReader is finished, this should become
# cleaner to write.
def hub(path: RepoSpec):
    path = ensure_url_suffix(path)
    if "/" not in path:
        org = path
        return GithubReader(org)
    # at this point we have at least org/repo/...
    org, repo, *_path = path.split("/")
    if not _path:
        return GithubReader(org)[repo]

    # If not, use RepoReader as the base object  # TODO: Finish RepoReader
    s = RepoReader(f"{org}/{repo}")
    path_iter = iter(_path)
    # TODO: Temporarily commented out -- if not needed, remove
    # if (repo := next(path_iter, None)) is not None:
    #     s = s[repo]
    if (resource := next(path_iter, None)) is not None:
        if resource in repo_collection_names or resource == "discussions":
            s = RepoReader(s.repo)[resource]
        else:
            # From now we assume the intent is to get a specific branch...
            if resource == "tree":  # this is to be consistent with browser url access
                # then consider this to be a request for branches
                resource = next(path_iter)
            else:
                # TODO: Change what s is suddenly: Terrible design
                # The point here is that the following instance will then work for
                # getting the branch
                s = GithubReader(org)[repo]
            s = s[resource]

    # Process the rest of the path with the s mapping
    for part in path_iter:
        s = s[part]
    return s


def team_repositories_action(
    repositories: Iterable[str],
    team: str,
    *,
    action: Literal["add_to_repo", "remove_from_repos"],
    org: str,
    wait_s: int = 1,
):
    """
    Add a list of repositories to a team with read permission
    """
    # Create a GitHub instance using an access token
    g = GithubReader()._github

    # Get the organization object by name
    org_ = g.get_organization(org)

    # Get the team object by name
    team_ = org_.get_team_by_slug(team)
    action_ = getattr(team_, action)

    for repo in repositories:
        # Get the repository object by name
        repo_ = g.get_repo(repo)
        # Carry out the action
        action_(repo_)
        time.sleep(wait_s)


add_repos_to_team = partial(team_repositories_action, action="add_to_repo")
rm_repos_from_team = partial(team_repositories_action, action="remove_from_repos")


# --------------------------------------------------------------------------------------
# Get markdown aggregate from GitHub repositories
from functools import partial
from types import SimpleNamespace
from hubcap.repo_slurp import repo_text_aggregate

github_repo_markdown_of = SimpleNamespace(
    files=partial(repo_text_aggregate, kinds=["files"]),
    discussions=partial(repo_text_aggregate, kinds=["discussions"]),
    issues=partial(repo_text_aggregate, kinds=["issues"]),
    wikis=partial(repo_text_aggregate, kinds=["wikis"]),
)
github_repo_markdown_of.__doc__ = (
    "Holds functions to get markdown aggregate from GitHub repositories.\n\n"
    "Example usage:\n\n"
    ">>> github_repo_markdown_of.files('thorwhalen/hubcap')  # doctest: +SKIP\n"
    ">>> github_repo_markdown_of.issues('thorwhalen/hubcap')  # doctest: +SKIP\n"
)


# --------------------------------------------------------------------------------------
# Converting notebooks to Markdown and cleaning them up

from typing import Optional, Union
from pathlib import Path
import re
from warnings import warn

from hubcap.util import replace_relative_urls, generate_github_url


def _raw_url(org, repo, branch="main", path=""):
    components = {
        "username": org,
        "repository": repo,
        "branch": branch,
        "path": path,
    }
    return generate_github_url(components, "fully_qualified_raw")
    # return (
    #     f'https://raw.githubusercontent.com/{repo_stub}/refs/heads/{branch}/{relpath}'
    # )


def _handle_repo_root_url(repo_root_url, image_relative_dir=""):
    # url join repo_root_url and image_relative_dir
    if image_relative_dir:
        repo_root_url = f"{repo_root_url.rstrip('/')}/{image_relative_dir.lstrip('/')}"

    if isinstance(repo_root_url, dict):
        return _raw_url(**repo_root_url)
    if not repo_root_url.startswith("http"):
        org, repo, branch, *relpath = repo_root_url.split("/")
        repo_stub = f"{org}/{repo}"
        return _raw_url(org, repo, branch, "/".join(relpath))
    else:
        protocol, simple_url = repo_root_url.split("://")
        if simple_url.startswith("github.com") or simple_url.startswith(
            "www.github.com"
        ):
            warn(
                f"Your repo_root_url is: {repo_root_url}. I do the work anyway, "
                "but you may want to consider that usually the URL should be a raw "
                "github URL like this: "
                "https://raw.githubusercontent.com/REPO_STUB/BRANCH/RELPATH/. "
                "Verify that the root URL you chose does work on the pypi readme page "
                "if that is what you are targeting."
            )
        return repo_root_url


# TODO: There's a same name function in hubcap.repo_slurp, as well as in contaix.markdwon and dn.src -- consolidate!!
def notebook_to_markdown(
    notebook_path: str,
    output_dir: str | None = None,
    repo_root_url: dict | str | None = None,
    *,
    image_relative_dir: str = "",
):
    """
    Convert a Jupyter notebook to Markdown and optionally post-process the output.

    Args:
        notebook_path (str): Path to the Jupyter notebook.
        output_dir (str, optional): Directory where the Markdown file will be written.
                                    If None, the Markdown is returned as a string.
        repo_root_url (str, optional): Root URL for replacing relative paths in the Markdown.
        image_relative_dir (str, optional): The (relative) directory where the images should be saved.

    Returns:
        str: The Markdown content, optionally post-processed.

    Usage Examples

    ### Convert a notebook to Markdown and return as a string

    >>> markdown_string = notebook_to_markdown(  # doctest: +SKIP
        notebook_path="example_notebook.ipynb",
        output_dir=None,  # Do not save to a file
        repo_root_url="https://github.com/username/repo/blob/main/",
        image_relative_dir="images"
    )

    ### Post-process directly from a notebook file

    >>> notebook_to_markdown = post_process_markdown_generated_from_notebook(  # doctest: +SKIP
        md_src="example_notebook.ipynb",
        repo_root_url="https://github.com/username/repo/blob/main/"
    )
    """
    from nbconvert import MarkdownExporter

    # Ensure the notebook file exists
    notebook_path = Path(notebook_path)
    if not notebook_path.exists():
        raise FileNotFoundError(f"Notebook not found: {notebook_path}")

    # Load and convert the notebook to Markdown
    markdown_exporter = MarkdownExporter()
    markdown_exporter.exclude_input_prompt = (
        True  # Optional: exclude input prompts like In[1]:
    )
    markdown_content, resources = markdown_exporter.from_filename(notebook_path)

    if repo_root_url:
        repo_root_url = _handle_repo_root_url(repo_root_url, image_relative_dir)
        markdown_content = postprocess_markdown_from_notebook(
            markdown_content, repo_root_url=repo_root_url
        )

    # Save resources (like images) to the output directory if specified
    if output_dir is not None:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save images to the directory specified in `resources`
        resource_dir = output_dir / image_relative_dir
        resource_dir.mkdir(parents=True, exist_ok=True)

        for filename, content in resources.get("outputs", {}).items():
            (resource_dir / filename).write_bytes(content)

        # Write the Markdown file
        output_filename = output_dir / f"{notebook_path.stem}.md"
        output_filename.write_text(markdown_content)
    else:
        # If no output directory is specified, images are not saved to disk.
        # You can optionally return the resources dictionary for manual handling.
        return markdown_content, resources

    return markdown_content


def postprocess_markdown_from_notebook(
    md_src: str, repo_root_url: str, md_trg: str = None
):
    """
    Post-process Markdown content generated from a notebook.

    Args:
        md_src (str): Markdown content, path to a Markdown file, or path to an ipynb file.
        repo_root_url (str): Root URL for replacing relative paths.
        md_trg (str, optional): Path to save the post-processed Markdown.

    Returns:
        str: The post-processed Markdown content.

    """
    if "\n" not in md_src and Path(md_src).exists():
        file_path = Path(md_src)
        if file_path.suffix == ".ipynb":
            # If the source is an ipynb file, convert it to Markdown
            md_src = notebook_to_markdown(file_path, output_dir=None)
        else:
            # If the source is a Markdown file, read its contents
            md_src = file_path.read_text()

    # Replace relative URLs with absolute raw URLs
    trg_str = replace_relative_urls(md_src, root_url=repo_root_url)

    # Remove unwanted artifacts
    trg_str = re.sub("<style scoped>(.*?)</style>", "", trg_str, flags=re.DOTALL)
    trg_str = re.sub(r"```python\s*```", "", trg_str, flags=re.DOTALL)

    # Save to the target file if specified
    if md_trg:
        Path(md_trg).write_text(trg_str)

    return trg_str


# --------------------------------------------------------------------------------------
# Copying discussions from one repo to another (even with private repos!)

import os
import requests
import re
import json

# --- Configuration ---
# Get your GitHub Personal Access Token from environment variable
GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"


def get_github_token():
    """Return a GitHub token from common env var names, or None if not set."""
    import os

    candidates = ("HUBCAP_GITHUB_TOKEN", "HUBCAP_TOKEN", "GH_TOKEN", "GITHUB_TOKEN")
    for name in candidates:
        token = os.getenv(name)
        if token:
            return token
    return None


# Backwards-compatible snapshot (may be None)
GITHUB_TOKEN = get_github_token()

# Existing behavior preserved: raise at import time if no token
if not GITHUB_TOKEN:
    raise OSError("GITHUB_TOKEN environment variable not set.")

# --- Helper Functions ---


def run_graphql_query(query, variables=None):
    """Executes a GraphQL query against the GitHub API."""
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {"query": query, "variables": variables or {}}
    response = requests.post(GITHUB_GRAPHQL_URL, headers=headers, json=payload)
    response.raise_for_status()  # Raise an exception for HTTP errors
    data = response.json()
    if "errors" in data:
        raise Exception(f"GraphQL errors: {data['errors']}")
    return data["data"]


def parse_github_discussion_url(discussion_url):
    """Parses a GitHub discussion URL to extract owner, repo, and discussion number."""
    match = re.match(
        r"https://github.com/([^/]+)/([^/]+)/discussions/(\d+)", discussion_url
    )
    if not match:
        raise ValueError("Invalid GitHub discussion URL format.")
    owner, repo_name, discussion_number = match.groups()
    return owner, repo_name, int(discussion_number)


def parse_github_repo_url(repo_url):
    """Parses a GitHub repository URL to extract owner and repo name."""
    match = re.match(r"https://github.com/([^/]+)/([^/]+)", repo_url)
    if not match:
        raise ValueError("Invalid GitHub repository URL format.")
    owner, repo_name = match.groups()
    return owner, repo_name


def get_repository_id(owner, repo_name):
    """Gets the GraphQL node ID of a repository."""
    query = """
    query GetRepositoryId($owner: String!, $repoName: String!) {
      repository(owner: $owner, name: $repoName) {
        id
        discussionCategories(first: 100) { # Fetch categories to aid in creating discussions
          nodes {
            id
            name
          }
        }
      }
    }
    """
    variables = {"owner": owner, "repoName": repo_name}
    data = run_graphql_query(query, variables)
    if not data or not data["repository"]:
        raise Exception(f"Repository '{owner}/{repo_name}' not found or inaccessible.")
    return data["repository"]["id"], data["repository"]["discussionCategories"]["nodes"]


def get_discussion_data(owner, repo_name, discussion_number):
    """
    Fetches the full JSON data for a discussion, including comments,
    using the GitHub GraphQL API.
    """
    query = """
    query GetDiscussion($owner: String!, $repoName: String!, $discussionNumber: Int!) {
      repository(owner: $owner, name: $repoName) {
        discussion(number: $discussionNumber) {
          title
          body
          url
          createdAt
          author {
            login
          }
          category {
            id # Category ID is needed for new discussion creation
            name
          }
          comments(first: 100) { # Adjust 'first' for more comments, use pagination if needed
            nodes {
              body
              createdAt
              author {
                login
              }
              # You can add more fields for comments if needed, e.g., reactions, url
            }
            pageInfo {
                hasNextPage
                endCursor
            }
          }
        }
      }
    }
    """
    variables = {
        "owner": owner,
        "repoName": repo_name,
        "discussionNumber": discussion_number,
    }
    data = run_graphql_query(query, variables)
    if not data or not data["repository"] or not data["repository"]["discussion"]:
        raise Exception(
            f"Discussion #{discussion_number} in '{owner}/{repo_name}' not found or inaccessible."
        )

    discussion = data["repository"]["discussion"]
    comments = discussion["comments"]["nodes"]

    # Handle pagination for comments
    while discussion["comments"]["pageInfo"]["hasNextPage"]:
        cursor = discussion["comments"]["pageInfo"]["endCursor"]
        comment_query = """
        query GetMoreDiscussionComments($owner: String!, $repoName: String!, $discussionNumber: Int!, $cursor: String!) {
          repository(owner: $owner, name: $repoName) {
            discussion(number: $discussionNumber) {
              comments(first: 100, after: $cursor) {
                nodes {
                  body
                  createdAt
                  author {
                    login
                  }
                }
                pageInfo {
                    hasNextPage
                    endCursor
                }
              }
            }
          }
        }
        """
        comment_variables = {
            "owner": owner,
            "repoName": repo_name,
            "discussionNumber": discussion_number,
            "cursor": cursor,
        }
        comment_data = run_graphql_query(comment_query, comment_variables)
        discussion["comments"]["nodes"].extend(
            comment_data["repository"]["discussion"]["comments"]["nodes"]
        )
        discussion["comments"]["pageInfo"] = comment_data["repository"]["discussion"][
            "comments"
        ]["pageInfo"]

    return discussion


def create_discussion(repo_id, title, body, category_id):
    """Creates a new discussion in the target repository."""
    mutation = """
    mutation CreateDiscussion($repositoryId: ID!, $title: String!, $body: String!, $categoryId: ID!) {
      createDiscussion(input: {repositoryId: $repositoryId, title: $title, body: $body, categoryId: $categoryId}) {
        discussion {
          id
          url
          number
        }
      }
    }
    """
    variables = {
        "repositoryId": repo_id,
        "title": title,
        "body": body,
        "categoryId": category_id,
    }
    data = run_graphql_query(mutation, variables)
    return data["createDiscussion"]["discussion"]


def create_discussion_comment(discussion_id, body):
    """Adds a comment to an existing discussion."""
    mutation = """
    mutation AddDiscussionComment($discussionId: ID!, $body: String!) {
      addDiscussionComment(input: {discussionId: $discussionId, body: $body}) {
        comment {
          id
          url
        }
      }
    }
    """
    variables = {"discussionId": discussion_id, "body": body}
    data = run_graphql_query(mutation, variables)
    return data["addDiscussionComment"]["comment"]


def copy_discussion(
    source_discussion_url, target_repo_url, *, target_category_name="General"
):
    """
    Copies a discussion from a source URL to a target repository URL.
    Attempts to preserve content and provide context for original authors/timestamps.
    """
    print(f"--- Starting Discussion Copy ---")
    print(f"Source Discussion: {source_discussion_url}")
    print(f"Target Repository: {target_repo_url}")

    # 1. Parse URLs
    source_owner, source_repo_name, discussion_number = parse_github_discussion_url(
        source_discussion_url
    )
    target_owner, target_repo_name = parse_github_repo_url(target_repo_url)

    # 2. Get target repository ID and categories
    print(
        f"Getting target repository ID and discussion categories for '{target_owner}/{target_repo_name}'..."
    )
    target_repo_id, target_categories = get_repository_id(
        target_owner, target_repo_name
    )
    print("Available discussion categories in target repository:")
    for cat in target_categories:
        print(f"  - Name: {cat['name']}, ID: {cat['id']}")

    # Prompt user to choose a category ID
    if target_category_name is None:
        target_category_name = input(
            "Enter the name of the target discussion category (e.g., 'General', 'Q&A'): "
        )

    target_category_id = None
    for cat in target_categories:
        if cat["name"].lower() == target_category_name.lower():
            target_category_id = cat["id"]
            break
    if not target_category_id:
        raise ValueError(
            f"Category '{target_category_name}' not found in target repository. Please choose from the listed categories."
        )

    # 3. Get source discussion data
    print(
        f"Fetching discussion #{discussion_number} from '{source_owner}/{source_repo_name}'..."
    )
    source_discussion = get_discussion_data(
        source_owner, source_repo_name, discussion_number
    )

    # 4. Prepare new discussion title and body
    original_discussion_link = source_discussion["url"]
    original_author = (
        source_discussion["author"]["login"]
        if source_discussion["author"]
        else "Unknown"
    )
    original_created_at = source_discussion["createdAt"]
    original_category_name = (
        source_discussion["category"]["name"]
        if source_discussion["category"]
        else "Unknown"
    )

    new_title = f"{source_discussion['title']}"
    new_body_prefix = f"""
_This discussion was copied from [original discussion]({original_discussion_link}) in `{source_owner}/{source_repo_name}`._

---
**Original Post by @{original_author} on {original_created_at} (Category: {original_category_name}):**

"""
    new_body = new_body_prefix + source_discussion["body"]

    # 5. Create the new discussion
    print(
        f"Creating new discussion in '{target_owner}/{target_repo_name}' under category '{target_category_name}'..."
    )
    new_discussion = create_discussion(
        target_repo_id, new_title, new_body, target_category_id
    )
    print(f"New discussion created: {new_discussion['url']}")
    print(f"New discussion ID: {new_discussion['id']}")

    # 6. Copy comments
    print("Copying comments...")
    for i, comment in enumerate(source_discussion["comments"]["nodes"]):
        comment_author = comment["author"]["login"] if comment["author"] else "Unknown"
        comment_created_at = comment["createdAt"]

        new_comment_body = f"""
---
**Comment by @{comment_author} on {comment_created_at}:**

{comment["body"]}
"""
        try:
            create_discussion_comment(new_discussion["id"], new_comment_body)
            print(
                f"  - Copied comment {i + 1}/{len(source_discussion['comments']['nodes'])}"
            )
        except Exception as e:
            print(f"  - ERROR copying comment {i + 1}: {e}")

    print(f"--- Discussion Copy Complete ---")
    print(f"New discussion available at: {new_discussion['url']}")


# --------------------------------------------------------------------------------------
# Miscellaneous tools


# TODO: Enhance to get more information, or be able to ask more from sha
# TODO: Test (manually): Not sure I'm getting all the commits I should be getting
def get_author_commits(
    repo: str, author_email: str, days_range: tuple | int
) -> list[dict]:
    """
    Fetches GitHub commits for a specific author within a given date range.

    Args:
        repo_name (str): The repo_owner/repo_name in the format for a repo.
        author_email (str): The email address of the author to filter commits by.
        days_range (tuple | int): The date range for the commits.
                                  If an int, it's the number of days back from today.
                                  If a tuple, it's (start_date_str, end_date_str) in 'YYYY-MM-DD' format (inclusive).

    Returns:
        list[dict]: A list of dictionaries, where each dictionary represents a commit
                    and contains 'sha', 'message', 'author_name', 'author_email', 'commit_date'.
                    Returns an empty list if no commits are found or an error occurs.
    """

    import os
    import requests
    from datetime import datetime, timedelta, timezone

    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        print("Error: GITHUB_TOKEN environment variable not set.")
        return []

    base_url = f"https://api.github.com/repos/{repo}/commits"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
    }

    # Determine start_date and end_date
    today = datetime.now(timezone.utc).date()
    if isinstance(days_range, int):
        if days_range < 0:
            print("Error: days_range (int) cannot be negative.")
            return []
        start_date_obj = today - timedelta(days=days_range)
        end_date_obj = today
    elif isinstance(days_range, tuple) and len(days_range) == 2:
        try:
            start_date_obj = datetime.strptime(days_range[0], "%Y-%m-%d").date()
            end_date_obj = datetime.strptime(days_range[1], "%Y-%m-%d").date()
        except ValueError:
            print("Error: Invalid date format in days_range tuple. Use 'YYYY-MM-DD'.")
            return []
        if start_date_obj > end_date_obj:
            print("Error: start_date cannot be after end_date.")
            return []
    else:
        print(
            "Error: days_range must be an integer or a tuple of (start_date_str, end_date_str)."
        )
        return []

    # Format dates for GitHub API (ISO 8601)
    # To make dates inclusive of the full day, set time to 00:00:00 for 'since' and 23:59:59 for 'until'
    since_iso = (
        datetime.combine(start_date_obj, datetime.min.time(), tzinfo=timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )
    until_iso = (
        datetime.combine(end_date_obj, datetime.max.time(), tzinfo=timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )

    all_commits = []
    page = 1
    per_page = 100  # Max per_page for GitHub API

    while True:
        params = {
            "since": since_iso,
            "until": until_iso,
            "per_page": per_page,
            "page": page,
        }

        try:
            response = requests.get(base_url, headers=headers, params=params)
            response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
            commits_data = response.json()

            if not commits_data:
                break  # No more commits on this page

            for commit_info in commits_data:
                commit_detail = commit_info.get("commit", {})
                author_detail = commit_detail.get("author", {})
                committer_detail = commit_detail.get(
                    "committer", {}
                )  # Fallback to committer if author is not filled

                commit_email = author_detail.get("email") or committer_detail.get(
                    "email"
                )

                if commit_email and commit_email.lower() == author_email.lower():
                    all_commits.append(
                        {
                            "sha": commit_info.get("sha"),
                            "message": commit_detail.get("message"),
                            "author_name": author_detail.get("name")
                            or committer_detail.get("name"),
                            "author_email": commit_email,
                            "commit_date": author_detail.get("date")
                            or committer_detail.get(
                                "date"
                            ),  # Use author date or committer date
                        }
                    )

            if len(commits_data) < per_page:
                break  # Less than per_page commits means it's the last page

            page += 1

        except requests.exceptions.RequestException as e:
            print(f"Network or API error: {e}")
            break
        except ValueError:
            print("Error: Could not parse API response as JSON.")
            break
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            break

    return all_commits


# --------------------------------------------------------------------------------------
# Local Repository Artifacts - Mapping interfaces to cached repository data


import os
from typing import Optional
from dol import KvReader, wrap_kvs, Pipe, add_ipython_key_completions
from hubcap.util import (
    repo_cache_dir,
    JsonFiles,
    get_repository_info,
    Discussions,
    ensure_full_name,
)
from hubcap.base import Issues


class _RepoInfoMapping(KvReader):
    """Mapping interface to cached repository info.json files."""

    def __init__(self, refresh: bool = False):
        self.refresh = refresh
        self._cache_dir = repo_cache_dir

    def __iter__(self):
        """Iterate over repository full names that have cached info."""
        for org_name in os.listdir(self._cache_dir):
            org_path = os.path.join(self._cache_dir, org_name)
            if os.path.isdir(org_path):
                for repo_name in os.listdir(org_path):
                    repo_path = os.path.join(org_path, repo_name)
                    if os.path.isdir(repo_path):
                        info_file = os.path.join(repo_path, "info.json")
                        if os.path.exists(info_file):
                            yield f"{org_name}/{repo_name}"

    def __getitem__(self, repo: str) -> dict:
        """Get repository info, from cache or by fetching."""
        return get_repository_info(repo, refresh=self.refresh)


class _RepoArtifactMapping(KvReader):
    """Base class for mapping interfaces to cached repository artifacts."""

    def __init__(self, artifact_type: str, artifact_class, refresh: bool = False):
        self.artifact_type = artifact_type
        self.artifact_class = artifact_class
        self.refresh = refresh
        self._cache_dir = repo_cache_dir

    def __iter__(self):
        """Iterate over repository full names that have this artifact cached."""
        for org_name in os.listdir(self._cache_dir):
            org_path = os.path.join(self._cache_dir, org_name)
            if os.path.isdir(org_path):
                for repo_name in os.listdir(org_path):
                    repo_path = os.path.join(org_path, repo_name)
                    artifact_dir = os.path.join(repo_path, self.artifact_type)
                    if os.path.isdir(artifact_dir) and os.listdir(artifact_dir):
                        yield f"{org_name}/{repo_name}"

    def __getitem__(self, repo: str) -> dict:
        """Get artifacts for a repository as a mapping."""
        full_name = ensure_full_name(repo)
        artifact_dir = os.path.join(self._cache_dir, full_name, self.artifact_type)

        # If cache doesn't exist or refresh is True, fetch from GitHub
        if self.refresh or not os.path.exists(artifact_dir):
            # Fetch and cache using the artifact class
            artifact_instance = self.artifact_class(
                repo, cache=True, refresh=self.refresh
            )
            # Trigger fetching by iterating and accessing items
            result = {}
            for key in artifact_instance:
                result[key] = artifact_instance[key]
            return result
        else:
            # Load from cache
            cache_store = JsonFiles(artifact_dir)
            return {
                int(k.replace(".json", "")): cache_store[k]
                for k in cache_store
                if k.endswith(".json")
            }


class _DiscussionsMapping(_RepoArtifactMapping):
    """Mapping interface to cached repository discussions."""

    def __init__(self, refresh: bool = False):
        super().__init__(
            artifact_type="discussions",
            artifact_class=Discussions,
            refresh=refresh,
        )


class _IssuesMapping(_RepoArtifactMapping):
    """Mapping interface to cached repository issues."""

    def __init__(self, refresh: bool = False):
        super().__init__(
            artifact_type="issues",
            artifact_class=Issues,
            refresh=refresh,
        )


class LocalRepoArtifacts(KvReader):
    """
    Provides mapping interfaces to locally cached repository artifacts.

    This class gives you access to cached repository information, discussions, and
    issues through simple mapping interfaces. Data is cached locally and can be
    refreshed on demand.

    Args:
        refresh: If True, always fetch fresh data from GitHub and update cache.
                 If False, use cached data when available.

    Attributes:
        info: Mapping interface to repository info (info.json for each repo)
        discussions: Mapping interface to repository discussions
        issues: Mapping interface to repository issues

    Example:
        >>> artifacts = LocalRepoArtifacts(refresh=False)  # doctest: +SKIP
        >>> # List available artifact types
        >>> list(artifacts)  # doctest: +SKIP
        ['info', 'discussions', 'issues']
        >>> # Access via attribute
        >>> info = artifacts.info['thorwhalen/hubcap']  # doctest: +SKIP
        >>> # Or via mapping interface
        >>> info = artifacts['info']['thorwhalen/hubcap']  # doctest: +SKIP
        >>> # Get cached discussions
        >>> discussions = artifacts.discussions['thorwhalen/hubcap']  # doctest: +SKIP
        >>> # Access a specific discussion
        >>> discussion_2 = discussions[2]  # doctest: +SKIP
        >>> # Get cached issues
        >>> issues = artifacts.issues['thorwhalen/hubcap']  # doctest: +SKIP

    The cache is stored in: {app_data_dir}/repos/{org}/{repo}/{artifact_type}/
    For example:
        - Info: ~/.local/share/hubcap/repos/thorwhalen/hubcap/info.json
        - Discussions: ~/.local/share/hubcap/repos/thorwhalen/hubcap/discussions/1.json
        - Issues: ~/.local/share/hubcap/repos/thorwhalen/hubcap/issues/4.json
    """

    def __init__(self, refresh: bool = False):
        self.refresh = refresh
        self.info = add_ipython_key_completions(_RepoInfoMapping(refresh=refresh))
        self.discussions = add_ipython_key_completions(
            _DiscussionsMapping(refresh=refresh)
        )
        self.issues = add_ipython_key_completions(_IssuesMapping(refresh=refresh))
        self._artifacts = {
            "info": self.info,
            "discussions": self.discussions,
            "issues": self.issues,
        }

    def __iter__(self):
        """Iterate over artifact type names."""
        return iter(self._artifacts)

    def __getitem__(self, key):
        """Get an artifact mapping by name."""
        return self._artifacts[key]

    def __len__(self):
        """Return number of artifact types."""
        return len(self._artifacts)


from hubcap.util import create_markdown_from_jdict


def _add_md_access(s):
    s.discussions_mds = add_ipython_key_completions(
        wrap_kvs(
            s.discussions,
            value_decoder=create_markdown_from_jdict,
        )
    )
    s.issues_mds = add_ipython_key_completions(
        wrap_kvs(
            s.issues,
            value_decoder=create_markdown_from_jdict,
        )
    )
    return s


# Create a default instance for convenience
local_repo_artifacts = _add_md_access(LocalRepoArtifacts(refresh=False))
remote_repo_artifacts = _add_md_access(LocalRepoArtifacts(refresh=True))
