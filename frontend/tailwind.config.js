/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg:       '#0c0e14',
        surface:  '#13161f',
        surface2: '#1a1e2a',
        accent:   '#00d4aa',
        gold:     '#e8c56a',
        danger:   '#ff5c5c',
        ink:      '#dde2ef',
        muted:    '#5c6478',
        prose:    '#9da8bf',
      },
      fontFamily: {
        serif: ['"DM Serif Display"', 'Georgia', 'serif'],
        sans:  ['Outfit', 'system-ui', 'sans-serif'],
        mono:  ['"JetBrains Mono"', 'monospace'],
      },
      animation: {
        'pulse-slow': 'pulse 2.2s ease-in-out infinite',
        'spin-fast':  'spin 0.75s linear infinite',
        'fade-up':    'fadeUp 0.35s ease both',
        'card-in':    'cardIn 0.3s ease both',
        'modal-in':   'modalIn 0.22s cubic-bezier(.34,1.56,.64,1)',
        'blink':      'blink 1s step-end infinite',
      },
      keyframes: {
        fadeUp:  { from: { opacity: 0, transform: 'translateY(10px)' }, to: { opacity: 1, transform: 'translateY(0)' } },
        cardIn:  { from: { opacity: 0, transform: 'translateX(10px)' }, to: { opacity: 1, transform: 'translateX(0)' } },
        modalIn: { from: { opacity: 0, transform: 'scale(0.94) translateY(14px)' }, to: { opacity: 1, transform: 'scale(1) translateY(0)' } },
        blink:   { '0%, 100%': { opacity: 1 }, '50%': { opacity: 0 } },
      },
    },
  },
  plugins: [],
};
