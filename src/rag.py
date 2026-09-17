"""Traceable local retrieval for the controlled UtiliCare knowledge corpus.

The Week 3 retriever is intentionally deterministic: it does not send corpus
content to an external service and every returned chunk retains its source ID.
"""

from __future__ import annotations

import csv
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CORPUS_DIR = ROOT / "knowledge" / "corpus"
REGISTER_PATH = ROOT / "knowledge" / "source_register.csv"
CHUNK_SIZE_WORDS = 120
CHUNK_OVERLAP_WORDS = 20
TOP_K = 3

# Words that carry little retrieval meaning in a customer question.
STOP_WORDS = frozenset(
    "a an and are as at be but by can do for from have how i if in is it me my of on or please should the this to was what when where which who why will with you your".split()
)
TOKEN_NORMALIZATION = {
    "billed": "bill",
    "billing": "bill",
    "bills": "bill",
    "charged": "charge",
    "charges": "charge",
    "connections": "connection",
    "flickering": "flicker",
    "leaking": "leak",
    "leaks": "leak",
    "restored": "restore",
    "restoration": "restore",
}


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    doc_id: str
    title: str
    category: str
    text: str
    token_counts: Counter[str]


@dataclass(frozen=True)
class RetrievedChunk:
    chunk: Chunk
    score: float

    def as_dict(self) -> dict[str, object]:
        return {
            "chunk_id": self.chunk.chunk_id,
            "doc_id": self.chunk.doc_id,
            "title": self.chunk.title,
            "category": self.chunk.category,
            "score": round(self.score, 3),
            "text": self.chunk.text,
        }


def _tokens(value: str) -> list[str]:
    return [
        TOKEN_NORMALIZATION.get(token, token)
        for token in re.findall(r"[a-z0-9]+", value.lower())
        if len(token) > 1 and token not in STOP_WORDS
    ]


def _parse_document(path: Path) -> tuple[str, str, str]:
    """Return document ID, title and body from the controlled Markdown format."""
    raw = path.read_text(encoding="utf-8")
    fields = dict(re.findall(r"^(Document ID|Title):\s*(.+)$", raw, re.MULTILINE))
    body_marker = "Content:"
    if body_marker not in raw or "Document ID" not in fields or "Title" not in fields:
        raise ValueError(f"Invalid corpus document format: {path.relative_to(ROOT)}")
    body = raw.split(body_marker, 1)[1].strip()
    if not body:
        raise ValueError(f"Corpus document has no content: {path.relative_to(ROOT)}")
    return fields["Document ID"], fields["Title"], body


def _load_register() -> dict[str, dict[str, str]]:
    with REGISTER_PATH.open(encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    required = {"Doc ID", "Title", "Category", "File Path"}
    if not rows or not required.issubset(rows[0]):
        raise ValueError("source_register.csv is missing required provenance columns")
    register = {row["Doc ID"]: row for row in rows}
    if len(register) != len(rows):
        raise ValueError("source_register.csv contains duplicate document IDs")
    return register


def build_index() -> list[Chunk]:
    """Validate corpus provenance and create overlapping, metadata-preserving chunks."""
    register = _load_register()
    chunks: list[Chunk] = []
    seen_ids: set[str] = set()

    for path in sorted(CORPUS_DIR.glob("*.md")):
        doc_id, title, body = _parse_document(path)
        row = register.get(doc_id)
        if row is None:
            raise ValueError(f"Corpus document {doc_id} is absent from source_register.csv")
        if row["Title"] != title:
            raise ValueError(f"Title mismatch for {doc_id} between corpus and source register")
        expected_path = (ROOT / row["File Path"]).resolve()
        if expected_path != path.resolve():
            raise ValueError(f"File-path mismatch for {doc_id} in source_register.csv")

        words = body.split()
        step = max(1, CHUNK_SIZE_WORDS - CHUNK_OVERLAP_WORDS)
        for number, start in enumerate(range(0, len(words), step), start=1):
            text = " ".join(words[start:start + CHUNK_SIZE_WORDS])
            if not text:
                continue
            chunks.append(Chunk(
                chunk_id=f"{doc_id}-C{number:02d}", doc_id=doc_id,
                title=title, category=row["Category"], text=text,
                token_counts=Counter(_tokens(f"{title} {text}")),
            ))
        seen_ids.add(doc_id)

    if seen_ids != set(register):
        missing_files = sorted(set(register) - seen_ids)
        raise ValueError(f"Source-register documents missing from corpus: {missing_files}")
    return chunks


_INDEX: list[Chunk] | None = None


def get_index() -> list[Chunk]:
    global _INDEX
    if _INDEX is None:
        _INDEX = build_index()
    return _INDEX


def retrieve(query: str, top_k: int = TOP_K) -> list[RetrievedChunk]:
    """Return ranked chunks, or no chunks when the corpus has no relevant evidence."""
    if top_k < 1:
        raise ValueError("top_k must be at least 1")
    query_counts = Counter(_tokens(query))
    if not query_counts:
        return []

    ranked: list[RetrievedChunk] = []
    for chunk in get_index():
        score = sum(query_count * chunk.token_counts[token] for token, query_count in query_counts.items())
        if score:
            ranked.append(RetrievedChunk(chunk=chunk, score=float(score)))
    return sorted(ranked, key=lambda item: (-item.score, item.chunk.doc_id))[:top_k]


def build_grounding(query: str) -> dict[str, object]:
    """Build model context and an auditable trace from the retrieved chunks."""
    matches = retrieve(query)
    sources = [
        {"doc_id": item.chunk.doc_id, "title": item.chunk.title, "category": item.chunk.category}
        for item in matches
    ]
    if not matches:
        return {
            "status": "insufficient_evidence",
            "context": "No relevant controlled knowledge-base evidence was retrieved.",
            "sources": [],
            "trace": {"query": query, "top_k": TOP_K, "retrieved_chunks": []},
        }

    context = "\n\n".join(
        f"[Source {item.chunk.doc_id} | {item.chunk.title}]\n{item.chunk.text}"
        for item in matches
    )
    return {
        "status": "grounded",
        "context": context,
        "sources": sources,
        "trace": {
            "query": query,
            "top_k": TOP_K,
            "retrieved_chunks": [item.as_dict() for item in matches],
        },
    }
