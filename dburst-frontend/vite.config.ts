/// <reference types="vitest" />
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react({
      babel: {
        plugins: [['babel-plugin-react-compiler']],
      },
    }),
    tailwindcss(),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    },
  },
  server: {
    // Disables Vite's Host-header allowlist (DNS-rebinding protection) so
    // the dev server accepts requests through a tunnel (ngrok, etc.) whose
    // hostname changes on every run. Dev-only — vite.config.ts has no
    // effect on the production build, which Vercel serves statically.
    allowedHosts: true,
    headers: {
      // Required for WebContainer (crossOriginIsolated). Safe with OAuth
      // here because both Google and GitHub login use full-page redirects,
      // not window.open() popups — COOP:same-origin only severs
      // window.opener, which a redirect flow never relies on. Mirrored in
      // production via vercel.json's headers (vite's server.headers only
      // applies to this dev server, not the deployed build).
      'Cross-Origin-Opener-Policy': 'same-origin',
      'Cross-Origin-Embedder-Policy': 'credentialless',
    },
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
  },
})
