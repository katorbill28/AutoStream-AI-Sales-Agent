from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List


@dataclass
class Chunk:
    source: str
    text: str


class KnowledgeBase:
    def __init__(self, folder: Path) -> None:
        self.folder = folder
        self.chunks = self._load_chunks()

    def _load_chunks(self) -> List[Chunk]:
        chunks: List[Chunk] = []
        for path in sorted(self.folder.glob("*.md")):
            content = path.read_text(encoding="utf-8")
            for block in [part.strip() for part in content.split("\n\n") if part.strip()]:
                chunks.append(Chunk(source=path.name, text=block))
        return chunks

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        return set(re.findall(r"[a-zA-Z0-9']+", text.lower()))

    def retrieve(self, query: str, top_k: int = 3) -> List[Chunk]:
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        scored = []
        for chunk in self.chunks:
            chunk_tokens = self._tokenize(chunk.text)
            overlap = len(query_tokens & chunk_tokens)
            if overlap:
                scored.append((overlap, len(chunk.text), chunk))

        scored.sort(key=lambda item: (-item[0], item[1]))
        return [chunk for _, _, chunk in scored[:top_k]]

    def sources(self) -> Iterable[str]:
        for chunk in self.chunks:
            yield chunk.source

