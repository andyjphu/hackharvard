import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'
import tailwindcss from '@tailwindcss/vite'
import electron from 'vite-plugin-electron';
import path from "node:path";

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),

    tailwindcss()],
})
