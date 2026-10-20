# hubcap.constants

A place to put constants, defaults, types…

### Functions

| [`repo_collection_names_`](#hubcap.constants.repo_collection_names_)()   | List of the names of the objects that can be retrieved from a repository (e.g. commits, contributors, issues, pull_requests, releases, tags, etc.) These names are extracted by taking all the method names of the `github.Repository` class that start with `get_` and end with `s`, and removing the `get_` prefix.   |
|-----------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

### hubcap.constants.repo_collection_names_()

List of the names of the objects that can be retrieved from a repository
(e.g. commits, contributors, issues, pull_requests, releases, tags, etc.)
These names are extracted by taking all the method names of the
`github.Repository` class that start with `get_` and end with `s`,
and removing the `get_` prefix.
