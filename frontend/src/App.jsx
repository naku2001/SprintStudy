import { useCallback, useEffect, useRef, useState } from 'react';
import Nav from './components/Nav';
import UploadZone from './components/UploadZone';
import { ProcessBar, ErrorBox } from './components/StatusBar';
import SummaryPanel from './components/SummaryPanel';
import Library from './components/Library';
import NoteDetailModal from './components/NoteDetailModal';
import FlashcardsWIP from './components/FlashcardsWIP';
import { normalizeMarkdown } from './utils/markdown';

export default function App() {
  // Page routing
  const [page, setPage] = useState('home');

  // Summary state
  const [summary, setSummary]     = useState('');
  const [streaming, setStreaming] = useState(false);
  const [error, setError]         = useState('');
  const [meta, setMeta]           = useState(null);

  // Modal state
  const [viewNoteId, setViewNoteId] = useState(null);

  const libraryRef = useRef(null);
  const summaryBuf = useRef('');

  // Expose viewNote globally so NoteCard's onView can call it
  useEffect(() => {
    window.__viewNote = (noteId) => setViewNoteId(noteId);
    return () => { delete window.__viewNote; };
  }, []);

  const handleStreaming = useCallback((on) => {
    setStreaming(on);
    if (on) {
      summaryBuf.current = '';
      setSummary('');
      setMeta(null);
    }
  }, []);

  const handleToken = useCallback((text) => {
    summaryBuf.current = normalizeMarkdown(summaryBuf.current + text);
    setSummary(summaryBuf.current);
  }, []);

  const handleDone = useCallback(() => {
    libraryRef.current?.refresh();
  }, []);

  const isHome = page === 'home';

  return (
    <div
      className="grid min-h-screen"
      style={{
        gridTemplateRows: '60px 1fr',
        gridTemplateColumns: isHome ? '1fr 320px' : '1fr',
        gridTemplateAreas: isHome ? '"nav nav" "main shelf"' : '"nav" "main"',
      }}
    >
      {/* ── Nav ─────────────────────────────────────────── */}
      <div style={{ gridArea: 'nav' }}>
        <Nav currentPage={page} onNavigate={setPage} />
      </div>

      {/* ── Main content ────────────────────────────────── */}
      <main
        className="overflow-y-auto flex flex-col gap-6"
        style={{
          gridArea: 'main',
          padding: isHome ? '40px' : '0',
          background: '#faf9ff',
        }}
      >
        {isHome ? (
          <>
            <UploadZone
              onStreaming={handleStreaming}
              onStatus={() => {}}
              onError={setError}
              onMeta={setMeta}
              onToken={handleToken}
              onDone={handleDone}
            />

            <ProcessBar visible={streaming} />

            <ErrorBox message={error} onDismiss={() => setError('')} />

            <SummaryPanel summary={summary} streaming={streaming} meta={meta} />
          </>
        ) : (
          <FlashcardsWIP />
        )}
      </main>

      {/* ── Library sidebar (home only) ───────────────── */}
      {isHome && (
        <div style={{ gridArea: 'shelf' }}>
          <Library
            ref={libraryRef}
            onStreaming={handleStreaming}
            onStatus={() => {}}
            onError={setError}
            onMeta={setMeta}
            onToken={handleToken}
            onDone={handleDone}
          />
        </div>
      )}

      {/* ── Note detail modal ────────────────────────────── */}
      <NoteDetailModal
        noteId={viewNoteId}
        onClose={() => setViewNoteId(null)}
      />
    </div>
  );
}
