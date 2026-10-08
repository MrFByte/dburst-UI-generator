/// <reference types="vitest" />
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import basicSsl from '@vitejs/plugin-basic-ssl'
import path from 'path'

// https://vite.dev/config/
export default defineConfig(({ command }) => ({
  plugins: [
    react({
      babel: {
        plugins: [['babel-plugin-react-compiler']],
      },
    }),
    tailwindcss(),
    // Serves the dev server over HTTPS so StackBlitz WebContainer API
    // accepts https://localhost:5173 as an allowed referrer.
    // Dev only — production hosting (Vercel) provides real HTTPS.
    ...(command === 'serve' ? [basicSsl()] : []),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    },
  },
  server: {
    headers: {
      // Required for WebContainer (SharedArrayBuffer).
      // NOTE: 'same-origin' blocks OAuth popups — Google login uses redirect
      // flow (not popup) to stay compatible with this header.
      // For Login
      // 'Cross-Origin-Opener-Policy': 'same-origin-allow-popups',
      // For WebContainer
      'Cross-Origin-Opener-Policy': 'same-origin',
      'Cross-Origin-Embedder-Policy': 'credentialless',
    },
    proxy: {
      '/api': {
        target: 'https://localhost:8000',
        changeOrigin: true,
        secure: false, // backend uses a local mkcert-signed cert, not a CA-trusted one
      }
    }
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
  },
}))
