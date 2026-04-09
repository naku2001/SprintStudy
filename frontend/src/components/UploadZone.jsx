import { useRef, useState } from 'react';
import { UploadCloud, FileText } from 'lucide-react';
import { listNotes, summarizeStream } from '../api/studyNotes';
import { consumeSse } from '../utils/sse';

export default function UploadZone({ onStreaming, onStatus, onError, onMeta, onToken, onDone }) {
  const inputRef                = useRef(null);
  const [file, setFile]         = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [embeddingChoice, setEmbeddingChoice] = useState('gemini');
  const [summaryModelChoice, setSummaryModelChoice] = useState('gemini');

  const embeddingOptions = {
    gemini: {
      label: 'Gemini embedding (default)',
      provider: 'gemini',
      model: 'models/gemini-embedding-001',
      hint: '',
    },
    bgeSmallZh: {
      label: 'BAAI/bge-small-zh (very slow for test)',
      provider: 'huggingface',
      model: 'BAAI/bge-small-zh',
      hint: 'very slow for test',
    },
  };

  const summaryModelOptions = {
    gemini: {
      label: 'Gemini 2.5 Flash (default)',
      provider: 'gemini',
      model: 'gemini-2.5-flash',
    },
    oss120b: {
      label: 'openai/gpt-oss-120b',
      provider: 'together',
      model: 'openai/gpt-oss-120b',
    },
  };

  function pickFile(f) {
    if (!f) return;
    setFile(f);
  }

  function nextFilenameWithSuffix(name, existingNames) {
    const lowerSet = new Set(existingNames.map((n) => String(n || '').toLowerCase()));
    if (!lowerSet.has(name.toLowerCase())) return name;
    const dot = name.lastIndexOf('.');
    const stem = dot > 0 ? name.slice(0, dot) : name;
    const ext = dot > 0 ? name.slice(dot) : '';
    let n = 1;
    while (true) {
      const candidate = `${stem}(${n})${ext}`;
      if (!lowerSet.has(candidate.toLowerCase())) return candidate;
      n += 1;
    }
  }

  async function handleSubmit(e) {
    e.stopPropagation();
    if (!file) { onError('Please select a .pdf or .txt file first.'); return; }

    onError('');

    try {
      const notes = await listNotes();
      const existing = (notes || []).map((n) => n.filename).filter(Boolean);
      const hasDuplicate = existing.some((n) => n.toLowerCase() === file.name.toLowerCase());
      if (hasDuplicate) {
        const nextName = nextFilenameWithSuffix(file.name, existing);
        const ok = window.confirm(
          `A file named "${file.name}" already exists.\n\nUpload anyway? It will be saved as "${nextName}".`
        );
        if (!ok) return;
      }
    } catch {
      // If pre-check fails, do not block upload; backend still enforces unique naming.
    }

    onStreaming(true);
    onStatus('Uploading...');

    try {
      const selected = embeddingOptions[embeddingChoice] || embeddingOptions.gemini;
      const summarySelected =
        summaryModelOptions[summaryModelChoice] || summaryModelOptions.gemini;
      const res = await summarizeStream(file, {
        embeddingProvider: selected.provider,
        embeddingModel: selected.model,
        generationProvider: summarySelected.provider,
        generationModel: summarySelected.model,
      });
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

      <div
        className="relative rounded-2xl border-2 border-dashed p-10 text-center transition-all duration-200 overflow-hidden group"
        style={{
          borderColor: dragOver ? '#c0392b' : '#d9d1f0',
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

        {/* Icon */}
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
          {' '}
        </p>

        {/* Chosen file badge */}
        {file && (
          <div
            className="inline-flex items-center gap-2 rounded-full border px-4 py-1.5 text-[13px] font-medium text-ink mb-6"
            style={{ borderColor: 'var(--border)', background: '#f5f2fc' }}
          >
            <FileText size={13} style={{ color: '#c0392b' }} />
            {file.name}
          </div>
        )}

        {/* Actions */}
        <div className="max-w-[560px] mx-auto mb-5 text-left">
          <label className="block text-[12px] font-semibold uppercase tracking-wider text-muted mb-2">
            Embedding model
          </label>
          <select
            value={embeddingChoice}
            onChange={(e) => setEmbeddingChoice(e.target.value)}
            className="w-full rounded-xl border px-3 py-2.5 text-[13.5px] text-ink bg-white"
            style={{ borderColor: 'var(--border)' }}
          >
            <option value="gemini">{embeddingOptions.gemini.label}</option>
            <option value="bgeSmallZh">{embeddingOptions.bgeSmallZh.label}</option>
          </select>
          {!!(embeddingOptions[embeddingChoice] || embeddingOptions.gemini).hint && (
            <p className="mt-2 text-[12px] text-muted">
              {(embeddingOptions[embeddingChoice] || embeddingOptions.gemini).hint}
            </p>
          )}
        </div>

        <div className="max-w-[560px] mx-auto mb-5 text-left">
          <label className="block text-[12px] font-semibold uppercase tracking-wider text-muted mb-2">
            Summary model
          </label>
          <select
            value={summaryModelChoice}
            onChange={(e) => setSummaryModelChoice(e.target.value)}
            className="w-full rounded-xl border px-3 py-2.5 text-[13.5px] text-ink bg-white"
            style={{ borderColor: 'var(--border)' }}
          >
            <option value="gemini">{summaryModelOptions.gemini.label}</option>
            <option value="oss120b">{summaryModelOptions.oss120b.label}</option>
          </select>
        </div>

        <div className="flex items-center justify-center gap-3">
          <button
            type="button"
            onClick={() => inputRef.current?.click()}
            className="rounded-xl border px-5 py-2.5 text-[13.5px] font-medium text-muted hover:text-ink transition-all"
            style={{ borderColor: 'var(--border)', background: '#f5f2fc' }}
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
          >
            <UploadCloud size={15} />
            Summarize
          </button>
        </div>
      </div>
    </div>
  );
}
