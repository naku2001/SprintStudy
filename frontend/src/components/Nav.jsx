export default function Nav({ currentPage, onNavigate }) {
  return (
    <nav
      className="sticky top-0 z-50 flex items-center justify-between px-8 h-[64px] bg-surface border-b"
      style={{ borderColor: 'var(--border)', boxShadow: '0 1px 0 rgba(45,27,105,0.06)' }}
    >
      {/* Brand */}
      <button
        onClick={() => onNavigate('home')}
        className="flex items-center gap-3 hover:opacity-75 transition-opacity"
      >
        <div
          className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
          style={{ background: '#c0392b' }}
        >
          <span className="text-white font-serif font-bold text-sm leading-none">N</span>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="font-serif text-[20px] font-semibold text-ink tracking-tight">Njere</span>
          <span className="text-[11px] font-medium tracking-widest uppercase text-muted hidden sm:block">
            Study Companion
          </span>
        </div>
      </button>

      {/* Nav links + badge */}
      <div className="flex items-center gap-1">
        <NavLink active={currentPage === 'home'} onClick={() => onNavigate('home')}>
          Summarize
        </NavLink>
        <NavLink active={currentPage === 'flashcards'} onClick={() => onNavigate('flashcards')}>
          Flashcards
        </NavLink>

        <div
          className="ml-4 flex items-center gap-2 text-[11px] font-mono font-medium px-3 py-1.5 rounded-full border"
          style={{
            color: '#c0392b',
            background: 'rgba(192,57,43,0.06)',
            borderColor: 'rgba(192,57,43,0.2)',
          }}
        >
          <span
            className="w-[5px] h-[5px] rounded-full flex-shrink-0"
            style={{ background: '#c0392b', animation: 'pulse 2s ease-in-out infinite' }}
          />
          Model Selectable
        </div>
      </div>
    </nav>
  );
}

function NavLink({ children, active, onClick }) {
  return (
    <button
      onClick={onClick}
      className={[
        'px-4 py-2 rounded-lg text-[13.5px] font-medium transition-all duration-150',
        active
          ? 'bg-surface2 text-ink'
          : 'text-muted hover:text-ink hover:bg-surface2',
      ].join(' ')}
    >
      {children}
    </button>
  );
}
