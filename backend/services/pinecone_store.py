from __future__ import annotations

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
        if not settings.PINECONE_API_KEY:
            raise ValueError("Missing PINECONE_API_KEY in environment.")

        self.client = Pinecone(api_key=settings.PINECONE_API_KEY)
        self.index_name = settings.PINECONE_INDEX_NAME
        self.namespace = settings.PINECONE_NAMESPACE
        self._ensure_index()
        self.index = self.client.Index(self.index_name)

    def _ensure_index(self) -> None:
        indexes = self.client.list_indexes()
        if hasattr(indexes, "names"):
            existing = set(indexes.names())
        else:
            existing = {index["name"] for index in indexes}
        if self.index_name in existing:
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
        vectors = [
            {
                "id": record.record_id,
                "values": record.vector,
                "metadata": record.metadata,
            }
            for record in records
        ]
        self.index.upsert(vectors=vectors, namespace=self.namespace)

    def query(
        self, vector: list[float], top_k: int = 5, filter_dict: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        return self.index.query(
            vector=vector,
            top_k=top_k,
            namespace=self.namespace,
            include_metadata=True,
            filter=filter_dict,
        )

    def delete_records(self, record_ids: list[str]) -> None:
        self.index.delete(ids=record_ids, namespace=self.namespace)

    def list_record_ids(self, prefix: str = "", page_limit: int = 100) -> list[str]:
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

    def fetch_records(self, record_ids: list[str]) -> dict[str, Any]:
        if not record_ids:
            return {}

        response = self.index.fetch(ids=record_ids, namespace=self.namespace)
        if hasattr(response, "vectors"):
            return dict(response.vectors)
        if isinstance(response, dict):
            return dict(response.get("vectors", {}))
        return {}

    def delete_by_note_id(self, note_id: str) -> None:
        self.index.delete(filter={"note_id": {"$eq": note_id}}, namespace=self.namespace)
