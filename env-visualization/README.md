<div align="center">

# AgentGym Environment Visualization

A lightweight Vue 3 frontend for interactively visualizing and debugging multiple AgentGym task environments (BabyAI · SciWorld · SearchQA · TextCraft · WebArena).

</div>

## Requirements

- Node.js >= 18
- npm

## Quick Start

```bash
cd env-visualization
# Install dependencies
npm install

cd src/environments/{env}/client/{env}client.js
# modify {env}client constructor server port to your own env server

# Start dev server
cd env-visualization
npm run dev

# Production build
npm run build

# Preview the built bundle locally
npm run preview
```

On Windows (cmd / PowerShell) run the same commands directly.

## Add New Environment

1. Create `src/environments/myenv/`.
2. Implement `index.js` exporting metadata + factory / component references:
   ```js
   export default {
       id: 'myenv',
       name: 'My Env',
       createClient(opts) { /* ... */ },
       component: () => import('./components/MyEnvViewer.vue')
   };
   ```
3. Register it in `src/environments/index.js`:
   ```js
   import myenv from './myenv';
   export default { /* existing envs */, myenv };
   ```
4. Add any static assets under `public/` (e.g. `public/assets/myenv/`).
5. (Optional) Extend service logic if the backend protocol differs.
