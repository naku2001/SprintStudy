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
      style={{ background: 'rgba(45,27,105,0.4)', backdropFilter: 'blur(4px)' }}
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div
        className="flex flex-col rounded-2xl border bg-surface w-[660px] max-w-full max-h-[82vh] animate-modal-in"
        style={{ borderColor: 'var(--border)', boxShadow: '0 20px 60px rgba(45,27,105,0.15), 0 8px 24px rgba(45,27,105,0.1)' }}
      >
        {/* Header */}
        <div
          className="flex items-center justify-between px-6 py-4 border-b flex-shrink-0"
          style={{ borderColor: 'var(--border)', background: '#f8f5ff', borderRadius: '16px 16px 0 0' }}
        >
          <div className="flex items-center gap-3">
            <div className="w-1 h-5 rounded-full" style={{ background: '#c0392b' }} />
            <span className="font-serif text-[18px] font-semibold text-ink truncate max-w-[80%]">
              {loading ? 'Loading…' : (detail?.filename || noteId)}
            </span>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-lg border flex items-center justify-center text-muted hover:text-ink transition-colors flex-shrink-0"
            style={{ borderColor: 'var(--border)', background: '#f5f2fc' }}
          >
            <X size={14} />
          </button>
        </div>

        {/* Body */}
        <div className="overflow-y-auto p-5 flex flex-col gap-2.5 flex-1">
          {loading && (
            <p className="text-[13px] text-muted py-6 text-center">Fetching chunks…</p>
          )}
          {error && (
            <p className="text-[13px] py-6 text-center" style={{ color: '#c0392b' }}>{error}</p>
          )}
          {!loading && !error && (detail?.chunks || []).map((chunk) => (
            <div
              key={chunk.record_id}
              className="rounded-xl border p-4"
              style={{ borderColor: 'var(--border)', background: '#f8f5ff' }}
            >
              <div className="flex gap-4 font-mono text-[11px] font-medium mb-2.5" style={{ color: '#c0392b' }}>
                <span>chunk {chunk.chunk_index}</span>
                <span>{chunk.embedding_dim}d</span>
              </div>
              <p className="text-[13px] text-muted leading-relaxed line-clamp-4">
                {chunk.chunk_text || '—'}
              </p>
              <p className="font-mono text-[10px] mt-2.5" style={{ color: '#c4b9e8' }}>
                [{(chunk.embedding_preview || []).map((v) => v.toFixed(5)).join(', ')} …]
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
