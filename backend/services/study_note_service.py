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
from google import genai
from google.genai import types

from backend.config.settings import settings
from backend.services.pinecone_store import PineconeRecord, PineconeStore

EMBED_MODEL = "models/gemini-embedding-001"
GEN_MODEL = "models/gemini-2.5-flash"

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

    def __init__(self) -> None:
        if not settings.GEMINI_API_KEY:
            raise ValueError("Missing GEMINI_API_KEY in environment.")
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

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

    def extract_chunks(self, file_path: Path, max_chars: int = 2000, overlap: int = 200) -> list[str]:
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

        res = self.client.models.embed_content(
            model=EMBED_MODEL,
            contents=chunks,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_DOCUMENT",
                output_dimensionality=settings.EMBEDDING_DIMENSION,
            ),
        )
        return np.array([e.values for e in res.embeddings], dtype=np.float32)

    def summarize_adaptive(self, chunks: list[str]) -> str:
        chunk_count = len(chunks)
        if chunk_count <= 6:
            return self._clean_markdown_text(self._summarize_once(chunks))

        batch_size = 4 if chunk_count <= 25 else 3
        batch_summaries = self._batch_summarize_chunks(chunks, batch_size=batch_size)
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
        joined = "\n\n".join([f"[CHUNK {i + 1}]\n{c}" for i, c in enumerate(chunks)])
        prompt = (
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
            "Rules:\n"
            "- Do not invent facts.\n"
            "- Stay faithful to the provided note.\n\n"
            "- Use Markdown headings with # and ## exactly as requested.\n"
            "- Do not use bold markers like ** anywhere in output.\n"
            "- Do not add any preface before the first heading.\n\n"
            f"EXCERPTS:\n{joined}"
        )
        return self._generate_with_retry(prompt, temperature=0.2)

    def _batch_summarize_chunks(self, chunks: list[str], batch_size: int) -> list[str]:
        summaries: list[str] = []
        for start in range(0, len(chunks), batch_size):
            batch = chunks[start : start + batch_size]
            joined = "\n\n".join([f"[CHUNK {start + i + 1}]\n{c}" for i, c in enumerate(batch)])
            prompt = (
                "You are summarizing a batch of study-note excerpts.\n"
                "For each chunk, return 3-7 bullets with key concepts, definitions, and critical details.\n"
                "Include equations/numbers/dates if they exist.\n"
                "Do not invent missing information.\n\n"
                f"EXCERPTS:\n{joined}"
            )
            summaries.append(self._generate_with_retry(prompt, temperature=0.2))
            time.sleep(0.4)
        return summaries

    def _summarize_all(self, batch_summaries: list[str]) -> str:
        combined = "\n\n".join(batch_summaries)
        prompt = (
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
            "Rules:\n"
            "- Be faithful to input text only.\n"
            "- Do not hallucinate missing facts.\n\n"
            "- Use Markdown headings with # and ## exactly as requested.\n"
            "- Do not use bold markers like ** anywhere in output.\n"
            "- Do not add any preface before the first heading.\n\n"
            f"BATCH SUMMARIES:\n{combined}"
        )
        return self._generate_with_retry(prompt, temperature=0.2)

    def summarize_adaptive_stream(self, chunks: list[str]):
        chunk_count = len(chunks)
        if chunk_count <= 6:
            yield {"type": "status", "message": "Small note detected. Streaming single-pass summary..."}
            prompt = self._build_single_pass_markdown_prompt(chunks)
            for text in self._generate_stream(prompt, temperature=0.2):
                yield {"type": "token", "text": text}
            yield {"type": "done"}
            return

        batch_size = 4 if chunk_count <= 25 else 3
        yield {
            "type": "status",
            "message": f"Preparing map-reduce summary ({chunk_count} chunks, batch_size={batch_size})...",
        }
        batch_summaries = self._batch_summarize_chunks(chunks, batch_size=batch_size)
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
            "Rules:\n"
            "- Do not invent facts.\n"
            "- Stay faithful to the provided note.\n\n"
            "- Use Markdown headings with # and ## exactly as requested.\n"
            "- Do not use bold markers like ** anywhere in output.\n"
            "- Do not add any preface before the first heading.\n\n"
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
            "Rules:\n"
            "- Be faithful to input text only.\n"
            "- Do not hallucinate missing facts.\n\n"
            "- Use Markdown headings with # and ## exactly as requested.\n"
            "- Do not use bold markers like ** anywhere in output.\n"
            "- Do not add any preface before the first heading.\n\n"
            f"BATCH SUMMARIES:\n{combined}"
        )

    def _generate_stream(self, prompt: str, temperature: float = 0.2):
        stream = self.client.models.generate_content_stream(
            model=settings.GEMINI_MODEL or GEN_MODEL,
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
                response = self.client.models.generate_content(
                    model=settings.GEMINI_MODEL or GEN_MODEL,
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

        raise RuntimeError(f"Gemini generation failed after retries. Last error: {last_error}")

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
