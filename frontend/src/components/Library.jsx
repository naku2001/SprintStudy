import { forwardRef, useCallback, useEffect, useImperativeHandle, useState } from 'react';
import { RefreshCw } from 'lucide-react';
import { listNotes, deleteNote, resummarizeStream } from '../api/studyNotes';
import { consumeSse } from '../utils/sse';
import NoteCard from './NoteCard';

const Library = forwardRef(function Library({ onStreaming, onStatus, onError, onMeta, onToken, onDone }, ref) {
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

  // Expose refresh() to parent via ref
  useImperativeHandle(ref, () => ({ refresh }), [refresh]);

  async function handleResumarize(noteId) {
    onError('');
    onStreaming(true);
    onStatus('Loading stored chunks…');

    try {
      const res = await resummarizeStream(noteId);
      await consumeSse(res, (evt, payload) => {
        if (evt === 'status') onStatus(payload.message || '');
        if (evt === 'meta')   onMeta(payload);
        if (evt === 'token')  onToken(payload.text || '');
        if (evt === 'done')   { onStatus('Done'); onDone(); }
        if (evt === 'error')  throw new Error(payload.detail || 'Stream error.');
      });
    } catch (err) {
      onError(err.message || String(err));
    } finally {
      onStreaming(false);
    }
  }

  async function handleDelete(noteId) {
    if (!window.confirm('Delete this note? Pinecone vectors and the local file will be removed.')) return;
    try {
      await deleteNote(noteId);
      await refresh();
    } catch (err) {
      onError(err.message);
    }
  }

  return (
    <aside
      className="flex flex-col border-l overflow-hidden"
      style={{ borderColor: 'var(--border)', background: '#13161f' }}
    >
      {/* Header */}
      <div
        className="flex items-center justify-between px-4 py-4 border-b flex-shrink-0"
        style={{ borderColor: 'var(--border)' }}
      >
        <span className="font-serif text-[18px] font-normal text-ink">Library</span>
        <button
          onClick={refresh}
          className="w-8 h-8 rounded-lg border flex items-center justify-center text-muted hover:text-accent hover:border-accent/35 transition-colors"
          style={{ borderColor: 'var(--border)', background: '#1a1e2a' }}
          title="Refresh library"
        >
          <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
        </button>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto p-2.5 flex flex-col gap-2">
        {loading && (
          <div className="text-center py-12 text-[13px] text-muted">
            <span className="block text-2xl mb-2.5 opacity-40">⏳</span>
            Loading…
          </div>
        )}

        {libError && !loading && (
          <div className="text-center py-12 text-[13px] text-danger">
            {libError}
          </div>
        )}

        {!loading && !libError && notes.length === 0 && (
          <div className="text-center py-12 text-[13px] text-muted leading-relaxed">
            <span className="block text-3xl mb-3 opacity-40">📚</span>
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
            onResumarize={() => handleResumarize(note.note_id)}
            onView={() => window.__viewNote?.(note.note_id)}
            onDelete={() => handleDelete(note.note_id)}
          />
        ))}
      </div>
    </aside>
  );
});

export default Library;
