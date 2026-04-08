import { AlertCircle } from 'lucide-react';

export function ProcessBar({ visible }) {
  if (!visible) return null;
  return (
    <div
      className="flex flex-col gap-3 rounded-2xl border px-6 py-5 bg-surface animate-fade-up"
      style={{ borderColor: 'var(--border)', boxShadow: 'var(--shadow-sm)' }}
    >
      <div className="flex items-center justify-between">
        <span className="text-[13.5px] font-semibold text-ink">Summarizing your document…</span>
        <span className="text-[11px] font-mono text-muted">AI at work</span>
      </div>

      {/* Indeterminate shimmer */}
      <div className="h-1 rounded-full overflow-hidden bg-surface2">
        <div
          className="absolute h-full rounded-full"
          style={{
            width: '40%',
            background: 'linear-gradient(90deg, transparent, #c0392b, transparent)',
            animation: 'shimmer 1.6s ease-in-out infinite',
            position: 'relative',
          }}
        />
      </div>

      <style>{`
        @keyframes shimmer {
          0%   { left: -45%; }
          100% { left: 110%; }
        }
        div.shimmer-track { position: relative; }
      `}</style>
    </div>
  );
}

export function ErrorBox({ message, onDismiss }) {
  if (!message) return null;
  return (
    <div
      className="flex items-start gap-3 rounded-2xl border px-5 py-4 text-[13.5px] animate-fade-up bg-surface"
      style={{ borderColor: 'rgba(220,38,38,0.25)', background: 'rgba(220,38,38,0.04)' }}
    >
      <AlertCircle size={15} className="flex-shrink-0 mt-0.5" style={{ color: '#dc2626' }} />
      <span className="flex-1" style={{ color: '#b91c1c' }}>{message}</span>
      {onDismiss && (
        <button
          onClick={onDismiss}
          className="text-muted hover:text-danger transition-colors text-xs flex-shrink-0"
        >
          ✕
        </button>
      )}
    </div>
  );
}
