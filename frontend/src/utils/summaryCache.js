const KEY = (noteId) => `njere_summary_${noteId}`;

export function saveToCache(noteId, summary) {
  if (!noteId || !summary) return;
  try {
    localStorage.setItem(KEY(noteId), summary);
  } catch {}
}

export function loadFromCache(noteId) {
  if (!noteId) return null;
  try {
    return localStorage.getItem(KEY(noteId)) || null;
  } catch {
    return null;
  }
}

export function removeFromCache(noteId) {
  if (!noteId) return;
  try {
    localStorage.removeItem(KEY(noteId));
  } catch {}
}
