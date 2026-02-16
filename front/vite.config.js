import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true
      },
      '/py-api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        // 将前端的 /py-api 前缀重写为后端的 /api 前缀
        rewrite: (path) => path.replace(/^\/py-api/, '/api')
      }
    }
  }
})

