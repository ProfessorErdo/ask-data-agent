import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/chat': 'http://localhost:8000',
      '/brd-template': 'http://localhost:8000',
      '/export-brd': 'http://localhost:8000'
    }
  }
})