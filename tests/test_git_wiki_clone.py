"""``git_wiki_clone`` unpacks ``_prep_git_clone_args`` correctly (thorwhalen/hubcap#19)."""

from unittest.mock import patch

from hubcap import util


def test_git_wiki_clone_builds_the_wiki_clone_command(tmp_path):
    with patch.object(util, 'git') as git:
        folder = util.git_wiki_clone('i2mint/dol', str(tmp_path / 'wiki'))
    command = git.call_args.args[0]
    assert command.startswith('clone ') and '.wiki.git' in command
    assert str(folder) == str(tmp_path / 'wiki')
