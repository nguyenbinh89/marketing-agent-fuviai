"""
FuviAI Marketing Agent — Vector Store
ChromaDB wrapper với fallback in-memory khi ChromaDB chưa sẵn sàng.
"""

from __future__ import annotations

import hashlib
from typing import Any
from loguru import logger

from backend.config.settings import get_settings

# Lazy import — tránh crash khi chromadb chưa tương thích
try:
    import chromadb
    from chromadb.utils import embedding_functions
    _CHROMA_AVAILABLE = True
except Exception as e:
    logger.warning(f"ChromaDB không khả dụng, dùng in-memory store: {e}")
    _CHROMA_AVAILABLE = False


class _InMemoryStore:
    """Fallback store đơn giản khi ChromaDB chưa sẵn sàng."""

    def __init__(self):
        self._docs: list[dict] = []

    def upsert(self, ids, documents, metadatas):
        existing_ids = {d["id"] for d in self._docs}
        for doc_id, text, meta in zip(ids, documents, metadatas):
            if doc_id not in existing_ids:
                self._docs.append({"id": doc_id, "text": text, **meta})

    def count(self):
        return len(self._docs)

    def query(self, query_texts, n_results, **kwargs):
        """Tìm kiếm đơn giản bằng keyword matching (thay thế vector search)."""
        query = query_texts[0].lower()
        scored = []
        for doc in self._docs:
            score = sum(1 for word in query.split() if word in doc["text"].lower())
            scored.append((score, doc))
        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[:n_results]
        return {
            "documents": [[d["text"] for _, d in top]],
            "metadatas": [[{k: v for k, v in d.items() if k not in ("id", "text")} for _, d in top]],
            "distances": [[1.0 - s * 0.1 for s, _ in top]],
        }

    def delete(self):
        self._docs = []


class VectorStore:
    """
    Vector store cho FuviAI knowledge base.
    Dùng ChromaDB nếu khả dụng, fallback sang in-memory store.

    Usage:
        store = VectorStore()
        store.add_documents([{"text": "...", "source": "cafef.vn", "date": "2026-03-05"}])
        results = store.search("xu hướng FMCG Việt Nam 2026", n_results=5)
    """

    def __init__(self):
        self.settings = get_settings()
        self._use_chroma = _CHROMA_AVAILABLE

        if self._use_chroma:
            self._client = chromadb.PersistentClient(
                path=self.settings.chroma_persist_dir
            )
            self._embed_fn = embedding_functions.DefaultEmbeddingFunction()
            self._collection = self._client.get_or_create_collection(
                name=self.settings.chroma_collection,
                embedding_function=self._embed_fn,
                metadata={"description": "FuviAI marketing knowledge base VN"},
            )
            logger.info(
                f"VectorStore (ChromaDB) initialized | "
                f"collection={self.settings.chroma_collection} | docs={self._collection.count()}"
            )
        else:
            self._store = _InMemoryStore()
            logger.info("VectorStore (in-memory) initialized")

    def add_documents(self, documents: list[dict[str, Any]]) -> int:
        if not documents:
            return 0

        ids, texts, metadatas = [], [], []
        for doc in documents:
            text = doc.get("text", "").strip()
            if not text:
                continue
            doc_id = hashlib.md5(text.encode()).hexdigest()
            ids.append(doc_id)
            texts.append(text)
            metadatas.append({
                "source": doc.get("source", "unknown"),
                "date": doc.get("date", ""),
                "category": doc.get("category", "general"),
                "title": doc.get("title", ""),
            })

        if not ids:
            return 0

        if self._use_chroma:
            self._collection.upsert(ids=ids, documents=texts, metadatas=metadatas)
        else:
            self._store.upsert(ids=ids, documents=texts, metadatas=metadatas)

        logger.info(f"Added {len(ids)} documents to VectorStore")
        return len(ids)

    def search(
        self,
        query: str,
        n_results: int = 5,
        category_filter: str | None = None,
    ) -> list[dict[str, Any]]:
        if self._use_chroma:
            total = self._collection.count()
            if total == 0:
                return []
            where = {"category": category_filter} if category_filter else None
            results = self._collection.query(
                query_texts=[query],
                n_results=min(n_results, total),
                where=where,
                include=["documents", "metadatas", "distances"],
            )
        else:
            total = self._store.count()
            if total == 0:
                return []
            results = self._store.query(
                query_texts=[query],
                n_results=min(n_results, total),
            )

        output = []
        if results["documents"] and results["documents"][0]:
            for text, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            ):
                output.append({
                    "text": text,
                    "source": meta.get("source", ""),
                    "date": meta.get("date", ""),
                    "category": meta.get("category", ""),
                    "title": meta.get("title", ""),
                    "distance": round(dist, 4),
                })
        return output

    def format_context_for_prompt(self, query: str, n_results: int = 5) -> str:
        results = self.search(query, n_results=n_results)
        if not results:
            return ""

        lines = ["**Context từ knowledge base:**\n"]
        for i, r in enumerate(results, 1):
            source_info = f"[{r['source']}]" if r["source"] else ""
            date_info = f"({r['date']})" if r["date"] else ""
            lines.append(f"{i}. {source_info}{date_info} {r['text'][:500]}\n")
        return "\n".join(lines)

    @property
    def doc_count(self) -> int:
        if self._use_chroma:
            return self._collection.count()
        return self._store.count()

    def clear(self) -> None:
        if self._use_chroma:
            self._client.delete_collection(self.settings.chroma_collection)
            self._collection = self._client.get_or_create_collection(
                name=self.settings.chroma_collection,
                embedding_function=self._embed_fn,
            )
        else:
            self._store.delete()
        logger.warning("VectorStore cleared")
