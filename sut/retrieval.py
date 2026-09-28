"""Deterministic local retrieval for the SUT.

- keyword: BM25-lite lexical scoring
- vector: hashing-trick embeddings + cosine similarity (no external deps)
- hybrid: reciprocal rank fusion of both rankings
"""
from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass
from pathlib import Path

TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


@dataclass
class Chunk:
    doc: str
    text: str


def load_documents(knowledge_dir: str | Path, chunk_chars: int = 600) -> list[Chunk]:
    chunks: list[Chunk] = []
    for path in sorted(Path(knowledge_dir).glob("*.md")):
        text = path.read_text(encoding="utf-8")
        buf = ""
        for para in re.split(r"\n\s*\n", text):
            if len(buf) + len(para) > chunk_chars and buf:
                chunks.append(Chunk(doc=path.name, text=buf.strip()))
                buf = para
            else:
                buf = f"{buf}\n\n{para}" if buf else para
        if buf.strip():
            chunks.append(Chunk(doc=path.name, text=buf.strip()))
    return chunks


def hashing_embed(tokens: list[str], dim: int = 128) -> list[float]:
    vec = [0.0] * dim
    for tok in tokens:
        h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
        vec[h % dim] += 1.0 if (h >> 8) % 2 == 0 else -1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


class Retriever:
    def __init__(self, knowledge_dir: str | Path):
        self.chunks = load_documents(knowledge_dir)
        self._chunk_tokens = [tokenize(c.text) for c in self.chunks]
        # document frequency for idf
        df: dict[str, int] = {}
        for toks in self._chunk_tokens:
            for t in set(toks):
                df[t] = df.get(t, 0) + 1
        n = max(len(self.chunks), 1)
        self._idf = {t: math.log(1 + (n - d + 0.5) / (d + 0.5)) for t, d in df.items()}
        self._chunk_vecs = [hashing_embed(t) for t in self._chunk_tokens]

    def _keyword_scores(self, query: str) -> list[float]:
        q = tokenize(query)
        scores = []
        for toks in self._chunk_tokens:
            tf: dict[str, int] = {}
            for t in toks:
                tf[t] = tf.get(t, 0) + 1
            s = 0.0
            for term in q:
                if term in tf:
                    s += self._idf.get(term, 0.0) * (tf[term] / (tf[term] + 1.2))
            scores.append(s)
        return scores

    def _vector_scores(self, query: str) -> list[float]:
        qv = hashing_embed(tokenize(query))
        return [cosine(qv, cv) for cv in self._chunk_vecs]

    @staticmethod
    def _ranked(scores: list[float]) -> list[int]:
        return sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)

    def search(self, query: str, mode: str = "keyword", top_k: int = 4) -> list[Chunk]:
        if mode == "none" or not self.chunks:
            return []
        ks = self._keyword_scores(query)
        if mode == "keyword":
            order = self._ranked(ks)
        elif mode == "vector":
            order = self._ranked(self._vector_scores(query))
        elif mode == "hybrid":
            krank = {i: r for r, i in enumerate(self._ranked(ks))}
            vrank = {i: r for r, i in enumerate(self._ranked(self._vector_scores(query)))}
            rrf = [
                1.0 / (60 + krank[i]) + 1.0 / (60 + vrank[i])
                for i in range(len(self.chunks))
            ]
            order = self._ranked(rrf)
        else:
            raise ValueError(f"unknown retrieval mode: {mode}")
        return [self.chunks[i] for i in order[:top_k] if ks[i] > 0 or mode != "keyword"] or [
            self.chunks[i] for i in order[:top_k]
        ]
