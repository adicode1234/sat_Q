import { defineConfig } from "vite";
import tailwindcss from "@tailwindcss/vite";
import { fileURLToPath, URL } from "node:url";

export default defineConfig({
  plugins: [
    tailwindcss(),
  ],

  resolve: {
    alias: {
      "@": fileURLToPath(new URL(".", import.meta.url)),
    },
  },

  server: {
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        ws: true,
      },

      "/reports": {
        target: "http://127.0.0.1:8000",
      },
    },
  },
});