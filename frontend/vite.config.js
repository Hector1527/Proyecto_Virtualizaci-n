import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

export default defineConfig({
  plugins: [vue(), vueDevTools()],

  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },

  server: {
    proxy: {
      '/api/reportes': {
        target: 'http://localhost:5004',
        changeOrigin: true,
      },

      '/api/inventario': {
        target: 'http://localhost:5001',
        changeOrigin: true,
      },


      '/api/pedidos': {
        target: 'http://localhost:5003',
        changeOrigin: true,
      },

    },
  }, 
})