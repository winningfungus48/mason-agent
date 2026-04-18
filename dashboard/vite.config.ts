import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    // Listen on all interfaces so Chrome, Cursor Simple Browser, and LAN can reach the dev server.
    host: true,
    port: 5173,
    strictPort: false,
    // Open the app in the default browser as soon as the dev server is ready (no manual URL).
    open: true,
  },
  preview: {
    host: true,
    port: 4173,
  },
})
