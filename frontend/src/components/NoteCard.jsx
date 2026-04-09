import { FileText } from 'lucide-react';

function ActionBtn({ children, variant = 'default', onClick }) {
  const styles = {
    default: { color: '#9587c8', background: '#f5f2fc', border: '1px solid #e2daf5' },
    red: { color: '#c0392b', background: 'rgba(192,57,43,0.06)', border: '1px solid rgba(192,57,43,0.2)' },
    danger: { color: '#9587c8', background: '#f5f2fc', border: '1px solid #e2daf5' },
  };
  return (
    <button
      type="button"
      className="flex-1 text-center text-[11.5px] font-medium py-1.5 rounded-lg transition-all duration-150 hover:opacity-75 active:scale-95"
      style={styles[variant]}
      onClick={onClick}
    >
      {children}
    </button>
  );
}

export default function NoteCard({
  note,
  index,
  isCached,
  onView,
  onResumarize,
  onOpenSummary,
  onRename,
  onDelete,
}) {
  const date = note.created_at
    ? new Date(note.created_at).toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      })
    : null;

  return (
    <div
      className="rounded-xl border bg-surface p-3.5 transition-all duration-200 hover:shadow-card-hover hover:-translate-x-px animate-card-in"
      style={{ borderColor: 'var(--border)', animationDelay: `${index * 35}ms` }}
    >
      <div className="flex items-start gap-2 mb-2.5">
        <FileText size={12} className="flex-shrink-0 mt-0.5" style={{ color: '#c0392b' }} />
        <span className="text-[13px] font-semibold text-ink truncate leading-tight">
          {note.filename || 'unknown'}
        </span>
      </div>

      <div className="flex flex-wrap gap-1.5 mb-3">
        <Chip>{note.chunk_count} chunk{note.chunk_count !== 1 ? 's' : ''}</Chip>
        {date && <Chip>{date}</Chip>}
        {note.local_file_exists && <Chip hi>local</Chip>}
        {isCached && <Chip hi>summary saved</Chip>}
      </div>

      <div className="grid grid-cols-2 gap-1.5">
        <ActionBtn variant="red" onClick={onResumarize}>Re-summarize</ActionBtn>
        <ActionBtn variant="default" onClick={onOpenSummary}>Open Summary</ActionBtn>
        <ActionBtn variant="default" onClick={onRename}>Rename</ActionBtn>
        <ActionBtn variant="default" onClick={onView}>View Chunks</ActionBtn>
        <ActionBtn variant="danger" onClick={onDelete}>Delete</ActionBtn>
      </div>
    </div>
  );
}

function Chip({ children, hi }) {
  return (
    <span
      className="font-mono text-[10.5px] font-medium px-2 py-0.5 rounded-md border"
      style={
        hi
          ? { color: '#c0392b', borderColor: 'rgba(192,57,43,0.2)', background: 'rgba(192,57,43,0.06)' }
          : { color: '#9587c8', borderColor: '#e2daf5', background: '#f5f2fc' }
      }
    >
      {children}
    </span>
  );
}
