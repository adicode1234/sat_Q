# Preserved design prototype

The production app is the Vite SPA at `../src.jsx`, loaded by `../index.html`.
It does not use a router or an SSR server.

`index.tsx` exports the retained `SatVisionNexus` React design prototype.
It uses the local simulated agent in `../lib/agent.ts`; it is not connected to
production API analysis and is not mounted by the active app. Its original
`styles.css` is retained here as design source (including its unconfigured
Tailwind directives); it is not the production `../style.css`.

The unused TanStack root, router, generated route tree, server and Start
middleware were removed after checking all frontend references. The original
files are recoverable from `../../.repair-backup/frontend-before.zip`.
All remaining TypeScript here is included in the normal strict type check.
