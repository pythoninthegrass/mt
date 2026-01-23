# Baseline Metrics: Hybrid Architecture

**Date**: 2025-01-23
**State**: Hybrid (Rust + Python PEX sidecar)

## Build Metrics

| Metric | Value |
|--------|-------|
| Build time (task tauri:build) | 2m 4.5s |
| App bundle size | 34 MB |
| DMG size | 27 MB |
| Sidecar (PEX) size | 23 MB |

## Code Metrics

| Metric | Value |
|--------|-------|
| Python backend lines | 4,113 |
| Python backend directory size | 464 KB |

## Notes

- Build includes PEX sidecar packaging step
- Sidecar is bundled but **unused** (all 87 Tauri commands in Rust)
- This is the baseline before completing migration to pure Rust
