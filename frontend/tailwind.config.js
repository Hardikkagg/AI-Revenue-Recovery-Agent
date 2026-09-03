/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: '#050816',
        surface: '#0f172a',
        surfaceElevated: '#111827',
        border: '#1e293b',
        text: '#e2e8f0',
        muted: '#94a3b8',
        ai: '#60a5fa',
        success: '#34d399',
        warning: '#fbbf24',
        danger: '#f87171',
      },
      boxShadow: {
        glow: '0 0 0 1px rgba(148,163,184,0.15), 0 18px 60px rgba(2,6,23,0.45)',
      },
      fontFamily: {
        sans: ['Inter', 'Segoe UI', 'sans-serif'],
      },
    },
  },
  plugins: [],
}

