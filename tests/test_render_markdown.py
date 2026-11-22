"""Offline tests of ``hubcap.snapshot.render_markdown`` and its helpers."""

from hubcap.snapshot import _author, _comment_block, _item_updated, render_markdown


def test_author_falls_back_through_user_author_and_ghost():
    assert _author({"user": {"login": "a"}}) == "a"
    assert _author({"author": {"login": "b"}}) == "b"
    assert _author({"user": None}) == "ghost"
    assert _author({}) == "ghost"


def test_item_updated_accepts_both_api_spellings():
    assert _item_updated({"updated_at": "x"}) == "x"
    assert _item_updated({"updatedAt": "y"}) == "y"
    assert _item_updated({}) == ""


def test_comment_block_marks_path_and_nests_replies_as_quotes():
    c = {
        "user": {"login": "a"},
        "path": "f.py",
        "created_at": "T",
        "body": " hi ",
        "replies": {"nodes": [{"author": {"login": "b"}, "createdAt": "U", "body": "yo"}]},
    }
    text = _comment_block(c)
    assert "**a** on `f.py` (T)" in text
    assert "> **b** (U)" in text and "> yo" in text


def test_render_markdown_issue_with_comments():
    item = {
        "number": 7,
        "title": 'say "hi"',
        "state": "open",
        "user": {"login": "a"},
        "updated_at": "T",
        "html_url": "http://u",
        "body": "body text",
        "comments_data": [{"user": {"login": "b"}, "body": "c1", "created_at": "T2"}],
    }
    md = render_markdown("issue", "o/r", item)
    assert md.startswith("---\nrepo: o/r\nkind: issue\nnumber: 7\n")
    assert "title: \"say 'hi'\"" in md  # quotes in the title are made YAML-safe
    assert "# say \"hi\"" in md and "body text" in md
    assert "## Comments" in md and "**b** (T2)" in md and md.endswith("\n")


def test_render_markdown_discussion_uses_the_category_as_state():
    item = {"number": 1, "title": "t", "category": {"name": "Q&A"}, "author": None}
    md = render_markdown("discussion", "o/r", item)
    assert "state: Q&A" in md and "author: ghost" in md
    assert "## Comments" not in md
