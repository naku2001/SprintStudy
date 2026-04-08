export default function FlashcardsWIP() {
  return (
    <div className="flex flex-col items-center justify-center min-h-full py-24 px-8 text-center">

      {/* Stacked card illustration */}
      <div className="relative w-48 h-32 mb-12">
        {/* Bottom card */}
        <div
          className="absolute inset-0 rounded-2xl border rotate-6 translate-x-3 translate-y-1"
          style={{ background: '#1a1e2a', borderColor: 'var(--border)' }}
        />
        {/* Middle card */}
        <div
          className="absolute inset-0 rounded-2xl border rotate-2 translate-x-1"
          style={{ background: '#1e2230', borderColor: 'rgba(0,212,170,0.12)' }}
        />
        {/* Front card */}
        <div
          className="absolute inset-0 rounded-2xl border flex flex-col items-center justify-center gap-2"
          style={{ background: '#13161f', borderColor: 'rgba(0,212,170,0.3)' }}
        >
          <div className="text-2xl">🃏</div>
          <div
            className="text-[10px] font-mono font-medium uppercase tracking-widest"
            style={{ color: '#00d4aa' }}
          >
            Flashcards
          </div>
        </div>
      </div>

      {/* Heading */}
      <h1 className="font-serif text-4xl italic text-ink mb-4">
        Coming Soon
      </h1>

      <p className="text-[15px] text-muted max-w-sm leading-relaxed mb-8">
        We're building an AI-powered flashcard generator that transforms your
        study notes into active-recall sets — automatically.
      </p>

      {/* Feature preview chips */}
      <div className="flex flex-wrap justify-center gap-2 mb-10">
        {[
          'Auto-generated from summaries',
          'Anki-style active recall',
          'Spaced repetition',
          'Export to Anki deck',
        ].map((label) => (
          <span
            key={label}
            className="text-[12px] font-medium px-3 py-1.5 rounded-full border"
            style={{
              borderColor: 'var(--border)',
              background: '#1a1e2a',
              color: '#5c6478',
            }}
          >
            {label}
          </span>
        ))}
      </div>

      {/* Progress bar */}
      <div
        className="w-64 h-1 rounded-full overflow-hidden"
        style={{ background: 'var(--border)' }}
      >
        <div
          className="h-full rounded-full"
          style={{
            width: '35%',
            background: 'linear-gradient(90deg, #00d4aa, #00d4aa88)',
          }}
        />
      </div>
      <p className="text-[11.5px] text-muted mt-2.5 font-mono">35% complete</p>
    </div>
  );
}
