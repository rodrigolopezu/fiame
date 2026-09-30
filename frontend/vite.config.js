import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// Las llamadas a /api se redirigen al backend FastAPI local.
export default defineConfig({
  plugins: [vue()],
  server: {
    port: Number(process.env.PORT) || 5180,
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
})
