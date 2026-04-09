from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any
from uuid import uuid4

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from flask import Flask, Response, jsonify, request, stream_with_context
from flask import render_template
from flask_cors import CORS

from backend.config.settings import settings
from backend.services.pinecone_store import PineconeStore
from backend.services.study_note_service import StudyNoteSummarizer

ALLOWED_EXTENSIONS = {".pdf", ".txt"}

app = Flask(__name__)
CORS(app)


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


def _json_error(message: str, status: int = 400):
    return jsonify({"detail": message}), status


def _get_upload_or_error():
    uploaded_file = request.files.get("file")
    if uploaded_file is None:
        return None, _json_error("Missing file field in multipart form data.", 400)
    return uploaded_file, None


def _save_uploaded_file(uploaded_file):
    filename = uploaded_file.filename or "uploaded_note"
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        return None, None, _json_error("Only .pdf and .txt files are supported.", 400)

    content = uploaded_file.read()
    if not content:
        return None, None, _json_error("Uploaded file is empty.", 400)

    upload_id = str(uuid4())
    save_path = settings.STUDY_NOTES_DIR / f"{upload_id}{suffix}"
    save_path.write_bytes(content)
    return filename, save_path, None


def _get_embedding_overrides() -> tuple[str | None, str | None]:
    provider = (request.form.get("embedding_provider") or "").strip().lower() or None
    model = (request.form.get("embedding_model") or "").strip() or None
    return provider, model


def _get_generation_overrides() -> tuple[str | None, str | None]:
    provider = (request.form.get("generation_provider") or "").strip().lower() or None
    model = (request.form.get("generation_model") or "").strip() or None
    return provider, model


def _resolve_unique_filename(original_filename: str) -> str:
    if not settings.PINECONE_API_KEY:
        return original_filename
    try:
        store = PineconeStore()
        record_ids = store.list_record_ids()
        chunk_ids = [rid for rid in record_ids if _is_chunk_record_id(rid)]
        if not chunk_ids:
            return original_filename
        first_by_note: dict[str, str] = {}
        for rid in chunk_ids:
            note_id = rid.split(":", 1)[0]
            if note_id not in first_by_note or _chunk_index(rid) < _chunk_index(first_by_note[note_id]):
                first_by_note[note_id] = rid
        first_records = store.fetch_records(list(first_by_note.values()))
        existing_lower: set[str] = set()
        for rid in first_by_note.values():
            raw = first_records.get(rid)
            if raw is None:
                continue
            normalized = _normalize_vector_record(rid, raw)
            name = str(normalized["metadata"].get("filename", "")).strip()
            if name:
                existing_lower.add(name.lower())
        candidate = original_filename.strip() or "uploaded_note"
        if candidate.lower() not in existing_lower:
            return candidate
        p = Path(candidate)
        stem = p.stem or "uploaded_note"
        suffix = p.suffix
        n = 1
        while True:
            trial = f"{stem}({n}){suffix}"
            if trial.lower() not in existing_lower:
                return trial
            n += 1
    except Exception:
        return original_filename


@app.post("/api/study-notes/summarize")
def summarize_study_note():
    uploaded_file, err = _get_upload_or_error()
    if err:
        return err

    filename, save_path, err = _save_uploaded_file(uploaded_file)
    if err:
        return err
    filename = _resolve_unique_filename(filename)
    embedding_provider, embedding_model = _get_embedding_overrides()
    generation_provider, generation_model = _get_generation_overrides()

    try:
        service = StudyNoteSummarizer(
            embedding_provider=embedding_provider,
            embedding_model=embedding_model,
            generation_provider=generation_provider,
            generation_model=generation_model,
        )
        result = service.summarize_and_store(file_path=save_path, filename=filename)
        if result.get("stored_to_pinecone") and result.get("summary"):
            PineconeStore().upsert_note_summary(
                note_id=str(result.get("note_id", "")),
                filename=str(result.get("filename", filename)),
                summary_markdown=str(result.get("summary", "")),
            )
        return jsonify(result)
    except ValueError as exc:
        return _json_error(str(exc), 400)
    except Exception as exc:  # noqa: BLE001
        return _json_error(f"Failed to summarize note: {exc}", 500)


