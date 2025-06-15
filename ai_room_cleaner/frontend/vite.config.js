import { defineConfig } from 'vite';

export default defineConfig({
  build: {
    outDir: 'dist',
    assetsDir: '',
    rollupOptions: {
      input: '/ai_room_cleaner/frontend/index.html'
    }
  },
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:8000'
    }
  }
});