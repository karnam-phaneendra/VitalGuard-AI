/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#6366f1",
        secondary: "#c084fc",
        dark: "#0f172a",
        card: "#1e293b",
      }
    },
  },
  plugins: [],
}
