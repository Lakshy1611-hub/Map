import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./app/**/*.{js,ts,jsx,tsx}', './components/**/*.{js,ts,jsx,tsx}', './lib/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'Noto Sans Devanagari', 'system-ui', 'sans-serif']
      },
      boxShadow: {
        glow: '0 24px 80px rgba(34, 211, 238, 0.22)'
      },
      backgroundImage: {
        'radial-grid': 'radial-gradient(circle at 20% 20%, rgba(45,212,191,.28), transparent 30%), radial-gradient(circle at 80% 10%, rgba(129,140,248,.30), transparent 28%), radial-gradient(circle at 50% 90%, rgba(244,114,182,.22), transparent 30%)'
      }
    }
  },
  plugins: []
};

export default config;
