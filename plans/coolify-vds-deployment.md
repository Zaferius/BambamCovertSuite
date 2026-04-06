# Coolify + Ubuntu VDS Deployment (IP-First)

This guide is for deploying the web stack on your own Ubuntu VDS using Coolify, starting with direct IP access (no domain required).

## 1) What You Deploy

The stack is defined in [docker-compose.yml](../docker-compose.yml):

- `frontend` (Next.js)
- `api` (FastAPI)
- `worker` (RQ worker)
- `redis` (queue backend)

Persistent app data is stored under:

- [data/uploads](../data/uploads)
- [data/outputs](../data/outputs)
- [data/db](../data/db)
- [data/temp](../data/temp)

## 2) Prepare Environment Values

Use these templates as reference:

- [backend/.env.production.example](../backend/.env.production.example)
- [frontend/.env.production.example](../frontend/.env.production.example)

For IP-only rollout, set:

- backend `CORS_ORIGINS=["http://YOUR_VDS_IP:3000"]`
- frontend `NEXT_PUBLIC_API_BASE_URL=http://YOUR_VDS_IP:8000`

## 3) Create a New Coolify Resource

1. In Coolify, create a **New Resource** from your Git repository.
2. Select **Docker Compose** deployment type.
3. Point to [docker-compose.yml](../docker-compose.yml).
4. Ensure deployment path is repository root.

## 4) Configure Ports (IP Access)

Open these ports on your VDS firewall/security group:

- `3000/tcp` (frontend)
- `8000/tcp` (api)
- `22/tcp` (ssh)

Keep `6379` private (do not expose Redis publicly).

## 5) Set Environment Variables in Coolify

Set variables per service in Coolify UI:

### `api` and `worker`

- `APP_ENV=production`
- `CORS_ORIGINS=["http://YOUR_VDS_IP:3000"]`
- `REDIS_URL=redis://redis:6379/0`
- Optional tuning:
  - `MAX_UPLOAD_SIZE_MB`
  - `QUEUE_DEFAULT_TIMEOUT`
  - `QUEUE_VIDEO_TIMEOUT`
  - `QUEUE_DOCUMENT_TIMEOUT`

### `frontend`

- `NEXT_PUBLIC_API_BASE_URL=http://YOUR_VDS_IP:8000`

## 6) Deploy and Verify

After first deploy, verify:

- `http://YOUR_VDS_IP:3000` opens UI
- `http://YOUR_VDS_IP:8000/health` returns success
- conversion jobs complete and output downloads work

## 7) Operations

- Back up [data/db](../data/db) regularly.
- Run cleanup periodically with `POST /admin/cleanup`.
- Monitor growth of [data/uploads](../data/uploads) and [data/outputs](../data/outputs).

## 8) Later: Domain + HTTPS

When ready, move from IP to domain/reverse-proxy setup in Coolify and update:

- backend `CORS_ORIGINS`
- frontend `NEXT_PUBLIC_API_BASE_URL`

No application code change is required for that migration.
