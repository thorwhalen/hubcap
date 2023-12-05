"""Download wikis from github"""

import os
import subprocess
import shutil
import tempfile


def download_github_wiki(repo_id: str, download_dir: str):
    """
    Download the wiki associated with a given GitHub repository.

    Parameters
    ----------
    repo_id : str
        The GitHub repository identifier in the format "owner/repository_name".
    download_dir : str
        The path of the directory where the wiki will be downloaded.

    Raises
    ------
    FileNotFoundError
        If the download_dir does not exist.
    """

    if not os.path.isdir(download_dir):
        os.makedirs(download_dir)

    owner, repo_name = repo_id.split('/')
    destination = os.path.join(download_dir, owner, repo_name)

    # GitHub stores wiki content in a separate git repository appended with ".wiki"
    wiki_repo = f'https://github.com/{repo_id}.wiki.git'

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            subprocess.check_call(['git', 'clone', wiki_repo, tmpdir])
        except subprocess.CalledProcessError:
            # If git clone fails, wiki probably does not exist, so return
            return

        # If we get here, wiki exists and we've cloned it successfully to a temporary directory.
        # Now we move the wiki files to the destination directory.

        os.makedirs(destination, exist_ok=True)
        for file_name in os.listdir(tmpdir):
            shutil.move(os.path.join(tmpdir, file_name), destination)


# def download_github_wiki(repo_id: str, download_dir: str):
#     """
#     Download all wikis of a GitHub repository to a specific directory.

#     Parameters
#     ----------
#     repo_id : str
#         Identifier of the repository in "owner/repository_name" format.
#     download_dir : str
#         Directory where wikis will be downloaded.
#     """
#     owner, repo_name = repo_id.split("/")
#     dest_dir = os.path.join(download_dir, owner, repo_name)

#     # Create the destination directory if it doesn't exist
#     os.makedirs(dest_dir, exist_ok=True)

#     # URL of the wiki's Git repository
#     wiki_git_url = f"https://github.com/{repo_id}.wiki.git"

#     try:
#         # Clone the wiki Git repository
#         subprocess.run(
#             ["git", "clone", wiki_git_url, dest_dir],
#             stderr=subprocess.DEVNULL,
#             check=True,
#         )
#     except subprocess.CalledProcessError:
#         # If the repository doesn't have a wiki, remove the created directory
#         os.rmdir(dest_dir)
#     except Exception as e:
#         print(f"An error occurred when downloading the wiki of {repo_id}: {e}")


def url_of_git_directory(path: str) -> str:
    """
    Check if a directory is a git repository and return its remote URL.

    Parameters
    ----------
    path : str
        The path of the directory to check.

    Returns
    -------
    str
        The remote URL if the directory is a git repository, None otherwise.
    """
    try:
        # Get the URL of the 'origin' remote
        with open(os.devnull, 'w') as devnull:
            url = subprocess.check_output(
                ['git', '-C', path, 'remote', 'get-url', 'origin'],
                stderr=devnull,
                encoding='utf-8',
            ).strip()
        return url
    except subprocess.CalledProcessError:
        return None
    except Exception as e:
        print(f'An error occurred when checking if {path} is a git directory: {e}')
        return None


def repository_identifiers(rootdir: str, recursive: bool = True):
    """
    Yield GitHub repository URLs for all git repositories under a given directory.

    Parameters
    ----------
    rootdir : str
        The root directory from where to start the search.
    recursive : bool, optional
        If True, search recursively in all subdirectories.
        If False, search only in the root directory.
        By default, True.

    Yields
    ------
    str
        The GitHub repository URL for each git repository.
    """
    for dirpath, dirnames, filenames in os.walk(rootdir):
        url = url_of_git_directory(dirpath)
        if url is not None:
            # This is a git repository, yield the repository URL
            # and stop exploring this directory further
            if url:
                yield url_to_repository_identifier(url)
            dirnames.clear()  # This will prevent os.walk from exploring subdirectories
        elif not recursive:
            # If we are not searching recursively, clear the dirnames list
            # so os.walk does not explore subdirectories
            dirnames.clear()


def url_to_repository_identifier(url: str):
    if isinstance(url, str):
        if url.endswith('.git'):
            url = url[:-4]  # Remove .git from the end
        if url.startswith('https://github.com/'):
            return url[len('https://github.com/') :]
