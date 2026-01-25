---
id: task-100
title: 'P4: Set up frontend build tooling (Vite + Tailwind + Basecoat)'
status: Done
assignee: []
created_date: '2026-01-12 04:08'
updated_date: '2026-01-24 22:28'
labels:
  - frontend
  - infrastructure
  - phase-4
milestone: Tauri Migration
dependencies:
  - task-093
priority: high
ordinal: 94382.8125
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Configure the frontend build environment for AlpineJS + Basecoat development.

**Setup steps:**
1. Initialize npm project in `src/`
2. Install dependencies:
   ```bash
   npm install alpinejs
   npm install -D vite tailwindcss postcss autoprefixer
   ```
3. Configure Tailwind with Basecoat:
   ```css
   /* src/style.css */
   @import "tailwindcss";
   @import "basecoat-css";
   ```
4. Configure Vite for Tauri:
   ```javascript
   // vite.config.js
   export default {
     root: 'src',
     build: {
       outDir: '../dist',
       emptyOutDir: true,
     }
   }
   ```
5. Update tauri.conf.json to use Vite dev server

**File structure:**
```
src/
├── index.html          # Main entry
├── main.js             # Alpine initialization
├── style.css           # Tailwind + Basecoat
├── js/
│   ├── stores.js       # Alpine.store definitions
│   └── api.js          # Backend API client
└── vite.config.js
```
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 npm project initialized with package.json
- [x] #2 Vite dev server runs and serves index.html
- [x] #3 Tailwind CSS compiles correctly
- [x] #4 Basecoat classes available
- [x] #5 AlpineJS initializes without errors
- [x] #6 Hot reload works during development
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Implementation Notes (2026-01-12)

### Repo Reorganization
Moved all business logic under `app/` directory:
- `app/backend/` - Python FastAPI sidecar
- `app/core/` - Python business logic
- `app/utils/` - Python utilities
- `app/config.py` - App config
- `app/main.py` - Legacy Tkinter entrypoint
- `app/src/` - Zig build files
- `app/frontend/` - Vite + Tailwind + Alpine + Basecoat

### Frontend Stack
- **Vite** with `@tailwindcss/vite` plugin
- **Tailwind v4** (latest)
- **Basecoat CSS** for components
- **AlpineJS** (ESM import, no CDN)
- **Basecoat JS** copied to `public/js/basecoat/` (Option B approach)

### Key Configuration
- `tauri.conf.json` uses simple `npm run dev` / `npm run build` commands
- Commands run from `app/frontend/` when using `npm --prefix app/frontend exec tauri dev`
- `frontendDist` path: `../app/frontend/dist` (relative to src-tauri)

### Verified Working
- `task tauri:dev` launches Vite + Tauri window
- Hot reload works
- Basecoat buttons render correctly
- Alpine.js initializes and binds data
<!-- SECTION:NOTES:END -->
