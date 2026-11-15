"""Split chapters into bounded, ordered TTS chunks (paragraph → sentence → word)."""

import re
from dataclasses import dataclass

from app.parser import Chapter

_SENTENCE_END = re.compile(r"(?<=[.!?。！？])\s+")


@dataclass(frozen=True)
class Chunk:
    chapter_index: int
    chapter_title: str
    text: str


def chunk_chapters(chapters: list[Chapter], max_chars: int) -> list[Chunk]:
    return [
        Chunk(index, chapter.title, text)
        for index, chapter in enumerate(chapters)
        for paragraph in chapter.paragraphs
        for text in _split_paragraph(paragraph, max_chars)
    ]


def _split_paragraph(paragraph: str, max_chars: int) -> list[str]:
    pieces: list[str] = []
    current = ""
    for sentence in _SENTENCE_END.split(paragraph):
        for part in _split_words(sentence, max_chars):
            if current and len(current) + 1 + len(part) > max_chars:
                pieces.append(current)
                current = part
            else:
                current = f"{current} {part}".strip()
    return [*pieces, current] if current else pieces


def _split_words(sentence: str, max_chars: int) -> list[str]:
    if len(sentence) <= max_chars:
        return [sentence]
    parts: list[str] = []
    current = ""
    for word in sentence.split():
        word_pieces = [word[i : i + max_chars] for i in range(0, len(word), max_chars)]
        for piece in word_pieces:
            if current and len(current) + 1 + len(piece) > max_chars:
                parts.append(current)
                current = piece
            else:
                current = f"{current} {piece}".strip()
    return [*parts, current] if current else parts
