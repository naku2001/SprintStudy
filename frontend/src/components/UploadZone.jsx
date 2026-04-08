import { useRef, useState } from 'react';
import { UploadCloud } from 'lucide-react';
import { summarizeStream } from '../api/studyNotes';
import { consumeSse } from '../utils/sse';

export default function UploadZone({ onStreaming, onStatus, onError, onMeta, onToken, onDone }) {
  const inputRef   = useRef(null);
  const [file, setFile]       = useState(null);
  const [dragOver, setDragOver] = useState(false);

  function pickFile(f) {
    if (!f) return;
    setFile(f);
  }

  async function handleSubmit(e) {
    e.stopPropagation();
    if (!file) { onError('Please select a .pdf or .txt file first.'); return; }

    onError('');
    onStreaming(true);
    onStatus('Uploading…');

    try {
      const res = await summarizeStream(file);
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

  return (
    <div>
      <p className="text-[11px] font-semibold uppercase tracking-widest text-muted mb-3">
        New Document
      </p>

      <div
        className={[
          'relative rounded-2xl border-2 border-dashed p-12 text-center transition-all duration-200 overflow-hidden group',
          dragOver
            ? 'border-accent/50 bg-surface'
            : 'bg-surface',
        ].join(' ')}
        style={{ borderColor: dragOver ? 'rgba(0,212,170,0.4)' : 'rgba(255,255,255,0.09)' }}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          const f = e.dataTransfer.files?.[0];
          if (f) pickFile(f);
        }}
      >
        {/* Radial glow on hover */}
        <div
          className="pointer-events-none absolute inset-0 transition-opacity duration-300"
          style={{
            background: 'radial-gradient(ellipse at 50% 0%, rgba(0,212,170,0.07) 0%, transparent 70%)',
            opacity: dragOver ? 1 : 0,
          }}
        />

        {/* Hidden file input */}
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.txt"
          className="hidden"
          onChange={(e) => pickFile(e.target.files?.[0])}
        />

        {/* Icon */}
        <div
          className="w-14 h-14 rounded-full border mx-auto mb-5 flex items-center justify-center transition-transform duration-300 group-hover:-translate-y-1"
          style={{ borderColor: 'var(--border)', background: '#1a1e2a' }}
        >
          <UploadCloud size={24} className="text-muted" />
        </div>

        <h2 className="font-serif text-2xl text-ink mb-2">Drop your document here</h2>
        <p className="text-[13.5px] text-muted mb-7">
          Accepts <span className="font-mono text-accent/80">.pdf</span> and{' '}
          <span className="font-mono text-accent/80">.txt</span> · chunks, embeds &amp; summarizes with Gemini
        </p>

        {/* Chosen file badge */}
        {file && (
          <div
            className="inline-flex items-center gap-2 rounded-full border px-4 py-1.5 text-[13px] text-ink mb-6"
            style={{ borderColor: 'var(--border)', background: '#1a1e2a' }}
          >
            <span className="text-accent">📎</span>
            {file.name}
          </div>
        )}

        {/* Buttons row */}
        <div className="flex items-center justify-center gap-3">
          <button
            type="button"
            onClick={() => inputRef.current?.click()}
            className="rounded-xl border px-5 py-2.5 text-[13.5px] font-medium text-muted transition-colors hover:text-ink"
            style={{ borderColor: 'var(--border)', background: '#1a1e2a' }}
          >
            Browse files
          </button>
          <button
            type="button"
            onClick={handleSubmit}
            className="inline-flex items-center gap-2 rounded-xl px-6 py-2.5 text-[14px] font-semibold text-bg bg-accent transition-all hover:-translate-y-0.5 hover:shadow-[0_8px_28px_rgba(0,212,170,0.28)]"
          >
            <UploadCloud size={15} />
            Summarize
          </button>
        </div>
      </div>
    </div>
  );
}
