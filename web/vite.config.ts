import { defineConfig } from "vite";

// Base path: at GitHub Pages we serve under /<repo>/. VITE_BASE is set by the
// deploy workflow. Locally, "/" works for both `npm run dev` and `npm run preview`.
export default defineConfig({
  base: process.env.VITE_BASE ?? "/",
  server: { port: 5173 },
});
