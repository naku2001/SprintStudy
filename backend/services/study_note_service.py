from __future__ import annotations

import json
import random
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

import fitz  # PyMuPDF
import numpy as np
import requests
from google import genai
from google.genai import types

from backend.config.settings import settings
from backend.services.pinecone_store import PineconeRecord, PineconeStore

EMBED_MODEL = "models/gemini-embedding-001"
GEN_MODEL = "models/gemini-2.5-flash"
MARKDOWN_RULES = (
    "Rules:\n"
    "- Do not invent facts.\n"
    "- Stay faithful to the provided note.\n"
    "- Use Markdown headings with # and ## exactly as requested.\n"
    "- Do not use bold markers like ** anywhere in output.\n"
    "- Do not add any preface before the first heading.\n\n"
)

BULLET_RE = re.compile(
    r"""^\s*(?:[-*]|(?:\(?\d{1,3}\)?[.)])|(?:[A-Za-z][.)]))\s+"""
)


@dataclass
class LineInfo:
    text: str
    bbox: tuple[float, float, float, float]
    font_size: float
    is_bold: bool


class StudyNoteSummarizer:
    """Extract, embed, summarize, and persist study note chunks."""

    def __init__(
        self,
        embedding_provider: Optional[str] = None,
        embedding_model: Optional[str] = None,
        generation_provider: Optional[str] = None,
        generation_model: Optional[str] = None,
    ) -> None:
        self.client: Optional[genai.Client] = None
        self.embedding_provider = (embedding_provider or settings.EMBEDDING_PROVIDER).lower()
        self.embedding_model = embedding_model or settings.EMBEDDING_MODEL or EMBED_MODEL
        self.generation_provider = (generation_provider or settings.GENERATION_PROVIDER).lower()
        self.generation_model = generation_model or settings.GENERATION_MODEL or ""

    def _get_gemini_client(self) -> genai.Client:
        if not settings.GEMINI_API_KEY:
            raise ValueError("Missing GEMINI_API_KEY in environment.")
        if self.client is None:
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        return self.client

    def summarize_and_store(self, file_path: Path, filename: str) -> dict[str, Any]:
        chunks = self.extract_chunks(file_path)
        if not chunks:
            raise ValueError("No usable text extracted from the uploaded file.")

        vectors = self.embed_chunks(chunks)
        note_id = file_path.stem or str(uuid4())
        stored_to_pinecone = self.store_chunks(
            note_id=note_id,
            filename=filename,
            stored_file=str(file_path.name),
            chunks=chunks,
            vectors=vectors,
        )
        summary = self.summarize_adaptive(chunks)

        return {
            "note_id": note_id,
            "filename": filename,
            "chunks": len(chunks),
            "stored_to_pinecone": stored_to_pinecone,
            "embedding_provider": self.embedding_provider,
            "embedding_model": self.embedding_model,
            "generation_provider": self.generation_provider,
            "generation_model": self._resolved_generation_model(),
            "summary": summary,
        }

    def store_chunks(
        self,
        note_id: str,
        filename: str,
        stored_file: str,
        chunks: list[str],
        vectors: np.ndarray,
    ) -> bool:
        return self._store_in_pinecone(
            note_id=note_id,
            filename=filename,
            stored_file=stored_file,
            chunks=chunks,
            vectors=vectors,
        )

    def extract_chunks(
        self, file_path: Path, max_chars: Optional[int] = None, overlap: Optional[int] = None
    ) -> list[str]:
        max_chars = int(max_chars or settings.CHUNK_MAX_CHARS)
        overlap = int(overlap or settings.CHUNK_OVERLAP)
        max_chars = max(400, max_chars)
        overlap = max(0, min(overlap, max_chars - 1))
        suffix = file_path.suffix.lower()
        if suffix == ".pdf":
            blocks = self._extract_smart_blocks_from_pdf(file_path)
        elif suffix == ".txt":
            text = file_path.read_text(encoding="utf-8", errors="ignore")
            blocks = self._paragraph_blocks(text)
        else:
            raise ValueError("Only .pdf and .txt are supported.")

        return self._pack_blocks(blocks, max_chars=max_chars, overlap=overlap)

    def embed_chunks(self, chunks: list[str]) -> np.ndarray:
        if not chunks:
            return np.zeros((0, settings.EMBEDDING_DIMENSION), dtype=np.float32)

        provider = self.embedding_provider
        if provider == "huggingface":
            return self._embed_chunks_huggingface(chunks)
        if provider != "gemini":
            raise ValueError(
                "Unsupported EMBEDDING_PROVIDER. Use 'gemini' or 'huggingface'."
            )

        return self._embed_chunks_gemini(chunks)

    def _embed_chunks_gemini(self, chunks: list[str]) -> np.ndarray:
        embed_model = self.embedding_model or EMBED_MODEL
        max_batch = max(1, min(100, int(settings.GEMINI_EMBED_MAX_BATCH)))

        rows: list[list[float]] = []
        for i in range(0, len(chunks), max_batch):
            batch = chunks[i : i + max_batch]
            res = self._get_gemini_client().models.embed_content(
                model=embed_model,
                contents=batch,
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_DOCUMENT",
                    output_dimensionality=settings.EMBEDDING_DIMENSION,
                ),
            )
            rows.extend([e.values for e in res.embeddings])

        vectors = np.array(rows, dtype=np.float32)
        self._validate_embedding_dimensions(vectors)
        if vectors.shape[0] != len(chunks):
            raise RuntimeError(
                f"Embedding count mismatch: got {vectors.shape[0]}, expected {len(chunks)}."
            )
        return vectors

    def _embed_chunks_huggingface(self, chunks: list[str]) -> np.ndarray:
        model_id = self.embedding_model or "BAAI/bge-small-zh"
        if not settings.HUGGINGFACE_API_KEY:
            raise ValueError(
                "Missing HUGGINGFACE_API_KEY in environment for huggingface embeddings."
            )

        headers = {"Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}"}
        custom_url = settings.HUGGINGFACE_API_URL.strip()
        if custom_url:
            candidate_urls = [custom_url]
        else:
            # Hugging Face migrated shared inference traffic to router.huggingface.co.
            candidate_urls = [
                f"https://router.huggingface.co/hf-inference/pipeline/feature-extraction/{model_id}",
                f"https://router.huggingface.co/hf-inference/models/{model_id}",
            ]

        vectors: list[np.ndarray] = []
        for chunk in chunks:
            payload = self._embed_hf_chunk_with_fallback(
                chunk=chunk,
                candidate_urls=candidate_urls,
                headers=headers,
            )
            vectors.append(self._to_sentence_vector(payload))

        arr = np.array(vectors, dtype=np.float32)
        self._validate_embedding_dimensions(arr)
        return arr

    def _request_hf_embedding(
        self,
        candidate_urls: list[str],
        headers: dict[str, str],
        body: dict[str, Any],
    ) -> Any:
        last_error: Optional[Exception] = None
        for url in candidate_urls:
            try:
                return self._post_hf_embedding_with_retry(url=url, headers=headers, body=body)
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                # Try next endpoint variant.
                continue
        raise RuntimeError(
            f"All HuggingFace embedding endpoint variants failed. Last error: {last_error}"
        )

    def _embed_hf_chunk_with_fallback(
        self,
        chunk: str,
        candidate_urls: list[str],
        headers: dict[str, str],
    ) -> Any:
        # Some HF-hosted encoder models (including bge-small-zh) can error on
        # long sequences unless we force truncation; if needed, progressively
        # shorten the text and retry.
        candidate_texts = [chunk]
        if len(chunk) > 1200:
            candidate_texts.append(chunk[:1200])
        if len(chunk) > 900:
            candidate_texts.append(chunk[:900])
        if len(chunk) > 600:
            candidate_texts.append(chunk[:600])
        if len(chunk) > 450:
            candidate_texts.append(chunk[:450])

        last_error: Optional[Exception] = None
        seen: set[str] = set()
        for text in candidate_texts:
            if text in seen:
                continue
            seen.add(text)
            body = {
                "inputs": text,
                "parameters": {"truncation": True, "max_length": 512},
                "options": {"wait_for_model": True},
            }
            try:
                return self._request_hf_embedding(
                    candidate_urls=candidate_urls,
                    headers=headers,
                    body=body,
                )
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                # Keep trying shorter variants for sequence-length errors.
                msg = str(exc).lower()
                if "tensor a" not in msg and "max" not in msg and "length" not in msg:
                    continue

        raise RuntimeError(
            f"HuggingFace embedding failed after truncation retries. Last error: {last_error}"
        )

    def _post_hf_embedding_with_retry(
        self,
        url: str,
        headers: dict[str, str],
        body: dict[str, Any],
        max_attempts: int = 6,
        base_sleep: float = 1.0,
    ) -> Any:
        last_error: Optional[Exception] = None
        for attempt in range(1, max_attempts + 1):
            try:
                response = requests.post(url, headers=headers, json=body, timeout=90)
                if response.status_code < 400:
                    return response.json()

                error_text = response.text[:400]
                # Old API host has been sunset by Hugging Face.
                if response.status_code == 410 and "no longer supported" in error_text.lower():
                    raise ValueError(error_text)
                err = RuntimeError(
                    f"HuggingFace embedding API failed with status {response.status_code}: {error_text}"
                )
                if response.status_code in {408, 429, 500, 502, 503, 504}:
                    raise err
                raise ValueError(str(err))
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                if not self._is_transient_error(exc):
                    raise
                sleep_sec = min(20.0, base_sleep * (2 ** (attempt - 1)))
                sleep_sec *= 0.7 + random.random() * 0.6
                time.sleep(sleep_sec)

        raise RuntimeError(
            f"HuggingFace embedding API failed after retries. Last error: {last_error}"
        )

    @staticmethod
    def _to_sentence_vector(payload: Any) -> np.ndarray:
        if not isinstance(payload, list) or not payload:
            raise ValueError("Invalid embedding payload returned by API.")

        if all(isinstance(v, (int, float)) for v in payload):
            return np.array(payload, dtype=np.float32)

        if isinstance(payload[0], list):
            first = payload[0]
            if first and all(isinstance(v, (int, float)) for v in first):
                matrix = np.array(payload, dtype=np.float32)
                if matrix.ndim == 2:
                    # Some feature-extraction endpoints return token-level vectors.
                    return matrix.mean(axis=0)
                return matrix.reshape(-1).astype(np.float32)
            return StudyNoteSummarizer._to_sentence_vector(first)

        raise ValueError("Could not parse embedding payload into a sentence vector.")

    @staticmethod
    def _validate_embedding_dimensions(vectors: np.ndarray) -> None:
        if vectors.size == 0:
            return
        if vectors.ndim != 2:
            raise ValueError(f"Embeddings must be a 2D array, got shape={vectors.shape}.")
        actual = int(vectors.shape[1])
        expected = int(settings.EMBEDDING_DIMENSION)
        if actual != expected:
            raise ValueError(
                "Embedding dimension mismatch: "
                f"got {actual}, expected {expected}. "
                "Update EMBEDDING_DIMENSION (and Pinecone index) to match the selected embedding model."
            )

    def summarize_adaptive(self, chunks: list[str]) -> str:
        chunk_count = len(chunks)
        if self._should_use_single_pass(chunks):
            return self._clean_markdown_text(self._summarize_once(chunks))

        batches = self._build_summary_batches(chunks)
        batch_summaries = self._batch_summarize_chunks(batches)
        return self._clean_markdown_text(self._summarize_all(batch_summaries))

    def _store_in_pinecone(
        self,
        note_id: str,
        filename: str,
        stored_file: str,
        chunks: list[str],
        vectors: np.ndarray,
    ) -> bool:
        if not settings.PINECONE_API_KEY:
            return False

        store = PineconeStore()
        created_at = datetime.now(timezone.utc).isoformat()
        records: list[PineconeRecord] = []

        for idx, (chunk, vector) in enumerate(zip(chunks, vectors)):
            metadata = {
                "note_id": note_id,
                "filename": filename,
                "stored_file": stored_file,
                "chunk_index": idx,
                "chunk_text": chunk,
                "embedding_provider": self.embedding_provider,
                "embedding_model": self.embedding_model,
                "created_at": created_at,
                "source_type": "study_note",
            }
            record = PineconeRecord(
                record_id=f"{note_id}:{idx}",
                vector=vector.tolist(),
                metadata=metadata,
            )
            records.append(record)

        store.upsert_records(records)
        return True

    def _summarize_once(self, chunks: list[str]) -> str:
        prompt = self._build_single_pass_markdown_prompt(chunks)
        return self._generate_with_retry(prompt, temperature=0.2)

    def _build_summary_batches(self, chunks: list[str]) -> list[list[str]]:
        target_batches = max(1, int(settings.SUMMARY_BATCH_TARGET_COUNT))
        max_batch_chunks = max(1, int(settings.SUMMARY_BATCH_MAX_CHUNKS))
        max_batch_chars = max(1200, int(settings.SUMMARY_BATCH_MAX_CHARS))
        # Increase batch size ceiling to keep number of LLM calls small.
        max_batch_chunks = max(max_batch_chunks, (len(chunks) + target_batches - 1) // target_batches)

        batches: list[list[str]] = []
        current: list[str] = []
        current_chars = 0

        for chunk in chunks:
            chunk_len = len(chunk)
            would_exceed_chars = current and (current_chars + chunk_len > max_batch_chars)
            would_exceed_chunks = len(current) >= max_batch_chunks
            if would_exceed_chars or would_exceed_chunks:
                batches.append(current)
                current = []
                current_chars = 0

            current.append(chunk)
            current_chars += chunk_len

        if current:
            batches.append(current)
        return self._cap_batches_to_limit(batches, max_batches=max(1, int(settings.SUMMARY_MAX_BATCHES)))

    @staticmethod
    def _cap_batches_to_limit(batches: list[list[str]], max_batches: int) -> list[list[str]]:
        if len(batches) <= max_batches:
            return batches

        # Hard cap: merge adjacent batches so total count never exceeds max_batches.
        merged: list[list[str]] = []
        step = (len(batches) + max_batches - 1) // max_batches
        for i in range(0, len(batches), step):
            group = batches[i : i + step]
            merged_batch: list[str] = []
            for b in group:
                merged_batch.extend(b)
            merged.append(merged_batch)
        return merged[:max_batches]

    def _should_use_single_pass(self, chunks: list[str]) -> bool:
        if len(chunks) <= settings.SUMMARY_SINGLE_PASS_MAX_CHUNKS:
            return True
        total_chars = sum(len(c) for c in chunks)
        return total_chars <= max(2000, int(settings.SUMMARY_SINGLE_PASS_MAX_INPUT_CHARS))

    def _batch_summarize_chunks(self, batches: list[list[str]]) -> list[str]:
        summaries: list[str] = []
        sleep_seconds = max(0.0, settings.SUMMARY_BATCH_SLEEP_MS / 1000.0)
        total_batches = len(batches)
        chunk_start = 1
        for i, batch in enumerate(batches, start=1):
            joined = "\n\n".join([f"[CHUNK {chunk_start + j}]\n{c}" for j, c in enumerate(batch)])
            prompt = (
                "You are summarizing a batch of study-note excerpts.\n"
                "For each chunk, return 3-7 bullets with key concepts, definitions, and critical details.\n"
                "Include equations/numbers/dates if they exist.\n"
                "Do not invent missing information.\n\n"
                f"EXCERPTS:\n{joined}"
            )
            summaries.append(self._generate_with_retry(prompt, temperature=0.2))
            chunk_start += len(batch)
            if sleep_seconds > 0 and i < total_batches:
                time.sleep(sleep_seconds)
        return summaries

    def _summarize_all(self, batch_summaries: list[str]) -> str:
        prompt = self._build_final_markdown_prompt(batch_summaries)
        return self._generate_with_retry(prompt, temperature=0.2)

    def summarize_adaptive_stream(self, chunks: list[str]):
        chunk_count = len(chunks)
        if self._should_use_single_pass(chunks):
            yield {"type": "status", "message": "Small note detected. Streaming single-pass summary..."}
            prompt = self._build_single_pass_markdown_prompt(chunks)
            for text in self._generate_stream(prompt, temperature=0.2):
                yield {"type": "token", "text": text}
            yield {"type": "done"}
            return

        batches = self._build_summary_batches(chunks)
        total_batches = len(batches)
        yield {
            "type": "status",
            "message": (
                f"Preparing map-reduce summary ({chunk_count} chunks, {total_batches} batches)..."
            ),
        }
        batch_summaries: list[str] = []
        sleep_seconds = max(0.0, settings.SUMMARY_BATCH_SLEEP_MS / 1000.0)
        chunk_start = 1
        for i, batch in enumerate(batches, start=1):
            chunk_end = chunk_start + len(batch) - 1
            yield {
                "type": "status",
                "message": f"Summarizing batch {i}/{total_batches} (chunks {chunk_start}-{chunk_end})...",
            }
            joined = "\n\n".join([f"[CHUNK {chunk_start + j}]\n{c}" for j, c in enumerate(batch)])
            prompt = (
                "You are summarizing a batch of study-note excerpts.\n"
                "For each chunk, return 3-7 bullets with key concepts, definitions, and critical details.\n"
                "Include equations/numbers/dates if they exist.\n"
                "Do not invent missing information.\n\n"
                f"EXCERPTS:\n{joined}"
            )
            batch_summaries.append(self._generate_with_retry(prompt, temperature=0.2))
            chunk_start = chunk_end + 1
            if sleep_seconds > 0 and i < total_batches:
                time.sleep(sleep_seconds)

        yield {"type": "status", "message": "Batch summaries done. Streaming final Markdown summary..."}
        final_prompt = self._build_final_markdown_prompt(batch_summaries)
        for text in self._generate_stream(final_prompt, temperature=0.2):
            yield {"type": "token", "text": text}
        yield {"type": "done"}

    def _build_single_pass_markdown_prompt(self, chunks: list[str]) -> str:
        joined = "\n\n".join([f"[CHUNK {i + 1}]\n{c}" for i, c in enumerate(chunks)])
        return (
            "You are a careful study-note summarization assistant.\n"
            "Write a concise final summary in English using clean Markdown.\n\n"
            "Output format (Markdown):\n"
            "# One-Sentence Overview\n"
            "A single sentence.\n\n"
            "## Key Takeaways\n"
            "- 6-12 bullets\n\n"
            "## Important Details\n"
            "- numbers/dates/definitions/formulas if present\n\n"
            "## Risks or Limitations\n"
            "- only if mentioned\n\n"
            "## 3 Quick Review Questions\n"
            "1. ...\n2. ...\n3. ...\n\n"
            f"{MARKDOWN_RULES}"
            f"EXCERPTS:\n{joined}"
        )

    def _build_final_markdown_prompt(self, batch_summaries: list[str]) -> str:
        combined = "\n\n".join(batch_summaries)
        return (
            "You will receive batch summaries generated from one study note.\n"
            "Write a final student-friendly summary in English using clean Markdown.\n\n"
            "Output format (Markdown):\n"
            "# One-Sentence Overview\n"
            "A single sentence.\n\n"
            "## Key Takeaways\n"
            "- 6-12 bullets\n\n"
            "## Topic Flow\n"
            "1. ... in order\n\n"
            "## Important Details\n"
            "- numbers/dates/requirements/caveats\n\n"
            "## 3 Quick Review Questions\n"
            "1. ...\n2. ...\n3. ...\n\n"
            f"{MARKDOWN_RULES}"
            f"BATCH SUMMARIES:\n{combined}"
        )

    def _generate_stream(self, prompt: str, temperature: float = 0.2):
        if self.generation_provider == "together":
            yield from self._generate_stream_together(prompt, temperature=temperature)
            return

        stream = self._get_gemini_client().models.generate_content_stream(
            model=self._resolved_generation_model(),
            contents=prompt,
            config=types.GenerateContentConfig(temperature=temperature),
        )
        for chunk in stream:
            text = getattr(chunk, "text", None)
            if text:
                yield text

    @staticmethod
    def _clean_markdown_text(text: str) -> str:
        out = (text or "").replace("\r\n", "\n")
        out = out.replace("**", "")
        lines = out.split("\n")

        heading_map = {
            "one-sentence overview": "# One-Sentence Overview",
            "key takeaways": "## Key Takeaways",
            "topic flow": "## Topic Flow",
            "important details": "## Important Details",
            "risks or limitations": "## Risks or Limitations",
            "3 quick review questions": "## 3 Quick Review Questions",
        }

        cleaned_lines: list[str] = []
        for line in lines:
            stripped = line.strip()
            key = stripped.lower().rstrip(":")
            if key in heading_map:
                cleaned_lines.append(heading_map[key])
            else:
                cleaned_lines.append(line)

        non_empty_idx = [i for i, ln in enumerate(cleaned_lines) if ln.strip()]
        if len(non_empty_idx) >= 2:
            first_i, second_i = non_empty_idx[0], non_empty_idx[1]
            a = cleaned_lines[first_i].lstrip("#").strip().lower().rstrip(":")
            b = cleaned_lines[second_i].lstrip("#").strip().lower().rstrip(":")
            if a == b:
                cleaned_lines[second_i] = ""

        cleaned = "\n".join(cleaned_lines).replace("\n\n\n", "\n\n").strip()
        first_non_empty = ""
        for ln in cleaned.split("\n"):
            if ln.strip():
                first_non_empty = ln.strip().lower().rstrip(":")
                break
        if not cleaned.startswith("# ") and first_non_empty != "one-sentence overview":
            cleaned = "# One-Sentence Overview\n" + cleaned
        return cleaned

    def _generate_with_retry(
        self,
        prompt: str,
        temperature: float = 0.2,
        max_attempts: int = 8,
        base_sleep: float = 1.0,
        max_sleep: float = 20.0,
    ) -> str:
        last_error: Optional[Exception] = None
        for attempt in range(1, max_attempts + 1):
            try:
                if self.generation_provider == "together":
                    text = self._generate_with_together(prompt, temperature=temperature).strip()
                else:
                    response = self._get_gemini_client().models.generate_content(
                        model=self._resolved_generation_model(),
                        contents=prompt,
                        config=types.GenerateContentConfig(temperature=temperature),
                    )
                    text = (response.text or "").strip()
                if text:
                    return text
                last_error = RuntimeError("Empty response text.")
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                if not self._is_transient_error(exc):
                    raise

            sleep_sec = min(max_sleep, base_sleep * (2 ** (attempt - 1)))
            sleep_sec *= 0.7 + random.random() * 0.6
            time.sleep(sleep_sec)

        raise RuntimeError(f"Generation failed after retries. Last error: {last_error}")

    def _resolved_generation_model(self) -> str:
        if self.generation_provider == "together":
            return self.generation_model or settings.TOGETHER_MODEL
        return self.generation_model or settings.GEMINI_MODEL or GEN_MODEL

    def current_generation_model(self) -> str:
        return self._resolved_generation_model()

    def _generate_with_together(self, prompt: str, temperature: float = 0.2) -> str:
        if not settings.TOGETHER_API_KEY:
            raise ValueError("Missing TOGETHER_API_KEY in environment.")
        url = settings.TOGETHER_BASE_URL.rstrip("/") + "/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.TOGETHER_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._resolved_generation_model(),
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=180)
        if resp.status_code >= 400:
            raise RuntimeError(
                f"Together generation failed with status {resp.status_code}: {resp.text[:500]}"
            )
        data = resp.json()
        choices = data.get("choices") or []
        if not choices:
            raise RuntimeError(f"Together response missing choices: {str(data)[:500]}")
        message = choices[0].get("message", {}) if isinstance(choices[0], dict) else {}
        content = message.get("content", "")
        text = self._together_content_to_text(content)
        if not text:
            # Some providers may place text in delta/content style fields.
            delta = choices[0].get("delta", {}) if isinstance(choices[0], dict) else {}
            text = self._together_content_to_text(delta.get("content", ""))
        return text

    def _generate_stream_together(self, prompt: str, temperature: float = 0.2):
        if not settings.TOGETHER_API_KEY:
            raise ValueError("Missing TOGETHER_API_KEY in environment.")
        url = settings.TOGETHER_BASE_URL.rstrip("/") + "/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.TOGETHER_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._resolved_generation_model(),
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "stream": True,
        }
        with requests.post(url, headers=headers, json=payload, stream=True, timeout=300) as resp:
            if resp.status_code >= 400:
                raise RuntimeError(
                    f"Together stream failed with status {resp.status_code}: {resp.text[:500]}"
                )
            for raw in resp.iter_lines(decode_unicode=True):
                if not raw:
                    continue
                line = raw.strip()
                if not line.startswith("data:"):
                    continue
                data_str = line[5:].strip()
                if not data_str or data_str == "[DONE]":
                    continue
                try:
                    item = json.loads(data_str)
                except json.JSONDecodeError:
                    continue
                choices = item.get("choices") or []
                if not choices:
                    continue
                first = choices[0] if isinstance(choices[0], dict) else {}
                delta = first.get("delta", {}) if isinstance(first, dict) else {}
                text = self._together_content_to_text(delta.get("content", ""))
                if not text:
                    text = self._together_content_to_text(
                        first.get("message", {}).get("content", "")
                    )
                if text:
                    yield text

    @staticmethod
    def _together_content_to_text(content: Any) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict):
                    # Common schema: {"type":"text","text":"..."}
                    text = item.get("text")
                    if isinstance(text, str):
                        parts.append(text)
            return "".join(parts)
        return ""

    @staticmethod
    def _is_transient_error(err: Exception) -> bool:
        msg = str(err).upper()
        transient_keys = [
            "503",
            "UNAVAILABLE",
            "429",
            "RESOURCE_EXHAUSTED",
            "500",
            "INTERNAL",
            "TIMEOUT",
        ]
        return any(k in msg for k in transient_keys)

    @staticmethod
    def _clean_text(text: str) -> str:
        return re.sub(r"\s+", " ", text.replace("\x00", " ")).strip()

    def _extract_lines_from_page(self, page: fitz.Page) -> list[LineInfo]:
        data = page.get_text("dict")
        lines: list[LineInfo] = []

        for block in data.get("blocks", []):
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                spans = line.get("spans", [])
                pieces: list[str] = []
                sizes: list[float] = []
                bold = False
                for span in spans:
                    span_text = span.get("text", "")
                    if span_text:
                        pieces.append(span_text)
                    size = float(span.get("size", 0.0) or 0.0)
                    if size > 0:
                        sizes.append(size)
                    font_name = (span.get("font", "") or "").lower()
                    if "bold" in font_name:
                        bold = True

                text = self._clean_text("".join(pieces))
                if not text:
                    continue

                bbox = tuple(line.get("bbox", (0, 0, 0, 0)))
                font_size = float(np.median(sizes)) if sizes else 0.0
                lines.append(
                    LineInfo(
                        text=text,
                        bbox=(bbox[0], bbox[1], bbox[2], bbox[3]),
                        font_size=font_size,
                        is_bold=bold,
                    )
                )

        lines.sort(key=lambda row: (row.bbox[1], row.bbox[0]))
        return lines

    def _extract_smart_blocks_from_pdf(self, pdf_path: Path) -> list[str]:
        doc = fitz.open(str(pdf_path))
        all_blocks: list[str] = []

        for page in doc:
            lines = self._extract_lines_from_page(page)
            if not lines:
                continue

            groups = self._group_lines_by_vertical_gaps(lines, gap_threshold=10.0)
            for group in groups:
                merged_blocks = self._merge_bullets_within_group(group)
                if merged_blocks:
                    all_blocks.append("\n".join(merged_blocks).strip())

        doc.close()
        return self._merge_title_with_next(all_blocks)

    @staticmethod
    def _group_lines_by_vertical_gaps(
        lines: list[LineInfo], gap_threshold: float
    ) -> list[list[LineInfo]]:
        if not lines:
            return []

        groups: list[list[LineInfo]] = []
        current: list[LineInfo] = [lines[0]]

        for prev_line, next_line in zip(lines, lines[1:]):
            gap = next_line.bbox[1] - prev_line.bbox[3]
            if gap > gap_threshold:
                groups.append(current)
                current = [next_line]
            else:
                current.append(next_line)

        groups.append(current)
        return groups

    @staticmethod
    def _merge_bullets_within_group(group: list[LineInfo]) -> list[str]:
        blocks: list[str] = []
        index = 0

        while index < len(group):
            text = group[index].text
            if BULLET_RE.match(text):
                bullet_lines = [text]
                index += 1
                while index < len(group):
                    nxt = group[index].text
                    if BULLET_RE.match(nxt) or len(nxt) <= 160:
                        bullet_lines.append(nxt)
                        index += 1
                    else:
                        break
                blocks.append("\n".join(bullet_lines))
            else:
                blocks.append(text)
                index += 1

        return blocks

    @staticmethod
    def _merge_title_with_next(chunks: list[str]) -> list[str]:
        merged: list[str] = []
        idx = 0
        while idx < len(chunks):
            current = chunks[idx].strip()
            if idx + 1 < len(chunks):
                nxt = chunks[idx + 1].strip()
                if "\n" not in current and len(current) <= 100 and nxt:
                    merged.append(f"{current}\n\n{nxt}")
                    idx += 2
                    continue
            merged.append(current)
            idx += 1
        return merged

    @staticmethod
    def _paragraph_blocks(text: str) -> list[str]:
        normalized = text.replace("\r\n", "\n")
        blocks = [p.strip() for p in re.split(r"\n\s*\n", normalized) if p.strip()]
        if blocks:
            return blocks
        compact = re.sub(r"\s+", " ", normalized).strip()
        return [compact] if compact else []

    @staticmethod
    def _pack_blocks(blocks: list[str], max_chars: int, overlap: int) -> list[str]:
        packed: list[str] = []
        current = ""

        def flush() -> None:
            nonlocal current
            if current.strip():
                packed.append(current.strip())
            current = ""

        for raw_block in blocks:
            block = raw_block.strip()
            if not block:
                continue

            if len(block) > max_chars:
                flush()
                step = max(1, max_chars - overlap)
                for i in range(0, len(block), step):
                    part = block[i : i + max_chars].strip()
                    if part:
                        packed.append(part)
                continue

            if not current:
                current = block
            elif len(current) + 2 + len(block) <= max_chars:
                current = f"{current}\n\n{block}"
            else:
                flush()
                current = block

        flush()
        return packed

    @staticmethod
    def export_debug_chunks(chunks: list[str], output_path: Path) -> None:
        with output_path.open("w", encoding="utf-8") as fp:
            for i, chunk in enumerate(chunks):
                obj = {"chunk_id": i, "text": chunk}
                fp.write(json.dumps(obj, ensure_ascii=False) + "\n")
