import { useRef, useState } from 'react';
import { UploadCloud, FileText } from 'lucide-react';
import { summarizeStream } from '../api/studyNotes';
import { consumeSse } from '../utils/sse';

export default function UploadZone({ onStreaming, onStatus, onError, onMeta, onToken, onDone }) {
  const inputRef             = useRef(null);
  const [file, setFile]      = useState(null);
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
      <p className="text-[11px] font-bold uppercase tracking-widest text-muted mb-3">
        New Document
      </p>

      {/* Drop zone */}
      <div
        className="relative rounded-2xl border-2 border-dashed p-10 text-center transition-all duration-200 overflow-hidden group"
        style={{
          borderColor: dragOver ? '#c0392b' : '#d6d0ca',
          background: dragOver ? 'rgba(192,57,43,0.03)' : '#ffffff',
        }}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          const f = e.dataTransfer.files?.[0];
          if (f) pickFile(f);
        }}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.txt"
          className="hidden"
          onChange={(e) => pickFile(e.target.files?.[0])}
        />

        {/* Icon ring */}
        <div
          className="w-14 h-14 rounded-2xl mx-auto mb-5 flex items-center justify-center transition-transform duration-300 group-hover:-translate-y-1"
          style={{ background: 'rgba(192,57,43,0.08)', border: '1.5px solid rgba(192,57,43,0.2)' }}
        >
          <UploadCloud size={24} style={{ color: '#c0392b' }} />
        </div>

        <h2 className="font-serif text-[22px] font-semibold text-ink mb-2">
          Drop your document here
        </h2>
        <p className="text-[13.5px] text-muted mb-7 leading-relaxed">
          Accepts{' '}
          <code className="font-mono text-[12.5px] px-1.5 py-0.5 rounded bg-surface2 text-ink">.pdf</code>
          {' '}and{' '}
          <code className="font-mono text-[12.5px] px-1.5 py-0.5 rounded bg-surface2 text-ink">.txt</code>
          {' '}— chunks, embeds &amp; summarizes with Gemini
        </p>

        {/* Chosen file badge */}
        {file && (
          <div
            className="inline-flex items-center gap-2 rounded-full border px-4 py-1.5 text-[13px] font-medium text-ink mb-6"
            style={{ borderColor: 'var(--border)', background: '#f7f5f2' }}
          >
            <FileText size={13} style={{ color: '#c0392b' }} />
            {file.name}
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center justify-center gap-3">
          <button
            type="button"
            onClick={() => inputRef.current?.click()}
            className="rounded-xl border px-5 py-2.5 text-[13.5px] font-medium text-muted hover:text-ink hover:border-border transition-all"
            style={{ borderColor: 'var(--border)', background: '#f7f5f2' }}
          >
            Browse files
          </button>
          <button
            type="button"
            onClick={handleSubmit}
            className="inline-flex items-center gap-2 rounded-xl px-6 py-2.5 text-[14px] font-semibold text-white transition-all duration-150 hover:-translate-y-px active:translate-y-0"
            style={{
              background: '#c0392b',
              boxShadow: '0 1px 3px rgba(192,57,43,0.3), 0 4px 14px rgba(192,57,43,0.2)',
            }}
            onMouseEnter={e => e.currentTarget.style.boxShadow = '0 2px 6px rgba(192,57,43,0.35), 0 6px 20px rgba(192,57,43,0.25)'}
            onMouseLeave={e => e.currentTarget.style.boxShadow = '0 1px 3px rgba(192,57,43,0.3), 0 4px 14px rgba(192,57,43,0.2)'}
          >
            <UploadCloud size={15} />
            Summarize
          </button>
        </div>
      </div>
    </div>
  );
}
