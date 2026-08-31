/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: "#0A0C10",
        panel: "#12151B",
        "panel-2": "#171B22",
        line: "#262B33",
        "line-soft": "#1B1F27",
        paper: "#E9E6DC",
        "paper-dim": "#9298A3",
        "paper-faint": "#5B616D",
        signal: "#FF6A2E",
        "signal-dim": "#7A3E22",
        alert: "#FF3B3B",
        caution: "#F2C24C",
        confirmed: "#33D18E",
      },
      fontFamily: {
        display: ['Space Grotesk', 'sans-serif'],
        sans: ['IBM Plex Sans', 'sans-serif'],
        mono: ['IBM Plex Mono', 'monospace'],
      }
    },
  },
  plugins: [],
};
