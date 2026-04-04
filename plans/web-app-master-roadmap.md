# Bambam Web App Master Roadmap

This roadmap covers the remaining work after the current completed milestone set for the self-hosted web migration.

## Current baseline already completed

- Dockerized `[frontend/](../frontend)` + `[backend/](../backend)` + worker + Redis stack
- Async image conversion
- Async audio conversion
- Async video conversion
- Async document conversion with LibreOffice headless
- Job history dashboard
- Cleanup endpoint and stale job cleanup baseline
- Batch upload plus zip export for image and audio
- Updated `[README.md](../README.md)` and initial smoke/test assets

## Remaining work tracks

## Track 1: Production hardening

### Queue and worker reliability

- Add explicit retry policy per job type in `[backend/app/worker.py](../backend/app/worker.py:1)`
- Differentiate timeouts for image, audio, video, and document jobs
- Add worker-side structured logging for start, finish, fail, and cleanup events
- Store queue job ids on internal jobs for traceability
- Add dead-letter or failure inspection strategy

### API and upload hardening

- Add file type and mime validation before persistence
- Add upload file size limits per module
- Reject unsupported or malformed uploads early
- Add safer validation for resize and format parameters on video routes
- Add better admin cleanup safety rules and dry-run capability

### Cleanup and retention

- Move cleanup logic to periodic scheduled task or startup-safe maintenance pass
- Separate retention rules for uploads, outputs, bundles, and failed jobs
- Clean empty job output directories recursively
- Keep final bundles for configurable duration

### Environment and deployment polish

- Add real `.env` usage docs for `[backend/.env.example](../backend/.env.example)` and `[frontend/.env.example](../frontend/.env.example)`
- Add Docker healthchecks in `[docker-compose.yml](../docker-compose.yml)`
- Improve `[backend/Dockerfile](../backend/Dockerfile)` and `[frontend/Dockerfile](../frontend/Dockerfile)` with production-minded optimizations
- Add optional reverse proxy example for local network exposure

## Track 2: Feature parity and missing product behavior

### Batch parity expansion

- Add batch and zip export for video jobs
- Add batch and zip export for document jobs
- Consider grouped mixed-result handling and manifest generation

### Image parity

- Add resize modes similar to `[ImageTab](../image_tab.py:29)`
- Add better quality/preset UX
- Add result manifest and per-file result visibility in batch jobs

### Audio parity

- Add sample rate and channel options inspired by `[SoundTab](../sound_tab.py:31)`
- Add better batch job summaries and per-file error reporting

### Video parity

- Add codec and preset selection
- Add better progress parsing from FFmpeg output
- Add source metadata preview
- Revisit trim/crop support for web UX in a safe later phase

### Document parity

- Expand supported document type validation
- Add explicit engine status surface in the UI
- Add per-format limitation messaging

### Settings and access control

- Add lightweight settings screen in `[frontend/](../frontend)`
- Add optional basic auth or local access gate
- Add configurable retention and upload size options

## Track 3: UX and frontend productization

### Navigation and layout

- Replace the current landing-page stacking approach in `[frontend/app/page.tsx](../frontend/app/page.tsx:1)` with a clearer app shell
- Add sidebar or top navigation
- Split modules into dedicated routes

### Job dashboard improvements

- Add filtering by type and status
- Add search by filename or job id
- Add expandable job detail rows
- Add retry and cleanup actions from UI
- Add better failed-job diagnostics display

### Converter UX improvements

- Add per-file progress and per-batch summaries
- Add drag-drop areas
- Add better success/error notifications
- Add disable states and validation messages for every form
- Improve mobile layout and spacing consistency

## Track 4: Testing and validation

### Backend tests

- Expand beyond `[backend/tests/test_health.py](../backend/tests/test_health.py:1)`
- Add route tests for image, audio, video, document, batch, jobs, and admin cleanup
- Add service-level tests for conversion command builders and storage helpers
- Add cleanup service tests

### Integration tests

- Add docker-based smoke tests for queue lifecycle
- Add one happy-path integration test per converter type
- Add batch zip verification tests for image and audio

### Frontend validation

- Add component or e2e coverage for converter forms and dashboard behavior
- Test polling, error states, and download link rendering

## Track 5: Release readiness

### Documentation

- Expand `[README.md](../README.md)` with clearer web-first installation and troubleshooting
- Add architecture notes linking to `[plans/web-app-migration-plan.md](../plans/web-app-migration-plan.md)`
- Add module support matrix showing single vs batch availability

### Operational readiness

- Add startup checklist and smoke verification notes
- Add backup/restore guidance for `[data/db](../data/db)` and outputs
- Add storage growth guidance for local self-hosted use

## Recommended implementation order

### Phase A

- production hardening for queue, validation, cleanup, and compose healthchecks

### Phase B

- frontend shell improvements and stronger dashboard UX

### Phase C

- batch parity for video and document

### Phase D

- module parity enhancements for image, audio, and video advanced controls

### Phase E

- tests, documentation expansion, and release checklist

## Suggested next coding target

Start with **Track 1: Production hardening**, because it improves all already-built modules at once and reduces rework before deeper feature parity efforts.
