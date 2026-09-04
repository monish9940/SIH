/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          950: '#060D17',
          900: '#0B192C',
          800: '#0F2137',
          700: '#1E293B',
          600: '#334155',
        },
        gov: {
          blue: '#0B192C',
          lightBg: '#F8FAFC',
          border: '#E2E8F0',
          orange: '#F97316',
          darkOrange: '#EA580C',
          accentGreen: '#16A34A',
          accentRed: '#DC2626',
        }
      }
    },
  },
  plugins: [],
}
