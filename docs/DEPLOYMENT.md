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

## Launch checklist

- Backend `/health` returns `ok`.
- CORS allows only expected domains.
- Upload limit works.
- Rate limit works.
- WhatsApp number is correct.
- Real AI provider tested with one Windows and one data-risk case.
- WordPress page has disclaimer and privacy link.
- Cloudflare WAF/rate limit added if public traffic grows.
