export default function FlashcardsWIP() {
  return (
    <div className="flex flex-col items-center justify-center min-h-full py-24 px-8 text-center">

      {/* Stacked card visual */}
      <div className="relative w-52 h-36 mb-14">
        <div
          className="absolute inset-0 rounded-2xl border rotate-6 translate-x-3 translate-y-1"
          style={{ background: '#f0eefa', borderColor: '#e2daf5' }}
        />
        <div
          className="absolute inset-0 rounded-2xl border rotate-2 translate-x-1"
          style={{ background: '#f8f5ff', borderColor: '#d9d1f0' }}
        />
        <div
          className="absolute inset-0 rounded-2xl border bg-surface flex flex-col items-center justify-center gap-2 shadow-card"
          style={{ borderColor: 'rgba(192,57,43,0.3)' }}
        >
          <div
            className="w-9 h-9 rounded-xl flex items-center justify-center"
            style={{ background: 'rgba(192,57,43,0.08)' }}
          >
            <span className="text-lg">🃏</span>
          </div>
          <span
            className="text-[10px] font-bold uppercase tracking-widest"
            style={{ color: '#c0392b' }}
          >
            Flashcards
          </span>
        </div>
      </div>

      <h1 className="font-serif text-4xl font-semibold italic text-ink mb-4">
        Coming Soon
      </h1>
      <p className="text-[15px] text-muted max-w-sm leading-relaxed mb-10">
        We're building an AI-powered flashcard generator that converts your
        study notes.
      </p>

      {/* Feature chips */}
      <div className="flex flex-wrap justify-center gap-2 mb-10">
        {[
          'Auto-generated from summaries',
          'Q&A',
          'Perfomance tracking',
         
        ].map((label) => (
          <span
            key={label}
            className="text-[12.5px] font-medium px-3.5 py-1.5 rounded-full border"
            style={{ borderColor: 'var(--border)', background: '#f8f5ff', color: '#9587c8' }}
          >
            {label}
          </span>
        ))}
      </div>

      {/* Progress bar */}
      <div
        className="w-60 h-1.5 rounded-full overflow-hidden"
        style={{ background: '#ede8f8' }}
      >
        <div
          className="h-full rounded-full"
          style={{ width: '35%', background: 'linear-gradient(90deg, #c0392b, #e74c3c)' }}
        />
      </div>
      <p className="text-[11.5px] text-muted mt-2 font-mono">35% complete</p>
    </div>
  );
}
