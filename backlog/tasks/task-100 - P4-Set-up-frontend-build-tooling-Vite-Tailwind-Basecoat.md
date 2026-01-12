---
id: task-100
title: 'P4: Set up frontend build tooling (Vite + Tailwind + Basecoat)'
status: To Do
assignee: []
created_date: '2026-01-12 04:08'
labels:
  - frontend
  - infrastructure
  - phase-4
milestone: Tauri Migration
dependencies:
  - task-093
priority: high
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
- [ ] #1 npm project initialized with package.json
- [ ] #2 Vite dev server runs and serves index.html
- [ ] #3 Tailwind CSS compiles correctly
- [ ] #4 Basecoat classes available
- [ ] #5 AlpineJS initializes without errors
- [ ] #6 Hot reload works during development
<!-- AC:END -->
