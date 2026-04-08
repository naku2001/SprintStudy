import { FileText } from 'lucide-react';

function ActionBtn({ children, variant = 'default', onClick }) {
  const base = 'flex-1 text-center text-[11.5px] font-medium py-1.5 rounded-lg border transition-all duration-150 cursor-pointer';
  const styles = {
    default: 'text-muted border-white/7 hover:text-ink hover:border-white/14',
    teal:    'text-muted border-white/7 hover:text-accent hover:border-accent/35 hover:bg-accent/10',
    danger:  'text-muted border-white/7 hover:text-danger hover:border-danger/30 hover:bg-danger/6',
  };
  return (
    <button
      type="button"
      className={`${base} ${styles[variant]}`}
      style={{ background: 'transparent' }}
      onClick={onClick}
    >
      {children}
    </button>
  );
}

export default function NoteCard({ note, index, onView, onResumarize, onDelete }) {
  const date = note.created_at
    ? new Date(note.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
    : null;

  return (
    <div
      className="rounded-xl border p-3.5 transition-all duration-200 hover:-translate-x-0.5 hover:border-accent/30 animate-card-in"
      style={{
        borderColor: 'var(--border)',
        background: '#1a1e2a',
        animationDelay: `${index * 40}ms`,
      }}
    >
      {/* Name */}
      <div className="flex items-start gap-2 mb-2">
        <FileText size={13} className="text-muted flex-shrink-0 mt-0.5" />
        <span className="text-[13.5px] font-medium text-ink truncate leading-tight">
          {note.filename || 'unknown'}
        </span>
      </div>

      {/* Chips */}
      <div className="flex flex-wrap gap-1.5 mb-3">
        <span className="font-mono text-[10.5px] text-muted px-2 py-0.5 rounded-full border"
              style={{ borderColor: 'var(--border)', background: '#13161f' }}>
          {note.chunk_count} chunk{note.chunk_count !== 1 ? 's' : ''}
        </span>
        {date && (
          <span className="font-mono text-[10.5px] text-muted px-2 py-0.5 rounded-full border"
                style={{ borderColor: 'var(--border)', background: '#13161f' }}>
            {date}
          </span>
        )}
        {note.local_file_exists && (
          <span className="font-mono text-[10.5px] text-accent px-2 py-0.5 rounded-full border border-accent/18"
                style={{ background: 'var(--accent-dim)' }}>
            local
          </span>
        )}
      </div>

      {/* Actions */}
      <div className="flex gap-1.5">
        <ActionBtn variant="teal"    onClick={onResumarize}>Re-summarize</ActionBtn>
        <ActionBtn variant="default" onClick={onView}>View</ActionBtn>
        <ActionBtn variant="danger"  onClick={onDelete}>Delete</ActionBtn>
      </div>
    </div>
  );
}
