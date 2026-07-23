/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        cyber: {
          bg: '#0a0a0f',
          card: 'rgba(18, 18, 26, 0.7)',
          border: 'rgba(255, 255, 255, 0.1)',
          neonRed: '#ff0055',
          neonGreen: '#00ff66',
          neonBlue: '#00ccff'
        }
      },
      animation: {
        'glitch': 'glitch 1s infinite',
      }
    },
  },
  plugins: [],
};