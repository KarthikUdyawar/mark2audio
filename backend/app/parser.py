"""Markdown → ordered narration chapters. Pure: no I/O, no network."""

from dataclasses import dataclass, field

from markdown_it import MarkdownIt
from markdown_it.token import Token

INTRO_TITLE = "Introduction"


@dataclass
class Chapter:
    title: str
    paragraphs: list[str] = field(default_factory=list)


class _Builder:
    def __init__(self) -> None:
        self.chapters: list[Chapter] = []

    def start(self, title: str) -> None:
        self.chapters.append(Chapter(title))

    def say(self, text: str) -> None:
        if not self.chapters:
            self.start(INTRO_TITLE)
        self.chapters[-1].paragraphs.append(text)

    def result(self) -> list[Chapter]:
        # A chapter holding only its own title has nothing to narrate.
        return [c for c in self.chapters if len(c.paragraphs) > (c.title != INTRO_TITLE)]


def parse_markdown(
    source: str, chapter_level: int = 1, include_code: bool = False
) -> list[Chapter]:
    """Split Markdown into chapters of speakable paragraphs (headings are spoken too)."""
    book = _Builder()
    heading_level = 0
    for token in MarkdownIt("commonmark").enable("table").parse(source):
        if token.type == "heading_open":
            heading_level = int(token.tag[1:])
        elif token.type == "inline":
            text = _inline_text(token, include_code)
            if heading_level and heading_level <= chapter_level and text:
                book.start(text)
            if text:
                book.say(text)
            heading_level = 0
        elif token.type in ("fence", "code_block") and include_code:
            text = " ".join(token.content.split())
            if text:
                book.say(text)
    return book.result()


def _inline_text(token: Token, include_code: bool) -> str:
    parts = []
    for child in token.children or []:
        if child.type == "text" or (child.type == "code_inline" and include_code):
            parts.append(child.content)
        elif child.type in ("softbreak", "hardbreak"):
            parts.append(" ")
    return " ".join("".join(parts).split())
