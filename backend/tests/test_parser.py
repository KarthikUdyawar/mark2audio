from app.parser import parse_markdown

DOC = """Intro text.

# One
Para with **bold**, a [link](http://x.io) and `code`.

- item a
- item b

> quoted

```py
secret()
```

## Sub
sub text

# Two
# Empty
"""


def test_chapters_in_order_with_clean_text() -> None:
    chapters = parse_markdown(DOC)
    titles = [c.title for c in chapters]
    assert titles == ["Introduction", "One"]  # "Two"/"Empty" are heading-only → dropped
    one = chapters[1].paragraphs
    assert one[0] == "One"
    assert "Para with bold, a link and" in one[1]
    assert "http" not in " ".join(one) and "secret" not in " ".join(one)
    assert one[2:5] == ["item a", "item b", "quoted"]
    assert one[-2:] == ["Sub", "sub text"]


def test_include_code_speaks_code() -> None:
    text = " ".join(p for c in parse_markdown(DOC, include_code=True) for p in c.paragraphs)
    assert "secret()" in text and "code" in text


def test_no_headings_single_chapter() -> None:
    (only,) = parse_markdown("just words\n\nmore words")
    assert only.paragraphs == ["just words", "more words"]


def test_chapter_level_two_splits_on_h2() -> None:
    chapters = parse_markdown("# A\nx\n## B\ny", chapter_level=2)
    assert [c.title for c in chapters] == ["A", "B"]


def test_textless_is_empty() -> None:
    assert parse_markdown("# \n\n```\ncode\n```\n") == []
