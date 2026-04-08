import { AlertCircle } from 'lucide-react';

export function ProcessBar({ visible }) {
  if (!visible) return null;
  return (
    <div
      className="flex flex-col gap-3 rounded-2xl border px-6 py-5 animate-fade-up"
      style={{ borderColor: 'var(--border)', background: '#13161f' }}
    >
      <div className="flex items-center justify-between">
        <span className="text-[13px] font-medium text-ink">Summarizing your document…</span>
        <span className="text-[11.5px] font-mono text-muted">AI at work</span>
      </div>
      {/* Indeterminate shimmer bar */}
      <div
        className="relative h-1 rounded-full overflow-hidden"
        style={{ background: 'rgba(255,255,255,0.06)' }}
      >
        <div
          className="absolute inset-y-0 rounded-full"
          style={{
            width: '45%',
            background: 'linear-gradient(90deg, transparent, #00d4aa, transparent)',
            animation: 'shimmer 1.6s ease-in-out infinite',
          }}
        />
      </div>
      <style>{`
        @keyframes shimmer {
          0%   { left: -50%; }
          100% { left: 110%; }
        }
      `}</style>
    </div>
  );
}

export function ErrorBox({ message, onDismiss }) {
  if (!message) return null;
  return (
    <div
      className="flex items-start gap-3 rounded-2xl border px-5 py-4 text-[13.5px] text-danger animate-fade-up"
      style={{ borderColor: 'rgba(255,92,92,0.25)', background: 'rgba(255,92,92,0.06)' }}
    >
      <AlertCircle size={15} className="flex-shrink-0 mt-0.5" />
      <span className="flex-1">{message}</span>
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
