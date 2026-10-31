import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Deployed only to Vercel, served at the domain root, so Vite's default base ('/') is correct.
export default defineConfig({
  plugins: [react()],
})