def _sse(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


class _StreamMarkdownCleaner:
    def __init__(self) -> None:
        self._carry = ""

    def clean(self, text: str) -> str:
        if not text:
            return ""
        combined = self._carry + text
        self._carry = ""
        if combined.endswith("*"):
            self._carry = "*"
            combined = combined[:-1]
        cleaned = combined.replace("**", "")
        # Keep headings/bullets readable when models stream compact text.
        cleaned = re.sub(r"(?<!\n)(##\s)", r"\n## ", cleaned)
        cleaned = re.sub(r"(?<!\n)(#\s)", r"\n# ", cleaned)
        cleaned = re.sub(r"(## [^\n]+?)\s*-\s", r"\1\n- ", cleaned)
        return cleaned

    def flush(self) -> str:
        tail = self._carry
        self._carry = ""
        return tail.replace("**", "")


def _emit_summary_stream(summary_iter, cleaner: _StreamMarkdownCleaner):
    buffer: list[str] = []
    for item in summary_iter:
        msg_type = item.get("type")
        if msg_type == "token":
            clean_text = cleaner.clean(item.get("text", ""))
            if clean_text:
                buffer.append(clean_text)
                yield _sse("token", {"text": clean_text})
        elif msg_type == "status":
            yield _sse("status", {"message": item.get("message", "")})
        elif msg_type == "done":
            tail = cleaner.flush()
            if tail:
                buffer.append(tail)
                yield _sse("token", {"text": tail})
            yield _sse("done", {"ok": True})
    return "".join(buffer).strip()


@app.post("/api/study-notes/summarize-stream")
def summarize_study_note_stream():
    uploaded_file, err = _get_upload_or_error()
    if err:
        return err
    filename, save_path, err = _save_uploaded_file(uploaded_file)
    if err:
        return err
    filename = _resolve_unique_filename(filename)
    embedding_provider, embedding_model = _get_embedding_overrides()
    generation_provider, generation_model = _get_generation_overrides()

    @stream_with_context
    def event_stream():
        try:
            cleaner = _StreamMarkdownCleaner()
            service = StudyNoteSummarizer(
                embedding_provider=embedding_provider,
                embedding_model=embedding_model,
                generation_provider=generation_provider,
                generation_model=generation_model,
            )
            yield _sse("status", {"message": "Extracting chunks..."})
            chunks = service.extract_chunks(save_path)
            if not chunks:
                yield _sse("error", {"detail": "No usable text extracted from the uploaded file."})
                return

            yield _sse("status", {"message": f"Embedding {len(chunks)} chunks..."})
            vectors = service.embed_chunks(chunks)
            note_id = save_path.stem
            stored = service.store_chunks(
                note_id=note_id,
                filename=filename,
                stored_file=save_path.name,
                chunks=chunks,
                vectors=vectors,
            )
            yield _sse(
                "meta",
                {
                    "note_id": note_id,
                    "filename": filename,
                    "chunks": len(chunks),
                    "stored_to_pinecone": stored,
                    "embedding_provider": service.embedding_provider,
                    "embedding_model": service.embedding_model,
                    "generation_provider": service.generation_provider,
                    "generation_model": service.current_generation_model(),
                },
            )
            summary_text = yield from _emit_summary_stream(
                service.summarize_adaptive_stream(chunks), cleaner
            )
            if stored and summary_text:
                PineconeStore().upsert_note_summary(
                    note_id=note_id,
                    filename=filename,
                    summary_markdown=summary_text,
                )
        except Exception as exc:  # noqa: BLE001
            yield _sse("error", {"detail": f"Failed to summarize note: {exc}"})

    return Response(event_stream(), mimetype="text/event-stream")


def _chunk_index(record_id: str) -> int:
    if ":" not in record_id:
        return -1
    idx_str = record_id.rsplit(":", 1)[1]
    return int(idx_str) if idx_str.isdigit() else -1


def _is_chunk_record_id(record_id: str) -> bool:
    if ":" not in record_id:
        return False
    return record_id.rsplit(":", 1)[1].isdigit()


def _normalize_vector_record(record_id: str, record_obj: Any) -> dict[str, Any]:
    metadata = getattr(record_obj, "metadata", None)
    values = getattr(record_obj, "values", None)

    if isinstance(record_obj, dict):
        metadata = record_obj.get("metadata", metadata)
        values = record_obj.get("values", values)

    metadata = metadata or {}
    values = values or []
    return {
        "id": record_id,
        "metadata": metadata,
        "values": values,
    }


def _load_note_records(store: PineconeStore, note_id: str) -> tuple[list[str], dict[str, Any]]:
    record_ids = store.list_record_ids(prefix=f"{note_id}:")
    record_ids = [rid for rid in record_ids if _is_chunk_record_id(rid)]
    record_ids.sort(key=_chunk_index)
    records = store.fetch_records(record_ids)
    return record_ids, records


def _load_note_chunks(store: PineconeStore, note_id: str):
    record_ids, records = _load_note_records(store, note_id)
    if not record_ids:
        return None, None, None

    filename = "unknown"
    chunk_texts: list[str] = []
    for i, record_id in enumerate(record_ids):
        raw = records.get(record_id)
        if raw is None:
            continue
        normalized = _normalize_vector_record(record_id, raw)
        metadata = normalized["metadata"]
        if i == 0:
            filename = metadata.get("filename", "unknown")
        text = (metadata.get("chunk_text") or "").strip()
        if text:
            chunk_texts.append(text)
    return record_ids, filename, chunk_texts


@app.get("/api/study-notes")
def list_study_notes():
    try:
        store = PineconeStore()
        record_ids = store.list_record_ids()
        if not record_ids:
            return jsonify({"notes": []})

        groups: dict[str, list[str]] = {}
        for record_id in record_ids:
            if not _is_chunk_record_id(record_id):
                continue
            note_id = record_id.split(":", 1)[0]
            groups.setdefault(note_id, []).append(record_id)

        if not groups:
            return jsonify({"notes": []})

        first_ids = []
        for note_id, ids in groups.items():
            best_id = min(ids, key=_chunk_index)
            first_ids.append((note_id, best_id))

        first_records = store.fetch_records([item[1] for item in first_ids])
        notes = []
        for note_id, first_id in first_ids:
            raw = first_records.get(first_id)
            if raw is None:
                continue
            normalized = _normalize_vector_record(first_id, raw)
            metadata = normalized["metadata"]

            stored_file = metadata.get("stored_file", "")
            local_path = str((settings.STUDY_NOTES_DIR / stored_file).resolve()) if stored_file else ""
            local_exists = bool(stored_file) and (settings.STUDY_NOTES_DIR / stored_file).exists()

            notes.append(
                {
                    "note_id": note_id,
                    "filename": metadata.get("filename", "unknown"),
                    "created_at": metadata.get("created_at"),
                    "chunk_count": len(groups.get(note_id, [])),
                    "local_file": stored_file,
                    "local_file_path": local_path,
                    "local_file_exists": local_exists,
                }
            )

        notes.sort(key=lambda n: n.get("created_at") or "", reverse=True)
        return jsonify({"notes": notes})
    except Exception as exc:  # noqa: BLE001
        return jsonify({"detail": f"Failed to list notes: {exc}"}), 500


@app.get("/api/study-notes/<note_id>")
def get_study_note_detail(note_id: str):
    include_full_values = request.args.get("include_full_values", "false").lower() == "true"
    try:
        store = PineconeStore()
        record_ids, records = _load_note_records(store, note_id)
        if not record_ids:
            return jsonify({"detail": f"note_id '{note_id}' not found."}), 404
        stored_summary = store.fetch_note_summary(note_id)

        chunks = []
        for record_id in record_ids:
            raw = records.get(record_id)
            if raw is None:
                continue
            normalized = _normalize_vector_record(record_id, raw)
            metadata = normalized["metadata"]
            values = normalized["values"]
            item = {
                "record_id": record_id,
                "chunk_index": metadata.get("chunk_index", _chunk_index(record_id)),
                "chunk_text": metadata.get("chunk_text", ""),
                "embedding_dim": len(values),
                "embedding_preview": values[:8],
            }
            if include_full_values:
                item["embedding_values"] = values
            chunks.append(item)

        first_meta = chunks[0] if chunks else {}
        filename = ""
        stored_file = ""
        if record_ids:
            first_raw = records.get(record_ids[0])
            if first_raw is not None:
                first_norm = _normalize_vector_record(record_ids[0], first_raw)
                filename = first_norm["metadata"].get("filename", "")
                stored_file = first_norm["metadata"].get("stored_file", "")

        return jsonify(
            {
                "note_id": note_id,
                "filename": filename,
                "stored_file": stored_file,
                "chunk_count": len(chunks),
                "summary_markdown": stored_summary,
                "chunks": chunks,
                "include_full_values": include_full_values,
                "sample_chunk_index": first_meta.get("chunk_index"),
            }
        )
    except Exception as exc:  # noqa: BLE001
        return jsonify({"detail": f"Failed to get note detail: {exc}"}), 500


@app.post("/api/study-notes/<note_id>/resummarize")
def resummarize_study_note(note_id: str):
    try:
        store = PineconeStore()
        record_ids, filename, chunk_texts = _load_note_chunks(store, note_id)
        if not record_ids:
            return _json_error(f"note_id '{note_id}' not found.", 404)

        if not chunk_texts:
            return _json_error("No chunk_text found for this note.", 400)

        summarizer = StudyNoteSummarizer()
        summary = summarizer.summarize_adaptive(chunk_texts)
        store.upsert_note_summary(note_id=note_id, filename=filename, summary_markdown=summary)
        return jsonify(
            {
                "note_id": note_id,
                "filename": filename,
                "chunks": len(chunk_texts),
                "summary": summary,
                "source": "pinecone_stored_chunks",
            }
        )
    except Exception as exc:  # noqa: BLE001
        return _json_error(f"Failed to re-summarize note: {exc}", 500)


@app.post("/api/study-notes/<note_id>/resummarize-stream")
def resummarize_study_note_stream(note_id: str):
    @stream_with_context
    def event_stream():
        try:
            cleaner = _StreamMarkdownCleaner()
            store = PineconeStore()
            record_ids, filename, chunk_texts = _load_note_chunks(store, note_id)
            if not record_ids:
                yield _sse("error", {"detail": f"note_id '{note_id}' not found."})
                return

            if not chunk_texts:
                yield _sse("error", {"detail": "No chunk_text found for this note."})
                return

            yield _sse(
                "meta",
                {
                    "note_id": note_id,
                    "filename": filename,
                    "chunks": len(chunk_texts),
                    "source": "pinecone_stored_chunks",
                },
            )
            summarizer = StudyNoteSummarizer()
            summary_text = yield from _emit_summary_stream(
                summarizer.summarize_adaptive_stream(chunk_texts), cleaner
            )
            if summary_text:
                store.upsert_note_summary(
                    note_id=note_id,
                    filename=filename,
                    summary_markdown=summary_text,
                )
        except Exception as exc:  # noqa: BLE001
            yield _sse("error", {"detail": f"Failed to re-summarize note: {exc}"})

    return Response(event_stream(), mimetype="text/event-stream")


@app.patch("/api/study-notes/<note_id>")
def rename_study_note(note_id: str):
    payload = request.get_json(silent=True) or {}
    new_filename = str(payload.get("filename", "")).strip()
    if not new_filename:
        return _json_error("filename is required.", 400)
    if len(new_filename) > 200:
        return _json_error("filename is too long (max 200 chars).", 400)

    try:
        store = PineconeStore()
        updated = store.rename_note(note_id=note_id, filename=new_filename)
        if updated == 0:
            return _json_error(f"note_id '{note_id}' not found.", 404)
        return jsonify({"note_id": note_id, "filename": new_filename, "updated_records": updated})
    except Exception as exc:  # noqa: BLE001
        return _json_error(f"Failed to rename note: {exc}", 500)


@app.delete("/api/study-notes/<note_id>")
def delete_study_note(note_id: str):
    try:
        store = PineconeStore()
        record_ids, _ = _load_note_records(store, note_id)
        if not record_ids:
            return jsonify({"detail": f"note_id '{note_id}' not found."}), 404

        stored_files = set()
        records = store.fetch_records(record_ids[:1])
        if record_ids:
            first_raw = records.get(record_ids[0])
            if first_raw is not None:
                first_norm = _normalize_vector_record(record_ids[0], first_raw)
                stored_file = first_norm["metadata"].get("stored_file")
                if stored_file:
                    stored_files.add(stored_file)

        store.delete_by_note_id(note_id)

        deleted_local_files = []
        for stored_file in stored_files:
            target = settings.STUDY_NOTES_DIR / stored_file
            if target.exists() and target.is_file():
                target.unlink()
                deleted_local_files.append(str(target.resolve()))

        return jsonify(
            {
                "note_id": note_id,
                "deleted_pinecone_records": len(record_ids),
                "deleted_local_files": deleted_local_files,
            }
        )
    except Exception as exc:  # noqa: BLE001
        return jsonify({"detail": f"Failed to delete note: {exc}"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
