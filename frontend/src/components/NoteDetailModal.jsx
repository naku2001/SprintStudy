import { useEffect, useState } from 'react';
import { X } from 'lucide-react';
import { getNoteDetail } from '../api/studyNotes';

export default function NoteDetailModal({ noteId, onClose }) {
  const [detail, setDetail]   = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState('');

  useEffect(() => {
    if (!noteId) return;
    setLoading(true);
    setError('');
    getNoteDetail(noteId)
      .then(setDetail)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [noteId]);

  if (!noteId) return null;

  return (
    <div
      className="fixed inset-0 z-[200] flex items-center justify-center p-5"
      style={{ background: 'rgba(0,0,0,0.72)', backdropFilter: 'blur(5px)' }}
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div
        className="flex flex-col rounded-2xl border w-[660px] max-w-full max-h-[82vh] animate-modal-in"
        style={{ borderColor: 'var(--border)', background: '#13161f' }}
      >
        {/* Header */}
        <div
          className="flex items-center justify-between px-6 py-4 border-b flex-shrink-0"
          style={{ borderColor: 'var(--border)' }}
        >
          <span className="font-serif text-[19px] font-normal text-ink truncate max-w-[85%]">
            {loading ? 'Loading…' : (detail?.filename || noteId)}
          </span>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-lg border flex items-center justify-center text-muted hover:text-accent hover:border-accent/35 transition-colors flex-shrink-0"
            style={{ borderColor: 'var(--border)', background: '#1a1e2a' }}
          >
            <X size={15} />
          </button>
        </div>

        {/* Body */}
        <div className="overflow-y-auto p-5 flex flex-col gap-2 flex-1">
          {loading && (
            <p className="text-[13px] text-muted py-4">Fetching chunks…</p>
          )}
          {error && (
            <p className="text-[13px] text-danger py-4">{error}</p>
          )}
          {!loading && !error && (detail?.chunks || []).map((chunk) => (
            <div
              key={chunk.record_id}
              className="rounded-xl border p-4"
              style={{ borderColor: 'var(--border)', background: '#1a1e2a' }}
            >
              <div className="flex gap-4 font-mono text-[11px] text-accent mb-2.5">
                <span>chunk {chunk.chunk_index}</span>
                <span>{chunk.embedding_dim}d embedding</span>
              </div>
              <p
                className="text-[13px] text-muted leading-relaxed line-clamp-4"
              >
                {chunk.chunk_text || '—'}
              </p>
              <p className="font-mono text-[10.5px] text-muted/60 mt-2">
                [{(chunk.embedding_preview || []).map((v) => v.toFixed(5)).join(', ')} …]
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
