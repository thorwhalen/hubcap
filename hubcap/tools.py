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
