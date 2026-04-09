import { forwardRef, useCallback, useEffect, useImperativeHandle, useState } from 'react';
import { RefreshCw, BookOpen } from 'lucide-react';
import { listNotes, deleteNote, getNoteDetail, renameNote, resummarizeStream } from '../api/studyNotes';
import { consumeSse } from '../utils/sse';
import { loadFromCache, saveToCache, removeFromCache } from '../utils/summaryCache';
import NoteCard from './NoteCard';

const Library = forwardRef(function Library(
  { onStreaming, onStatus, onError, onMeta, onToken, onDone, onShowCachedSummary },
  ref
) {
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [libError, setLibErr] = useState('');

  const refresh = useCallback(async () => {
    setLoading(true);
    setLibErr('');
    try {
      const data = await listNotes();
      setNotes(data);
    } catch (err) {
      setLibErr(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);
  useImperativeHandle(ref, () => ({ refresh }), [refresh]);

  async function handleResumarize(noteId) {
    onError('');
    onStreaming(true);
    onStatus('Loading stored chunks...');
    try {
      const res = await resummarizeStream(noteId);
      let fullSummary = '';
      await consumeSse(res, (evt, payload) => {
        if (evt === 'status') onStatus(payload.message || '');
        if (evt === 'meta') onMeta(payload);
        if (evt === 'token') {
          const part = payload.text || '';
          fullSummary += part;
          onToken(part);
        }
        if (evt === 'done') {
          if (fullSummary) saveToCache(noteId, fullSummary);
          onStatus('Done');
          onDone();
        }
        if (evt === 'error') throw new Error(payload.detail || 'Stream error.');
      });
    } catch (err) {
      onError(err.message || String(err));
    } finally {
      onStreaming(false);
    }
  }

  async function handleOpenSummary(note) {
    const cached = loadFromCache(note.note_id);
    if (cached) {
      onShowCachedSummary?.(note.note_id, cached, {
        note_id: note.note_id,
        filename: note.filename,
        chunks: note.chunk_count,
        source: 'cache',
      });
      return;
    }

    onError('');
    onStreaming(true);
    onStatus('Loading saved summary...');
    try {
      const detail = await getNoteDetail(note.note_id);
      const saved = (detail?.summary_markdown || '').trim();
      if (!saved) {
        throw new Error('No saved summary found for this note yet.');
      }
      saveToCache(note.note_id, saved);
      onShowCachedSummary?.(note.note_id, saved, {
        note_id: note.note_id,
        filename: detail.filename || note.filename,
        chunks: detail.chunk_count || note.chunk_count,
        source: 'stored_summary',
      });
    } catch (err) {
      onError(err.message || String(err));
    } finally {
      onStreaming(false);
    }
  }

  async function handleDelete(note) {
    if (!window.confirm('Delete this note? Pinecone vectors and the local file will be removed.')) return;
    try {
      await deleteNote(note.note_id);
      removeFromCache(note.note_id);
      await refresh();
    } catch (err) {
      onError(err.message);
    }
  }

  async function handleRename(note) {
    const current = note?.filename || '';
    const next = window.prompt('Rename note filename:', current);
    if (next == null) return;
    const trimmed = next.trim();
    if (!trimmed) {
      onError('Filename cannot be empty.');
      return;
    }
    try {
      await renameNote(note.note_id, trimmed);
      await refresh();
    } catch (err) {
      onError(err.message || String(err));
    }
  }

  return (
    <aside
      className="flex flex-col h-full border-l bg-surface"
      style={{ borderColor: 'var(--border)' }}
    >
      <div
        className="flex items-center justify-between px-4 py-3.5 border-b flex-shrink-0"
        style={{ borderColor: 'var(--border)', background: '#f8f5ff' }}
      >
        <div className="flex items-center gap-2">
          <BookOpen size={14} style={{ color: '#c0392b' }} />
          <span className="font-serif text-[17px] font-semibold text-ink">Library</span>
        </div>
        <button
          onClick={refresh}
          className="w-7 h-7 rounded-lg border flex items-center justify-center text-muted hover:text-ink transition-colors"
          style={{ borderColor: 'var(--border)', background: '#f5f2fc' }}
          title="Refresh"
        >
          <RefreshCw size={12} className={loading ? 'animate-spin' : ''} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-2.5 flex flex-col gap-2">
        {loading && (
          <div className="text-center py-10 text-[13px] text-muted">
            <div className="text-2xl mb-2 opacity-40">...</div>
            Loading...
          </div>
        )}

        {libError && !loading && (
          <div className="text-center py-10 text-[13px]" style={{ color: '#c0392b' }}>
            {libError}
          </div>
        )}

        {!loading && !libError && notes.length === 0 && (
          <div className="text-center py-10 text-[13px] text-muted leading-relaxed px-4">
            <div className="text-3xl mb-3 opacity-30">[]</div>
            No notes yet.
            <br />
            Upload a document to begin.
          </div>
        )}

        {!loading &&
          notes.map((note, i) => (
            <NoteCard
              key={note.note_id}
              note={note}
              index={i}
              isCached={!!loadFromCache(note.note_id)}
              onResumarize={() => handleResumarize(note.note_id)}
              onOpenSummary={() => handleOpenSummary(note)}
              onRename={() => handleRename(note)}
              onView={() => window.__viewNote?.(note.note_id)}
              onDelete={() => handleDelete(note)}
            />
          ))}
      </div>
    </aside>
  );
});

export default Library;
