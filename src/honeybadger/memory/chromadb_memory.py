import hashlib
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import chromadb
from chromadb.config import Settings
from chromadb.utils.embedding_functions import EmbeddingFunction

logger = logging.getLogger(__name__)


class SimpleTextEmbeddingFunction(EmbeddingFunction):
    def __call__(self, texts: List[str], **kwargs) -> List[List[float]]:
        embeddings: List[List[float]] = []
        for text in texts:
            digest = hashlib.sha256(text.encode("utf-8")).digest()
            embeddings.append([b / 255.0 for b in digest[:128]])
        return embeddings


class HoneyBadgerMemory:
    def __init__(self, persist_dir: Optional[str] = None, max_storage_mb: int = 1024) -> None:
        self.persist_dir = Path(persist_dir or Path(__file__).resolve().parents[2] / "memory_store")
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.max_storage_mb = max_storage_mb
        self.client = chromadb.Client(
            Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=str(self.persist_dir),
            )
        )
        self.collection = self.client.get_or_create_collection(
            name="honeybadger_memory",
            embedding_function=SimpleTextEmbeddingFunction(),
        )
        self._enforce_storage_limit()

    def _store_size_mb(self) -> float:
        total_bytes = sum(f.stat().st_size for f in self.persist_dir.rglob("*") if f.is_file())
        return total_bytes / 1024**2

    def _enforce_storage_limit(self) -> None:
        size_mb = self._store_size_mb()
        if size_mb > self.max_storage_mb:
            logger.warning(
                "HoneyBadgerMemory storage exceeded %s MB: %.2f MB, pruning now.",
                self.max_storage_mb,
                size_mb,
            )
            self.auto_prune()

    def save(self, role: str, text: str) -> None:
        item_id = hashlib.sha256(f"{datetime.utcnow().isoformat()}-{role}-{text}".encode("utf-8")).hexdigest()
        metadata = {
            "role": role,
            "created_at": datetime.utcnow().isoformat(),
        }
        self.collection.add(
            ids=[item_id],
            documents=[text],
            metadatas=[metadata],
        )
        self.client.persist()
        self._enforce_storage_limit()

    def auto_prune(self) -> None:
        raw = self.collection.get(include=["ids", "documents", "metadatas"])
        ids = raw.get("ids", [])
        documents = raw.get("documents", [])
        metadatas = raw.get("metadatas", [])

        if not ids:
            return

        prune_before = datetime.utcnow() - timedelta(days=7)
        old_ids: List[str] = []
        summary_texts: List[str] = []

        for item_id, document, metadata in zip(ids, documents, metadatas):
            created_at = metadata.get("created_at")
            try:
                record_time = datetime.fromisoformat(created_at)
            except Exception:
                continue
            if record_time < prune_before:
                old_ids.append(item_id)
                summary_texts.append(f"[{metadata.get('role', 'unknown')}] {document}")

        if not old_ids:
            return

        summary = self._summarize_texts(summary_texts)
        summary_id = hashlib.sha256(f"summary-{datetime.utcnow().isoformat()}".encode("utf-8")).hexdigest()
        self.collection.add(
            ids=[summary_id],
            documents=[summary],
            metadatas=[{"role": "summary", "created_at": datetime.utcnow().isoformat(), "summary_of": "weekly_prune"}],
        )
        self.collection.delete(ids=old_ids)
        self.client.persist()
        logger.info("Pruned %d old memory entries and created a summary.", len(old_ids))

    def _summarize_texts(self, texts: List[str]) -> str:
        if not texts:
            return ""
        combined = "\n".join(texts)
        sentences = combined.split(". ")
        summary_sentences = sentences[: min(8, len(sentences))]
        summary = ". ".join(summary_sentences).strip()
        if len(summary) > 1500:
            summary = summary[:1500].rsplit(" ", 1)[0] + "..."
        return f"Weekly memory summary: {summary}"
