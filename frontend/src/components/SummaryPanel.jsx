import { renderMarkdownToHtml } from '../utils/markdown';

function Chip({ children, hi }) {
  return (
    <span
      className={`font-mono text-[11.5px] px-2.5 py-0.5 rounded-full border ${
        hi
          ? 'text-accent border-accent/20'
          : 'text-muted border-white/5'
      }`}
      style={{ background: hi ? 'var(--accent-dim)' : '#1a1e2a' }}
    >
      {children}
    </span>
  );
}

export default function SummaryPanel({ summary, streaming, meta }) {
  if (!summary && !streaming) return null;

  return (
    <div
      className="flex flex-col rounded-2xl border overflow-hidden animate-fade-up"
      style={{ borderColor: 'var(--border)', background: '#13161f' }}
    >
      {/* Header */}
      <div
        className="flex items-center justify-between px-6 py-3.5 border-b"
        style={{ borderColor: 'var(--border)' }}
      >
        <span className="text-[11px] font-semibold uppercase tracking-widest text-muted">
          Summary
        </span>
        <div className="flex gap-2 flex-wrap justify-end">
          {meta?.filename && <Chip>{meta.filename}</Chip>}
          {meta?.chunks   && <Chip hi>{meta.chunks} chunks</Chip>}
          {meta?.source === 'pinecone_stored_chunks' && <Chip hi>re-summarized</Chip>}
        </div>
      </div>

      {/* Body */}
      <div
        className={`px-9 py-8 max-h-[640px] overflow-y-auto summary-md text-[15px] leading-relaxed ${
          streaming ? 'typing-cursor' : ''
        }`}
        dangerouslySetInnerHTML={{ __html: renderMarkdownToHtml(summary) }}
      />
    </div>
  );
}
