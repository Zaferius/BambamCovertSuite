# Operations Checklist for Bambam Web App

## Pre-deployment checklist

- Review `[backend/.env.example](../backend/.env.example)` and create environment values appropriate for the host
- Confirm Docker and Docker Compose are installed
- Ensure sufficient free disk space for uploads, outputs, and bundle archives
- Confirm LibreOffice and FFmpeg are available through the configured Docker images

## Startup checklist

1. Run `[docker-compose.yml](../docker-compose.yml)` with:
   - `docker compose up --build`
2. Verify health:
   - frontend responds on `http://localhost:3000`
   - API responds on `http://localhost:8000/health`
   - Redis healthcheck is passing
3. Run smoke checks:
   - `[scripts/smoke-test.ps1](../scripts/smoke-test.ps1:1)`
   - `[scripts/queue-smoke-test.ps1](../scripts/queue-smoke-test.ps1:1)`

## Routine operations checklist

- Review job history from `[frontend/app/components/jobs-dashboard.tsx](../frontend/app/components/jobs-dashboard.tsx:18)`
- Run cleanup periodically using `POST /admin/cleanup`
- Monitor growth of:
  - `[data/uploads](../data/uploads)`
  - `[data/outputs](../data/outputs)`
  - `[data/db](../data/db)`
  - `[data/temp](../data/temp)`

## Failure response checklist

- If conversions fail repeatedly, inspect API and worker container logs
- Verify Redis is healthy
- Verify output disk is not full
- Verify uploaded file type and size match current policy
- For document failures, verify LibreOffice behavior inside the container
