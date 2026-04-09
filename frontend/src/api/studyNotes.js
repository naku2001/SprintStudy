const BASE = '/api/study-notes';

/**
 * Safely parse JSON from a Response.
 * Returns {} if the body is empty or not valid JSON instead of throwing.
 */
async function safeJson(res) {
  const text = await res.text();
  if (!text.trim()) return {};
  try { return JSON.parse(text); } catch { return {}; }
}

/** List all stored notes. Returns { notes: [...] } */
export async function listNotes() {
  const res = await fetch(BASE);
  const data = await safeJson(res);
  if (!res.ok) throw new Error(data.detail || `Server error ${res.status}.`);
  return data.notes || [];
}

/** Get detail for a single note (chunks + embedding previews). */
export async function getNoteDetail(noteId) {
  const res = await fetch(`${BASE}/${encodeURIComponent(noteId)}`);
  const data = await safeJson(res);
  if (!res.ok) throw new Error(data.detail || `Server error ${res.status}.`);
  return data;
}

/** Delete a note (Pinecone + local file). */
export async function deleteNote(noteId) {
  const res = await fetch(`${BASE}/${encodeURIComponent(noteId)}`, { method: 'DELETE' });
  const data = await safeJson(res);
  if (!res.ok) throw new Error(data.detail || `Server error ${res.status}.`);
  return data;
}

/** Rename a note display filename stored in Pinecone metadata. */
export async function renameNote(noteId, filename) {
  const res = await fetch(`${BASE}/${encodeURIComponent(noteId)}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ filename }),
  });
  const data = await safeJson(res);
  if (!res.ok) throw new Error(data.detail || `Server error ${res.status}.`);
  return data;
}

/**
 * Upload a file and stream the summarization.
 * Returns a raw Response for SSE consumption.
 */
export async function summarizeStream(file, options = {}) {
  const fd = new FormData();
  fd.append('file', file);
  if (options.embeddingProvider) fd.append('embedding_provider', options.embeddingProvider);
  if (options.embeddingModel) fd.append('embedding_model', options.embeddingModel);
  if (options.generationProvider) fd.append('generation_provider', options.generationProvider);
  if (options.generationModel) fd.append('generation_model', options.generationModel);
  const res = await fetch(`${BASE}/summarize-stream`, { method: 'POST', body: fd });
  if (!res.ok) {
    const data = await safeJson(res);
    throw new Error(data.detail || `Server error ${res.status}.`);
  }
  return res;
}

/**
 * Re-summarize a stored note from Pinecone chunks.
 * Returns a raw Response for SSE consumption.
 */
export async function resummarizeStream(noteId) {
  const res = await fetch(`${BASE}/${encodeURIComponent(noteId)}/resummarize-stream`, {
    method: 'POST',
  });
  if (!res.ok) {
    const data = await safeJson(res);
    throw new Error(data.detail || `Server error ${res.status}.`);
  }
  return res;
}
