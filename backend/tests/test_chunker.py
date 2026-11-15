from app.chunker import Chunk, chunk_chapters
from app.parser import Chapter


def test_paragraph_boundaries_kept_and_mapped_to_chapter() -> None:
    chapters = [Chapter("A", ["one.", "two."]), Chapter("B", ["three."])]
    assert chunk_chapters(chapters, max_chars=100) == [
        Chunk(0, "A", "one."),
        Chunk(0, "A", "two."),
        Chunk(1, "B", "three."),
    ]


def test_long_paragraph_splits_on_sentences_within_bound() -> None:
    para = "Aaaa aaa. Bbbb bbb. Cccc ccc."
    chunks = chunk_chapters([Chapter("A", [para])], max_chars=20)
    assert [c.text for c in chunks] == ["Aaaa aaa. Bbbb bbb.", "Cccc ccc."]


def test_oversized_sentence_hard_splits_on_words() -> None:
    chunks = chunk_chapters([Chapter("A", ["word " * 10])], max_chars=12)
    assert all(len(c.text) <= 12 for c in chunks)
    assert " ".join(c.text for c in chunks) == ("word " * 10).strip()


def test_unicode_and_empty() -> None:
    assert chunk_chapters([Chapter("A", ["Héllo wörld. 日本語です。"])], 50)[0].text.startswith(
        "Héllo"
    )
    assert chunk_chapters([Chapter("A", [])], 50) == []
