import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@domain': path.resolve(__dirname, './src/domain'),
      '@application': path.resolve(__dirname, './src/application'),
      '@infrastructure': path.resolve(__dirname, './src/infrastructure'),
      '@presentation': path.resolve(__dirname, './src/presentation'),
      '@shared': path.resolve(__dirname, './src/shared'),
    },
  },
  server: {
    host: true,
    port: 5173,
    watch: {
      usePolling: true
    },
    proxy: {
      '/auth': { target: 'http://localhost:8000', changeOrigin: true },
      '/users': { target: 'http://localhost:8000', changeOrigin: true },
      '/classes': { target: 'http://localhost:8000', changeOrigin: true },
      '/exams': { target: 'http://localhost:8000', changeOrigin: true },
      '/exam-questions': { target: 'http://localhost:8000', changeOrigin: true },
      '/student-answers': { target: 'http://localhost:8000', changeOrigin: true },
      '/attachments': { target: 'http://localhost:8000', changeOrigin: true },
      '/grading-criteria': { target: 'http://localhost:8000', changeOrigin: true },
      '/exam-criteria': { target: 'http://localhost:8000', changeOrigin: true },
      '/question-criteria-override': { target: 'http://localhost:8000', changeOrigin: true },
      '/analytics': { target: 'http://localhost:8000', changeOrigin: true },
      '/reviews': { target: 'http://localhost:8000', changeOrigin: true },
      '/dashboard': { target: 'http://localhost:8000', changeOrigin: true },
      '/health': { target: 'http://localhost:8000', changeOrigin: true },
    }
  },
})
