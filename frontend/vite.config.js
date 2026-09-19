import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// /api/* is forwarded to the Django dev server
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { "/api": "http://localhost:8000" },
  },
  test: {
    environment: "jsdom",
    globals: true,
  },
});
