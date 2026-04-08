import { useCallback, useEffect, useRef, useState } from 'react';
import Nav from './components/Nav';
import UploadZone from './components/UploadZone';
import { ProcessBar, ErrorBox } from './components/StatusBar';
import SummaryPanel from './components/SummaryPanel';
import Library from './components/Library';
import NoteDetailModal from './components/NoteDetailModal';
import FlashcardsWIP from './components/FlashcardsWIP';
import { normalizeMarkdown } from './utils/markdown';
import { saveToCache } from './utils/summaryCache';

export default function App() {
  const [page, setPage]           = useState('home');
  const [summary, setSummary]     = useState('');
  const [streaming, setStreaming] = useState(false);
  const [error, setError]         = useState('');
  const [meta, setMeta]           = useState(null);
  const [viewNoteId, setViewNoteId] = useState(null);

  const libraryRef    = useRef(null);
  const summaryBuf    = useRef('');
  const activeNoteId  = useRef(null); // tracks note_id of the in-progress stream

  useEffect(() => {
    window.__viewNote = (noteId) => setViewNoteId(noteId);
    return () => { delete window.__viewNote; };
  }, []);

  const handleStreaming = useCallback((on) => {
    setStreaming(on);
    if (on) {
      summaryBuf.current = '';
      activeNoteId.current = null;
      setSummary('');
      setMeta(null);
    }
  }, []);

  const handleMeta = useCallback((metaData) => {
    setMeta(metaData);
    // Capture note_id so we can cache the summary when done
    if (metaData?.note_id) {
      activeNoteId.current = metaData.note_id;
    }
  }, []);

  const handleToken = useCallback((text) => {
    summaryBuf.current = normalizeMarkdown(summaryBuf.current + text);
    setSummary(summaryBuf.current);
  }, []);

  const handleDone = useCallback(() => {
    // Persist the finished summary to localStorage
    if (activeNoteId.current && summaryBuf.current) {
      saveToCache(activeNoteId.current, summaryBuf.current);
    }
    libraryRef.current?.refresh();
  }, []);

  // Called by Library when a cached summary should be displayed directly
  const handleShowCachedSummary = useCallback((noteId, cachedSummary, noteMeta) => {
    summaryBuf.current = cachedSummary;
    setSummary(cachedSummary);
    setMeta(noteMeta);
    setError('');
  }, []);

  const isHome = page === 'home';

  return (
    <div
      className="grid min-h-screen"
      style={{
        gridTemplateRows: '64px 1fr',
        gridTemplateColumns: isHome ? '1fr 320px' : '1fr',
        gridTemplateAreas: isHome ? '"nav nav" "main shelf"' : '"nav" "main"',
      }}
    >
      <div style={{ gridArea: 'nav' }}>
        <Nav currentPage={page} onNavigate={setPage} />
      </div>

      <main
        className="overflow-y-auto flex flex-col gap-6"
        style={{ gridArea: 'main', padding: isHome ? '40px' : '0', background: '#faf9ff' }}
      >
        {isHome ? (
          <>
            <UploadZone
              onStreaming={handleStreaming}
              onStatus={() => {}}
              onError={setError}
              onMeta={handleMeta}
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

      {isHome && (
        <div style={{ gridArea: 'shelf' }}>
          <Library
            ref={libraryRef}
            onStreaming={handleStreaming}
            onStatus={() => {}}
            onError={setError}
            onMeta={handleMeta}
            onToken={handleToken}
            onDone={handleDone}
            onShowCachedSummary={handleShowCachedSummary}
          />
        </div>
      )}

      <NoteDetailModal
        noteId={viewNoteId}
        onClose={() => setViewNoteId(null)}
      />
    </div>
  );
}
