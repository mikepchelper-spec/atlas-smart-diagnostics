# Atlas Smart Diagnostics

AI-assisted self-service diagnostic triage for Atlas PC Support.

The project gives `atlaspcsupport.com` an embeddable **Diagnóstico IA** page where a visitor selects their operating system, pastes an error message, optionally uploads a screenshot, and receives a structured, safety-first diagnosis with a WhatsApp handoff.

## Product goal

This is not a “magic repair bot”. It is a lead-converting triage assistant:

1. Explain likely causes.
2. Classify difficulty for a basic user.
3. Warn when data loss or advanced repair risk exists.
4. Give safe, reversible first steps.
5. Escalate risky cases to Atlas PC Support with a prefilled WhatsApp message.

## MVP features

- Windows 10/11, macOS, common Linux distributions, and custom Linux distro input.
- Error text + optional JPG/PNG/WebP screenshot upload.
- Structured response:
  - likely causes with confidence,
  - difficulty: basic, intermediate, advanced, data risk,
  - self-service probability,
  - before-touching checklist,
  - safe steps,
  - stop-and-contact signals,
  - legal/safety disclaimer,
  - WhatsApp handoff text.
- Provider-agnostic AI backend:
  - `mock` rule-based fallback by default,
  - OpenAI-compatible endpoint support for OpenAI/Groq/etc.
- API keys stay server-side; WordPress/browser never receives them.
- Basic per-IP rate limiting.
- WordPress-friendly frontend build.

## Architecture

```text
WordPress page / iframe
        ↓
React/Vite frontend
        ↓ multipart form-data
FastAPI backend
        ↓
AI provider (optional) or safe rule-based fallback
        ↓
Structured JSON diagnosis
```

## Local development

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Health check:

```bash
curl http://localhost:8000/health
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Open `http://localhost:5173`.

## Environment variables

Backend:

| Variable | Default | Notes |
|---|---:|---|
| `AI_PROVIDER` | `mock` | `mock`, `openai`, `groq`, or any OpenAI-compatible provider name. |
| `AI_API_KEY` | empty | Required for real AI calls. If missing, safe fallback is used. |
| `AI_BASE_URL` | provider default | Optional OpenAI-compatible base URL. |
| `AI_MODEL` | provider default | Optional model override. |
| `ALLOWED_ORIGINS` | `http://localhost:5173` | Comma-separated CORS origins. Add `https://atlaspcsupport.com`. |
| `ATLAS_WHATSAPP_NUMBER` | placeholder | International format without `+`. |
| `MAX_UPLOAD_MB` | `8` | Server-side screenshot upload limit. |
| `RATE_LIMIT_PER_MINUTE` | `12` | Basic per-IP abuse protection. |

Frontend:

| Variable | Notes |
|---|---|
| `VITE_API_BASE_URL` | Backend base URL, e.g. `https://diagnostico.atlaspcsupport.com`. |
| `VITE_ATLAS_WHATSAPP_NUMBER` | WhatsApp number in international format without `+`. |

## WordPress embed options

### Option A — iframe, simplest

Deploy the frontend to a subdomain such as `https://diagnostico.atlaspcsupport.com` and embed it in Elementor:

```html
<iframe
  src="https://diagnostico.atlaspcsupport.com"
  title="Diagnóstico IA Atlas"
  loading="lazy"
  style="width:100%;min-height:1200px;border:0;border-radius:24px;overflow:hidden;"
></iframe>
```

### Option B — static build inside WordPress

Build the frontend and upload `frontend/dist/` to a static path served by NPM or WordPress uploads. Use an iframe pointing to that path.

Avoid placing API keys or provider credentials in WordPress.

## Safety policy

The assistant must not present risky actions as casual steps. It should escalate when the issue suggests:

- BitLocker/recovery key problems.
- Disk SMART warnings, clicking drives, missing partitions, boot failure.
- Ransomware/malware or encrypted files.
- Repeated blue screens or kernel panics.
- Commands such as `diskpart clean`, formatting, firmware flashing, registry edits, or OS reinstall.
- Important personal/business data without a verified backup.

## Deployment notes

- Backend can run on Fly.io, Render, Railway, or the Oracle VM behind Nginx Proxy Manager.
- Put the API behind HTTPS.
- Configure CORS to only allow your web origins.
- Start with `AI_PROVIDER=mock` for smoke tests, then enable a real provider.
- Add Cloudflare/WAF rate limits before public launch if traffic grows.

## Production (Oracle + NPM)

Current production setup uses one public domain:

- `https://diagnostico.atlaspcsupport.com` serves the React frontend.
- `https://diagnostico.atlaspcsupport.com/api` proxies to FastAPI.
- `https://diagnostico.atlaspcsupport.com/health` proxies to FastAPI health.

Production files included in this repo:

- `docker-compose.prod.yml`
- `frontend/Dockerfile.prod`

Quick start on Oracle VM:

```bash
cd /home/ubuntu/servicios/atlas-smart-diagnostics
cp backend/.env.example backend/.env
# edit backend/.env with real provider key + allowed origins
docker-compose -f docker-compose.prod.yml up -d --build
```

Nginx Proxy Manager target:

- Domain: `diagnostico.atlaspcsupport.com`
- Forward host: `atlasdiag-web`
- Forward port: `80`
- SSL: Let's Encrypt cert + Force SSL

For full production steps and troubleshooting, see `docs/DEPLOYMENT.md` and `docs/OPERATIONS.md`.

## Validation

```bash
npm --prefix frontend run lint
npm --prefix frontend run build
python -m ruff check backend/app backend/tests
python -m pytest backend/tests
```
