import { forwardRef, useCallback, useEffect, useImperativeHandle, useState } from 'react';
import { RefreshCw, BookOpen } from 'lucide-react';
import { listNotes, deleteNote, resummarizeStream } from '../api/studyNotes';
import { consumeSse } from '../utils/sse';
import { loadFromCache, saveToCache, removeFromCache } from '../utils/summaryCache';
import NoteCard from './NoteCard';

const Library = forwardRef(function Library(
  { onStreaming, onStatus, onError, onMeta, onToken, onDone, onShowCachedSummary },
  ref
) {
  const [notes, setNotes]     = useState([]);
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

  useEffect(() => { refresh(); }, [refresh]);
  useImperativeHandle(ref, () => ({ refresh }), [refresh]);

  async function handleViewSummary(note) {
    // Check localStorage first — show instantly if cached
    const cached = loadFromCache(note.note_id);
    if (cached) {
      onShowCachedSummary(note.note_id, cached, {
        note_id: note.note_id,
        filename: note.filename,
        source: 'cache',
      });
      return;
    }

    // No cache yet — generate it and cache the result
    onError('');
    onStreaming(true);
    onStatus('Generating summary…');
    try {
      const res = await resummarizeStream(note.note_id);
      let fullSummary = '';
      await consumeSse(res, (evt, payload) => {
        if (evt === 'status') onStatus(payload.message || '');
        if (evt === 'meta')   onMeta({ ...payload, filename: note.filename });
        if (evt === 'token') {
          fullSummary += payload.text || '';
          onToken(payload.text || '');
        }
        if (evt === 'done') {
          // Cache the generated summary for next time
          if (fullSummary) saveToCache(note.note_id, fullSummary);
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

  async function handleDelete(note) {
    if (!window.confirm('Delete this note? Pinecone vectors and the local file will be removed.')) return;
    try {
      await deleteNote(note.note_id);
      removeFromCache(note.note_id); // clean up cached summary too
      await refresh();
    } catch (err) {
      onError(err.message);
    }
  }

  return (
    <aside
      className="flex flex-col h-full border-l bg-surface"
      style={{ borderColor: 'var(--border)' }}
    >
      {/* Header */}
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

      {/* Note list */}
      <div className="flex-1 overflow-y-auto p-2.5 flex flex-col gap-2">
        {loading && (
          <div className="text-center py-10 text-[13px] text-muted">
            <div className="text-2xl mb-2 opacity-40">⏳</div>
            Loading…
          </div>
        )}

        {libError && !loading && (
          <div className="text-center py-10 text-[13px]" style={{ color: '#c0392b' }}>
            {libError}
          </div>
        )}

        {!loading && !libError && notes.length === 0 && (
          <div className="text-center py-10 text-[13px] text-muted leading-relaxed px-4">
            <div className="text-3xl mb-3 opacity-30">📚</div>
            No notes yet.
            <br />
            Upload a document to begin.
          </div>
        )}

        {!loading && notes.map((note, i) => (
          <NoteCard
            key={note.note_id}
            note={note}
            index={i}
            isCached={!!loadFromCache(note.note_id)}
            onViewSummary={() => handleViewSummary(note)}
            onDelete={() => handleDelete(note)}
          />
        ))}
      </div>
    </aside>
  );
});

export default Library;
