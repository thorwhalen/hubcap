"""A medley of tools for Hubcap."""

from typing import Iterable, Literal
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
        "path": relpath,
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
    output_dir: Optional[str] = None,
    repo_root_url: Optional[Union[dict, str]] = None,
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
    trg_str = re.sub("```python\s*```", "", trg_str, flags=re.DOTALL)

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
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    raise EnvironmentError("GITHUB_TOKEN environment variable not set.")

GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"

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
    source_discussion_url, target_repo_url, *, target_category_name='General'
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
        if cat['name'].lower() == target_category_name.lower():
            target_category_id = cat['id']
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
