/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg:       '#f7f5f2',
        surface:  '#ffffff',
        surface2: '#f0ede8',
        accent:   '#c0392b',
        'accent-dark': '#96281b',
        gold:     '#b07d2e',
        danger:   '#dc2626',
        ink:      '#1c1917',
        muted:    '#78716c',
        prose:    '#44403c',
        border:   '#e3ddd7',
      },
      fontFamily: {
        serif: ['"Playfair Display"', 'Georgia', 'serif'],
        sans:  ['"Plus Jakarta Sans"', 'system-ui', 'sans-serif'],
        mono:  ['"IBM Plex Mono"', 'monospace'],
      },
      animation: {
        'pulse-slow': 'pulse 2.2s ease-in-out infinite',
        'spin-fast':  'spin 0.75s linear infinite',
        'fade-up':    'fadeUp 0.3s ease both',
        'card-in':    'cardIn 0.25s ease both',
        'modal-in':   'modalIn 0.2s cubic-bezier(.34,1.4,.64,1)',
        'blink':      'blink 1s step-end infinite',
      },
      keyframes: {
        fadeUp:  { from: { opacity: 0, transform: 'translateY(8px)' }, to: { opacity: 1, transform: 'translateY(0)' } },
        cardIn:  { from: { opacity: 0, transform: 'translateX(8px)'  }, to: { opacity: 1, transform: 'translateX(0)' } },
        modalIn: { from: { opacity: 0, transform: 'scale(0.96) translateY(10px)' }, to: { opacity: 1, transform: 'scale(1) translateY(0)' } },
        blink:   { '0%, 100%': { opacity: 1 }, '50%': { opacity: 0 } },
      },
      boxShadow: {
        'card':  '0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)',
        'card-hover': '0 4px 12px rgba(0,0,0,0.08), 0 2px 4px rgba(0,0,0,0.04)',
        'modal': '0 20px 60px rgba(0,0,0,0.12), 0 8px 24px rgba(0,0,0,0.08)',
        'btn':   '0 1px 3px rgba(192,57,43,0.25)',
        'btn-hover': '0 4px 14px rgba(192,57,43,0.3)',
      },
    },
  },
  plugins: [],
};
