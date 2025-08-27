/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: ["./pages/**/*.{js,jsx,ts,tsx}", "./components/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0a0f1a",
        panel: "#0f1726",
        accent: "#00F0FF",
        magenta: "#ff00f7",
        lemon: "#d6ff00",
        cyber: {
          100: "#a7f3d0",
          200: "#6ee7b7",
          300: "#34d399",
          400: "#10b981",
          500: "#059669"
        }
      },
      boxShadow: {
        glow: "0 0 10px rgba(0,240,255,0.6), 0 0 20px rgba(255,0,247,0.25)"
      },
      dropShadow: {
        glow: ["0 0 8px #00F0FF", "0 0 16px #ff00f7"]
      }
    },
  },
  plugins: [],
};
