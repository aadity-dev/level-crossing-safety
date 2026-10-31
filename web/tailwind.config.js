/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: {
          dark: '#0B0D10',
          card: '#13171C',
          cardHover: '#1A2027',
          elevated: '#171C23',
        },
        border: {
          subtle: '#252B33',
          highlight: '#323B47',
        },
        text: {
          primary: '#F5F7FA',
          secondary: '#929BA8',
          muted: '#636C7A',
        },
        railway: {
          critical: '#EF4444',
          high: '#F97316',
          medium: '#F59E0B',
          operational: '#10B981',
          cyan: '#06B6D4',
          blue: '#3B82F6',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      }
    },
  },
  plugins: [],
}
