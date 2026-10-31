import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Deployed only to Vercel, served at the domain root, so Vite's default base ('/') is correct.
// In development, /api is forwarded to the local backend (server/, uvicorn on :8000); in
// production vercel.json rewrites it to Railway, so the browser always sees one origin.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: { '/api': 'http://localhost:8000' },
  },
})
