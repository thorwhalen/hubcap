# hubcap.base

Base objects

### Functions

| `decoded_contents`(content_file)           |    |
|--------------------------------------------|----|
| `find_github_token`()                      |    |
| `find_user_name`()                         |    |
| `identity`(x)                              |    |
| `repo_objects_instance`(repo, object_name) |    |

### Classes

| [`BranchDir`](#hubcap.base.BranchDir)(repo, branch_name[, path, ...])       |                                                                 |
|--------------------------------------------------------------------------------------------------|-----------------------------------------------------------------|
| [`Branches`](#hubcap.base.Branches)(repo[, content_file_extractor])        |                                                                 |
| [`GitHubDol`](#hubcap.base.GitHubDol)([account_name, ...])                  | a Store that can access a GitHub account                        |
| [`GitHubReader`](#hubcap.base.GitHubReader)                                    |                                                                 |
| [`GithubReader`](#hubcap.base.GithubReader)([account_name, ...])               | a Store that can access a GitHub account.                       |
| [`IssueComments`](#hubcap.base.IssueComments)(issue_obj)                        | Mapping interface to repository issue comments' body            |
| [`IssueCommentsBase`](#hubcap.base.IssueCommentsBase)(issue_obj)                    | Base Mapping interface to repository issue comments (object)    |
| [`IssueContents`](#hubcap.base.IssueContents)(issue_obj)                        | Mapping interface to repository issue contents                  |
| [`Issues`](#hubcap.base.Issues)(repo[, get_objs, objs_to_items, ...])    | Mapping interface to repository issues.                         |
| [`PaginatedListDol`](#hubcap.base.PaginatedListDol)(paginated_list)                | Gives a Sized & Iterable & Reversible view of a paginated_list. |
| [`RepoObjects`](#hubcap.base.RepoObjects)(repo, get_objs, \*[, ...])          |                                                                 |
| [`RepoReader`](#hubcap.base.RepoReader)(repo)                                |                                                                 |
| [`Workflows`](#hubcap.base.Workflows)(repo[, get_objs, objs_to_items, ...]) |                                                                 |

### Exceptions

| [`RepositoryNotFound`](#hubcap.base.RepositoryNotFound)(status[, data, headers, ...])   | Raised when a repository is not found   |
|-----------------------------------------------------------------------------------------------------|-----------------------------------------|
| [`ResourceNotFound`](#hubcap.base.ResourceNotFound)                                   | Raised when a resource is not found     |

### *class* hubcap.base.BranchDir(repo, branch_name, path='', content_file_extractor=<function decoded_contents>)

Bases: `KvReader`

### *class* hubcap.base.Branches(repo, content_file_extractor=<function decoded_contents>)

Bases: `KvReader`

### *class* hubcap.base.GitHubDol(account_name=None, content_file_extractor=<function decoded_contents>, login_or_token=None, password=None, jwt=None, base_url='https://api.github.com', timeout=15, user_agent='PyGithub/Python', per_page=30, verify=True, retry=None, pool_size=None)

Bases: `KvReader`

a Store that can access a GitHub account

### hubcap.base.GitHubReader

alias of [`GithubReader`](#hubcap.base.GithubReader)

### *class* hubcap.base.GithubReader(account_name=None, content_file_extractor=<function decoded_contents>, \*, auth=None, jwt=None, base_url='https://api.github.com', timeout=15, user_agent='PyGithub/Python', per_page=30, verify=True, retry=None, get_repos_kwargs=(), login_or_token=None, password=None)

Bases: `KvReader`

a Store that can access a GitHub account.

You need to specify a token in auth, or in the environment variable
HUBCAP_GITHUB_TOKEN or GITHUB_TOKEN.

The iteration is defined to be the repositories of the account_name
(could be organization name).

### *class* hubcap.base.IssueComments(issue_obj)

Bases: `Store`

Mapping interface to repository issue comments’ body

### *class* hubcap.base.IssueCommentsBase(issue_obj)

Bases: `KvReader`

Base Mapping interface to repository issue comments (object)

### *class* hubcap.base.IssueContents(issue_obj)

Bases: `KvReader`

Mapping interface to repository issue contents

### *class* hubcap.base.Issues(repo, get_objs=<function Repository.get_issues>, \*, objs_to_items='number', data_of_obj=<function identity>, get_objs_kwargs=(('state', 'open'), ), cache=False, refresh=True)

Bases: [`RepoObjects`](#hubcap.base.RepoObjects)

Mapping interface to repository issues.

* **Parameters:**
  * **repo** ([`Union`](https://docs.python.org/3/library/typing.html#typing.Union)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), `Repository`]) – The repository to get issues from
  * **get_objs** – The function to get the issues
  * **objs_to_items** – A function to get the key-value pairs from the issue objects
  * **data_of_obj** – A function to get the data from the issue object.
    Default is attrgetter(‘body’). Use identity to get the whole issue object.
  * **get_objs_kwargs** – The keyword arguments to pass to the get_objs function
  * **cache** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – If True, cache issue data to local storage
  * **refresh** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – If True, always fetch fresh data from GitHub and update cache

The default of data_of_obj is `IssueContents`, which will give a mapping
interface to the body and comments of the issue.

### *class* hubcap.base.PaginatedListDol(paginated_list)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Gives a Sized & Iterable & Reversible view of a paginated_list.
That is, iterating over a PaginatedListDol

### *class* hubcap.base.RepoObjects(repo, get_objs, \*, objs_to_items=<class 'enumerate'>, data_of_obj=<function identity>, get_objs_kwargs=None)

Bases: `KvReader`

### *class* hubcap.base.RepoReader(repo)

Bases: `KvReader`

### *exception* hubcap.base.RepositoryNotFound(status, data=None, headers=None, message=None)

Bases: `UnknownObjectException`, [`ResourceNotFound`](#hubcap.base.ResourceNotFound)

Raised when a repository is not found

### *exception* hubcap.base.ResourceNotFound

Bases: [`Exception`](https://docs.python.org/3/builtins/exceptions.html#Exception)

Raised when a resource is not found

### *class* hubcap.base.Workflows(repo, get_objs=<function Repository.get_workflows>, \*, objs_to_items='id', data_of_obj=<function identity>, get_objs_kwargs=())

Bases: [`RepoObjects`](#hubcap.base.RepoObjects)
