import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [
        svelte()
    ],
    build: {
        outDir: "../dictum/dictum/server/static/",
    },
    server: {
        cors: {
            origin: "*",
        },
        proxy: {
            "^/static": { target: "http://localhost:8000" },
            "^/graphql": { target: "http://localhost:8000" }
        }
    }
})