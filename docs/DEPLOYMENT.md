# Deployment Guide

## Production topology (current)

```text
diagnostico.atlaspcsupport.com
  ├─ /            -> React frontend (atlasdiag-web)
  ├─ /api/*       -> FastAPI backend (atlasdiag-api)
  └─ /health      -> FastAPI health endpoint
```

This setup intentionally uses a single public domain to simplify CORS and avoid cross-subdomain issues.

## Prerequisites

- Oracle VM with Docker and Docker Compose installed.
- Nginx Proxy Manager (NPM) running on the same Docker network used by app containers.
- DNS A record:
  - `diagnostico.atlaspcsupport.com -> 129.146.121.2`
- External Docker network available (expected name: `web_traffic`).

Create network once if needed:

```bash
docker network create web_traffic
```

## 1) Clone and configure

```bash
cd /home/ubuntu/servicios
git clone https://github.com/mikepchelper-spec/atlas-smart-diagnostics.git
cd atlas-smart-diagnostics
```

Create backend env:

```bash
cp backend/.env.example backend/.env
```

Set at least:

- `AI_PROVIDER`
- `AI_API_KEY`
- `AI_MODEL`
- `ALLOWED_ORIGINS=https://diagnostico.atlaspcsupport.com,https://atlaspcsupport.com`
- `ATLAS_WHATSAPP_NUMBER=<number_without_plus>`

Optional root `.env` (for frontend build args):

```bash
cat > .env <<'EOF'
VITE_API_BASE_URL=https://diagnostico.atlaspcsupport.com
VITE_ATLAS_WHATSAPP_NUMBER=51999999999
EOF
```

## 2) Build and run

```bash
docker-compose -f docker-compose.prod.yml up -d --build
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

Expected containers:

- `atlasdiag-web`
- `atlasdiag-api`

## 3) Configure Nginx Proxy Manager

Create or edit proxy host:

- **Domain Names**: `diagnostico.atlaspcsupport.com`
- **Scheme**: `http`
- **Forward Hostname/IP**: `atlasdiag-web`
- **Forward Port**: `80`
- **Block Common Exploits**: ON
- **Websockets Support**: ON

SSL tab:

- Request or select Let's Encrypt certificate.
- Enable `Force SSL`.
- Enable `HTTP/2`.

Important: no custom redirect from `/` should be present for this host.

## 4) Validation checks

```bash
curl -I https://diagnostico.atlaspcsupport.com
curl -s https://diagnostico.atlaspcsupport.com/health
curl -s -X POST https://diagnostico.atlaspcsupport.com/api/diagnose \
  -F "os=windows-11" \
  -F "error_text=Blue screen after update"
```

Expected:

- Homepage responds `200`.
- `/health` returns JSON with `status: ok`.
- `/api/diagnose` returns structured diagnosis JSON.

## WordPress embed snippet

Use in Elementor HTML widget on `atlaspcsupport.com`:

```html
<iframe
  src="https://diagnostico.atlaspcsupport.com"
  title="Diagnóstico IA Atlas"
  loading="lazy"
  style="width:100%;min-height:1200px;border:0;border-radius:24px;overflow:hidden;"
></iframe>
```

## Troubleshooting

### `DNS_PROBE_FINISHED_NXDOMAIN`

- DNS record missing or not propagated.
- Verify A record for `diagnostico` points to VM public IP.

### Cloudflare `525 SSL handshake failed`

- NPM cert missing/invalid.
- Re-issue certificate in NPM and ensure proxy host points to live container.

### `502 Bad Gateway` in NPM

- Target container not running, or wrong target host/port.
- Check:
  - `docker ps`
  - NPM target should be `atlasdiag-web:80`.

### Frontend loads, but API fails

- Verify `atlasdiag-api` is running.
- Check reverse proxy rules in `frontend/Dockerfile.prod`.
- Check backend logs:
  - `docker logs atlasdiag-api --tail 200`

### CORS errors in browser console

- Add real origin(s) to `ALLOWED_ORIGINS` in `backend/.env`.
- Restart services after changing env.

## Launch checklist

- `atlaspcsupport.com` remains unaffected.
- `diagnostico` homepage works over HTTPS.
- `/health` and `/api/diagnose` pass.
- Real provider key loaded server-side only.
- Rate limit and upload limits tested.
- Privacy disclaimer and handoff message verified.
