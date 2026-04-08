export default function Nav({ currentPage, onNavigate }) {
  return (
    <nav className="sticky top-0 z-50 flex items-center justify-between px-8 h-[60px] border-b bg-bg/85 backdrop-blur-xl"
         style={{ borderColor: 'var(--border)' }}>

      {/* Brand */}
      <button
        onClick={() => onNavigate('home')}
        className="flex items-baseline gap-3 hover:opacity-80 transition-opacity"
      >
        <span className="font-serif text-xl italic text-ink tracking-tight">Njere</span>
        <span className="w-[5px] h-[5px] rounded-full bg-accent mb-0.5 flex-shrink-0"
              style={{ display: 'inline-block' }} />
        <span className="text-[11px] font-medium tracking-widest uppercase text-muted">
          Study Companion
        </span>
      </button>

      {/* Nav links + badge */}
      <div className="flex items-center gap-3">

        <button
          onClick={() => onNavigate('home')}
          className={[
            'text-[13px] font-medium px-3 py-1.5 rounded-lg transition-colors',
            currentPage === 'home'
              ? 'text-ink bg-surface2'
              : 'text-muted hover:text-ink',
          ].join(' ')}
        >
          Summarize
        </button>

        <button
          onClick={() => onNavigate('flashcards')}
          className={[
            'text-[13px] font-medium px-3 py-1.5 rounded-lg transition-colors',
            currentPage === 'flashcards'
              ? 'text-ink bg-surface2'
              : 'text-muted hover:text-ink',
          ].join(' ')}
        >
          Flashcards
        </button>

        <div
          className="flex items-center gap-2 text-[11.5px] text-accent font-mono px-3 py-1.5 rounded-full border ml-2"
          style={{ background: 'var(--accent-dim)', borderColor: 'rgba(0,212,170,0.18)' }}
        >
          <span className="w-[5px] h-[5px] rounded-full bg-accent flex-shrink-0 animate-pulse-slow" />
          gemini-2.5-flash
        </div>
      </div>
    </nav>
  );
}
