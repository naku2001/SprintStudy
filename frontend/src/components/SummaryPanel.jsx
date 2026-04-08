import { renderMarkdownToHtml } from '../utils/markdown';

function Chip({ children, hi }) {
  return (
    <span
      className="font-mono text-[11px] font-medium px-2.5 py-0.5 rounded-full border"
      style={
        hi
          ? { color: '#c0392b', background: 'rgba(192,57,43,0.07)', borderColor: 'rgba(192,57,43,0.2)' }
          : { color: '#78716c', background: '#f7f5f2', borderColor: 'var(--border)' }
      }
    >
      {children}
    </span>
  );
}

export default function SummaryPanel({ summary, streaming, meta }) {
  if (!summary && !streaming) return null;

  return (
    <div
      className="flex flex-col rounded-2xl border bg-surface overflow-hidden animate-fade-up"
      style={{ borderColor: 'var(--border)', boxShadow: 'var(--shadow-sm)' }}
    >
      {/* Header bar */}
      <div
        className="flex items-center justify-between px-6 py-3 border-b"
        style={{ borderColor: 'var(--border)', background: '#faf8f6' }}
      >
        <div className="flex items-center gap-2">
          <div className="w-[3px] h-4 rounded-full" style={{ background: '#c0392b' }} />
          <span className="text-[11px] font-bold uppercase tracking-widest text-muted">
            Summary
          </span>
        </div>
        <div className="flex gap-2 flex-wrap justify-end">
          {meta?.filename && <Chip>{meta.filename}</Chip>}
          {meta?.chunks   && <Chip hi>{meta.chunks} chunks</Chip>}
          {meta?.source === 'pinecone_stored_chunks' && <Chip hi>re-summarized</Chip>}
        </div>
      </div>

      {/* Content */}
      <div
        className={`px-8 py-7 max-h-[640px] overflow-y-auto summary-md ${streaming ? 'typing-cursor' : ''}`}
        dangerouslySetInnerHTML={{ __html: renderMarkdownToHtml(summary) }}
      />
    </div>
  );
}
