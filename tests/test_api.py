# Description: API-level pytest coverage for health, listing, detail, rename, delete, and summarize.
# This file is part of the SprintStudy project.

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pytest

from backend import main as api_main


class FakePineconeStore:
    records: dict[str, dict] = {}

    def __init__(self) -> None:
        """Create in-memory fake store for API tests."""
        pass

    def list_record_ids(self, prefix: str = "", page_limit: int = 100) -> list[str]:
        """Return sorted record ids, optionally filtered by prefix."""
        ids = sorted(self.records.keys())
        if prefix:
            ids = [rid for rid in ids if rid.startswith(prefix)]
        return ids

    def fetch_records(self, record_ids: list[str], batch_size: int = 100) -> dict[str, dict]:
        """Fetch fake records by id."""
        return {rid: self.records[rid] for rid in record_ids if rid in self.records}

    def fetch_note_summary(self, note_id: str) -> str | None:
        """Load fake persisted summary markdown."""
        rec = self.records.get(f"{note_id}:summary")
        if not rec:
            return None
        return rec.get("metadata", {}).get("summary_markdown")

    def upsert_note_summary(self, note_id: str, filename: str, summary_markdown: str) -> None:
        """Store/overwrite fake summary record."""
        self.records[f"{note_id}:summary"] = {
            "metadata": {
                "note_id": note_id,
                "filename": filename,
                "source_type": "note_summary",
                "summary_markdown": summary_markdown,
            },
            "values": [1e-6],
        }

    def rename_note(self, note_id: str, filename: str) -> int:
        """Rename all fake records for one note id."""
        updated = 0
        for rid, rec in self.records.items():
            if not rid.startswith(f"{note_id}:"):
                continue
            rec.setdefault("metadata", {})["filename"] = filename
            updated += 1
        return updated

    def delete_by_note_id(self, note_id: str) -> None:
        """Delete all fake records belonging to one note."""
        for rid in list(self.records.keys()):
            if rid.startswith(f"{note_id}:"):
                del self.records[rid]


class FakeStudyNoteSummarizer:
    def __init__(
        self,
        embedding_provider: str | None = None,
        embedding_model: str | None = None,
        generation_provider: str | None = None,
        generation_model: str | None = None,
    ) -> None:
        """Configure predictable fake model metadata."""
        self.embedding_provider = embedding_provider or "gemini"
        self.embedding_model = embedding_model or "models/gemini-embedding-001"
        self.generation_provider = generation_provider or "gemini"
        self._generation_model = generation_model or "gemini-2.5-flash"

    def summarize_and_store(self, file_path: Path, filename: str) -> dict:
        """Return a stable summarize result for route tests."""
        return {
            "note_id": "new-note",
            "filename": filename,
            "chunks": 1,
            "summary": "# One-Sentence Overview\nA short summary.",
            "stored_to_pinecone": True,
        }


@pytest.fixture()
def client(monkeypatch, tmp_path):
    """Provide Flask test client wired to fake Pinecone/service layers."""
    api_main.app.config.update(TESTING=True)
    api_main.settings.STUDY_NOTES_DIR = tmp_path
    api_main.settings.PINECONE_API_KEY = "test-key"
    FakePineconeStore.records = {
        "note-1:0": {
            "metadata": {
                "filename": "alpha.pdf",
                "created_at": "2026-04-08T12:00:00Z",
                "chunk_index": 0,
                "chunk_text": "Alpha first chunk",
                "stored_file": "alpha-local.pdf",
            },
            "values": [0.1, 0.2, 0.3],
        },
        "note-1:1": {
            "metadata": {
                "filename": "alpha.pdf",
                "created_at": "2026-04-08T12:00:00Z",
                "chunk_index": 1,
                "chunk_text": "Alpha second chunk",
                "stored_file": "alpha-local.pdf",
            },
            "values": [0.3, 0.2, 0.1],
        },
        "note-1:summary": {
            "metadata": {
                "note_id": "note-1",
                "filename": "alpha.pdf",
                "summary_markdown": "# One-Sentence Overview\nAlpha summary",
            },
            "values": [1e-6],
        },
    }

    (tmp_path / "alpha-local.pdf").write_bytes(b"fake-pdf")

    monkeypatch.setattr(api_main, "PineconeStore", FakePineconeStore)
    monkeypatch.setattr(api_main, "StudyNoteSummarizer", FakeStudyNoteSummarizer)
    return api_main.app.test_client()


def test_health(client):
    """Health endpoint should always return ok."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


def test_list_notes(client):
    """List endpoint should return one grouped note card."""
    resp = client.get("/api/study-notes")
    assert resp.status_code == 200
    notes = resp.get_json()["notes"]
    assert len(notes) == 1
    assert notes[0]["note_id"] == "note-1"
    assert notes[0]["chunk_count"] == 2
    assert notes[0]["local_file_exists"] is True


def test_get_note_detail_includes_summary(client):
    """Detail endpoint should include chunks and saved summary markdown."""
    resp = client.get("/api/study-notes/note-1")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["note_id"] == "note-1"
    assert body["chunk_count"] == 2
    assert body["summary_markdown"].startswith("# One-Sentence Overview")
    assert body["chunks"][0]["chunk_text"] == "Alpha first chunk"


def test_rename_note(client):
    """Rename endpoint should update filename metadata for note records."""
    resp = client.patch("/api/study-notes/note-1", json={"filename": "renamed.pdf"})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["filename"] == "renamed.pdf"
    assert body["updated_records"] == 3

    detail = client.get("/api/study-notes/note-1").get_json()
    assert detail["filename"] == "renamed.pdf"


def test_delete_note_removes_local_file_and_records(client):
    """Delete endpoint should remove fake records and linked local file."""
    resp = client.delete("/api/study-notes/note-1")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["note_id"] == "note-1"
    assert body["deleted_pinecone_records"] == 2
    assert len(body["deleted_local_files"]) == 1

    missing = client.get("/api/study-notes/note-1")
    assert missing.status_code == 404


def test_summarize_upload(client):
    """Summarize upload endpoint should return fake summary payload."""
    data = {
        "file": (BytesIO(b"hello world"), "hello.txt"),
    }
    resp = client.post("/api/study-notes/summarize", data=data, content_type="multipart/form-data")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["note_id"] == "new-note"
    assert body["filename"] == "hello.txt"
    assert body["stored_to_pinecone"] is True
