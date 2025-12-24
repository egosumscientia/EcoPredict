/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",   // Escanea todas las plantillas Jinja2
    "./static/js/**/*.js"      // (futuro) scripts JS si agregas Recharts o lógica interactiva
  ],
  darkMode: "class",            // Modo oscuro activado por clase (ya usado en base.html)
  theme: {
    extend: {
      colors: {
        cyan: {
          DEFAULT: '#06b6d4',
          light: '#22d3ee',
          dark: '#0891b2',
        },
        emerald: {
          DEFAULT: '#10b981',
          light: '#34d399',
          dark: '#047857',
        },
      },
    },
  },
  plugins: [],
}
