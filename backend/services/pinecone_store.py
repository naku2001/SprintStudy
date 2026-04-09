# Description: Pinecone data access layer for vectors, metadata, and saved summaries.

from __future__ import annotations

import json
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Any, Optional

from pinecone import Pinecone, ServerlessSpec

from backend.config.settings import settings


@dataclass
class PineconeRecord:
    """Generic record for storing note chunks or generated artifacts."""

    record_id: str
    vector: list[float]
    metadata: dict[str, Any]


class PineconeStore:
    """Single data gateway for vectors + metadata in Pinecone."""

    def __init__(self) -> None:
        """Create Pinecone client, ensure index exists, and bind namespace."""
        if not settings.PINECONE_API_KEY:
            raise ValueError("Missing PINECONE_API_KEY in environment.")

        self.client = Pinecone(api_key=settings.PINECONE_API_KEY)
        self.index_name = settings.PINECONE_INDEX_NAME
        self.namespace = settings.PINECONE_NAMESPACE
        self._ensure_index()
        self.index = self.client.Index(self.index_name)

    def _ensure_index(self) -> None:
        """Create index when missing, or recreate when configured dimension differs."""
        indexes = self.client.list_indexes()
        if hasattr(indexes, "names"):
            existing = set(indexes.names())
        else:
            existing = {index["name"] for index in indexes}

        if self.index_name in existing:
            desc = self.client.describe_index(self.index_name)
            existing_dim = getattr(desc, "dimension", None)
            if existing_dim is not None and existing_dim != settings.EMBEDDING_DIMENSION:
                # Dimension mismatch — delete the stale index and recreate
                self.client.delete_index(self.index_name)
            else:
                return

        self.client.create_index(
            name=self.index_name,
            dimension=settings.EMBEDDING_DIMENSION,
            metric="cosine",
            spec=ServerlessSpec(
                cloud=settings.PINECONE_CLOUD,
                region=settings.PINECONE_REGION,
            ),
        )

    def upsert_records(self, records: list[PineconeRecord]) -> None:
        """Upsert chunk records using size-aware batching to avoid API limits."""
        vectors = [
            {
                "id": record.record_id,
                "values": record.vector,
                "metadata": record.metadata,
            }
            for record in records
        ]
        if not vectors:
            return

        max_records = max(1, int(settings.PINECONE_UPSERT_MAX_RECORDS))
        max_bytes = max(200_000, int(settings.PINECONE_UPSERT_MAX_BYTES))

        batch: list[dict[str, Any]] = []
        batch_bytes = 0

        for vec in vectors:
            payload_size = len(json.dumps(vec, ensure_ascii=False))

            # If one record is extremely large, send it alone and let server decide.
            if payload_size >= max_bytes:
                if batch:
                    self.index.upsert(vectors=batch, namespace=self.namespace)
                    batch = []
                    batch_bytes = 0
                self.index.upsert(vectors=[vec], namespace=self.namespace)
                continue

            exceed_records = len(batch) >= max_records
            exceed_bytes = batch and (batch_bytes + payload_size > max_bytes)
            if exceed_records or exceed_bytes:
                self.index.upsert(vectors=batch, namespace=self.namespace)
                batch = []
                batch_bytes = 0

            batch.append(vec)
            batch_bytes += payload_size

        if batch:
            self.index.upsert(vectors=batch, namespace=self.namespace)

    def query(
        self, vector: list[float], top_k: int = 5, filter_dict: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """Query nearest vectors from configured namespace."""
        return self.index.query(
            vector=vector,
            top_k=top_k,
            namespace=self.namespace,
            include_metadata=True,
            filter=filter_dict,
        )

    def delete_records(self, record_ids: list[str]) -> None:
        """Delete records by explicit id list."""
        self.index.delete(ids=record_ids, namespace=self.namespace)

    def list_record_ids(self, prefix: str = "", page_limit: int = 100) -> list[str]:
        """List record ids in namespace with optional prefix filter."""
        if page_limit <= 0:
            page_limit = 1
        if page_limit >= 100:
            page_limit = 99
        record_ids: list[str] = []
        for page_ids in self.index.list(
            prefix=prefix,
            limit=page_limit,
            namespace=self.namespace,
        ):
            record_ids.extend(page_ids)
        return record_ids

    def fetch_records(self, record_ids: list[str], batch_size: int = 100) -> dict[str, Any]:
        """Fetch records in batches and merge SDK responses."""
        if not record_ids:
            return {}

        merged: dict[str, Any] = {}
        size = max(1, min(batch_size, 200))
        for i in range(0, len(record_ids), size):
            chunk_ids = record_ids[i : i + size]
            response = self.index.fetch(ids=chunk_ids, namespace=self.namespace)
            if hasattr(response, "vectors"):
                merged.update(dict(response.vectors))
            elif isinstance(response, dict):
                merged.update(dict(response.get("vectors", {})))
        return merged

    def rename_note(self, note_id: str, filename: str) -> int:
        """Update filename metadata on all records belonging to one note."""
        record_ids = self.list_record_ids(prefix=f"{note_id}:")
        if not record_ids:
            return 0

        updated = 0
        for record_id in record_ids:
            self.index.update(
                id=record_id,
                set_metadata={"filename": filename},
                namespace=self.namespace,
            )
            updated += 1
        return updated

    def upsert_note_summary(self, note_id: str, filename: str, summary_markdown: str) -> None:
        """Store latest markdown summary as a dedicated per-note record."""
        dim = int(settings.EMBEDDING_DIMENSION)
        # Pinecone dense vectors cannot be all-zero.
        values = [0.0] * dim
        if dim > 0:
            values[0] = 1e-6
        record = {
            "id": f"{note_id}:summary",
            "values": values,
            "metadata": {
                "note_id": note_id,
                "filename": filename,
                "source_type": "note_summary",
                "summary_markdown": summary_markdown,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
        }
        self.index.upsert(vectors=[record], namespace=self.namespace)

    def fetch_note_summary(self, note_id: str) -> Optional[str]:
        """Load persisted summary markdown for one note if available."""
        response = self.index.fetch(ids=[f"{note_id}:summary"], namespace=self.namespace)
        vectors: dict[str, Any] = {}
        if hasattr(response, "vectors"):
            vectors = dict(response.vectors)
        elif isinstance(response, dict):
            vectors = dict(response.get("vectors", {}))
        raw = vectors.get(f"{note_id}:summary")
        if raw is None:
            return None
        metadata = getattr(raw, "metadata", None)
        if isinstance(raw, dict):
            metadata = raw.get("metadata", metadata)
        if not isinstance(metadata, dict):
            return None
        text = metadata.get("summary_markdown")
        return str(text) if text else None

    def delete_by_note_id(self, note_id: str) -> None:
        """Delete all records linked to a note via metadata filter."""
        self.index.delete(filter={"note_id": {"$eq": note_id}}, namespace=self.namespace)
