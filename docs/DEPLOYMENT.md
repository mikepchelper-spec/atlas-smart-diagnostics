# Deployment guide

## Recommended production layout

```text
diagnostico.atlaspcsupport.com        -> static frontend
diagnostico-api.atlaspcsupport.com    -> FastAPI backend
atlaspcsupport.com/autoservicio       -> WordPress page embedding frontend iframe
```

## Backend on Oracle + Nginx Proxy Manager

1. Clone repo on Oracle.
2. Create `backend/.env` from `.env.example`.
3. Set real variables:
   - `AI_PROVIDER`
   - `AI_API_KEY`
   - `AI_MODEL`
   - `ALLOWED_ORIGINS=https://atlaspcsupport.com,https://diagnostico.atlaspcsupport.com`
   - `ATLAS_WHATSAPP_NUMBER`
   - `METRICS_ADMIN_KEY` (optional, only if you want private aggregate metrics)
4. Run with Docker or systemd/uvicorn.
5. Add NPM Proxy Host for `diagnostico-api.atlaspcsupport.com`.
6. Enable HTTPS, Force SSL, HTTP/2.

## Frontend static hosting

```bash
cd frontend
npm ci
VITE_API_BASE_URL=https://diagnostico-api.atlaspcsupport.com \
VITE_ATLAS_WHATSAPP_NUMBER=51999999999 \
npm run build
```

Upload `frontend/dist/` to your static host or serve it with NPM.

## WordPress Elementor embed

Use an HTML widget:

```html
<iframe
  src="https://diagnostico.atlaspcsupport.com"
  title="Diagnóstico IA Atlas"
  loading="lazy"
  style="width:100%;min-height:1200px;border:0;border-radius:24px;overflow:hidden;"
></iframe>
```

Recommended WordPress page setup:

- Page/menu label: **Diagnóstico IA** or **Auto‑Diagnóstico PC**.
- Add a short intro above the iframe: “Orientación inicial, no reemplaza soporte profesional.”
- Add privacy/disclaimer link below the iframe.
- Keep API CORS limited to `https://atlaspcsupport.com` and `https://diagnostico.atlaspcsupport.com`.
- Do not put AI keys, metrics keys, or backend secrets in Elementor.

## Private metrics check

If `METRICS_ADMIN_KEY` is set:

```bash
curl -H "X-Atlas-Metrics-Key: $METRICS_ADMIN_KEY" \
  https://diagnostico-api.atlaspcsupport.com/api/metrics
```

Expected anonymous shape:

```json
{
  "events": {"diagnosis": 10, "whatsapp_click": 3},
  "operating_systems": {"windows_11": 7},
  "categories": {"network": 4},
  "difficulties": {"basic": 5},
  "locales": {"es": 9, "en": 1}
}
```

No raw issue text, images, IPs, phone numbers, names, or emails are stored by the MVP metrics layer.

## Knowledge base upkeep

Runbook hints live in `backend/app/knowledge_base.py`. Add or adjust entries when Atlas creates new support workflows. Keep entries short, safe, and non-secret; they are used as model context and may be reflected in diagnostic output.

## Launch checklist

- Backend `/health` returns `ok`.
- CORS allows only expected domains.
- Upload limit works.
- Rate limit works.
- WhatsApp number is correct.
- A test diagnosis returns an `ATLAS-CASE-XXXXXX` case ID.
- WhatsApp CTA includes case ID and structured summary.
- Metrics endpoint returns 404 without the private key.
- Real AI provider tested with one Windows and one data-risk case.
- WordPress page has disclaimer and privacy link.
- Cloudflare WAF/rate limit added if public traffic grows.
