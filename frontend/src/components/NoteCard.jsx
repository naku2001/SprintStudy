import { FileText } from 'lucide-react';

function ActionBtn({ children, variant = 'default', onClick }) {
  const styles = {
    default: {
      color: '#78716c',
      background: '#f7f5f2',
      border: '1px solid var(--border)',
    },
    red: {
      color: '#c0392b',
      background: 'rgba(192,57,43,0.06)',
      border: '1px solid rgba(192,57,43,0.2)',
    },
    danger: {
      color: '#78716c',
      background: '#f7f5f2',
      border: '1px solid var(--border)',
    },
  };

  return (
    <button
      type="button"
      className="flex-1 text-center text-[11.5px] font-medium py-1.5 rounded-lg transition-all duration-150 hover:opacity-80 active:scale-95"
      style={styles[variant]}
      onClick={onClick}
    >
      {children}
    </button>
  );
}

export default function NoteCard({ note, index, onView, onResumarize, onDelete }) {
  const date = note.created_at
    ? new Date(note.created_at).toLocaleDateString(undefined, {
        month: 'short', day: 'numeric', year: 'numeric',
      })
    : null;

  return (
    <div
      className="rounded-xl border bg-surface p-3.5 transition-all duration-200 hover:shadow-card-hover hover:-translate-x-px animate-card-in"
      style={{ borderColor: 'var(--border)', animationDelay: `${index * 35}ms` }}
    >
      {/* Filename */}
      <div className="flex items-start gap-2 mb-2.5">
        <FileText size={12} className="flex-shrink-0 mt-0.5" style={{ color: '#c0392b' }} />
        <span className="text-[13px] font-semibold text-ink truncate leading-tight">
          {note.filename || 'unknown'}
        </span>
      </div>

      {/* Meta chips */}
      <div className="flex flex-wrap gap-1.5 mb-3">
        <span className="font-mono text-[10.5px] text-muted px-2 py-0.5 rounded-md border"
              style={{ borderColor: 'var(--border)', background: '#f7f5f2' }}>
          {note.chunk_count} chunk{note.chunk_count !== 1 ? 's' : ''}
        </span>
        {date && (
          <span className="font-mono text-[10.5px] text-muted px-2 py-0.5 rounded-md border"
                style={{ borderColor: 'var(--border)', background: '#f7f5f2' }}>
            {date}
          </span>
        )}
        {note.local_file_exists && (
          <span className="font-mono text-[10.5px] font-medium px-2 py-0.5 rounded-md border"
                style={{ color: '#c0392b', borderColor: 'rgba(192,57,43,0.2)', background: 'rgba(192,57,43,0.06)' }}>
            local
          </span>
        )}
      </div>

      {/* Actions */}
      <div className="flex gap-1.5">
        <ActionBtn variant="red"     onClick={onResumarize}>Re-summarize</ActionBtn>
        <ActionBtn variant="default" onClick={onView}>View</ActionBtn>
        <ActionBtn variant="danger"  onClick={onDelete}>Delete</ActionBtn>
      </div>
    </div>
  );
}
