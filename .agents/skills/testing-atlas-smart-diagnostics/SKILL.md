---
name: testing-atlas-smart-diagnostics
description: Test Atlas Smart Diagnostics end-to-end locally. Use when verifying diagnosis UI, case IDs, WhatsApp handoff, bilingual UI, Atlas runbook matching, or anonymous metrics.
---

# Testing Atlas Smart Diagnostics

## Devin Secrets Needed

- `AI_API_KEY` — optional; only needed when testing a real OpenAI/Groq/OpenAI-compatible provider instead of the mock provider.
- `METRICS_ADMIN_KEY` — optional for production/staging metrics access. For local testing, set a throwaway value in the shell, e.g. `METRICS_ADMIN_KEY=test-metrics-key`.

## Local mock E2E setup

1. Start the backend from repo root:
   ```bash
   cd backend
   METRICS_ADMIN_KEY=test-metrics-key ../.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```
2. Start the frontend from repo root in another shell:
   ```bash
   cd frontend
   VITE_API_BASE_URL=http://localhost:8000 npm run dev -- --host 127.0.0.1 --port 5173
   ```
3. Open `http://localhost:5173` in Chrome. The backend CORS default allows this local frontend origin.

## Core browser assertions

Use the UI rather than backend-only requests for the main flow.

1. Verify the default Spanish hero appears, then click `EN`.
   - The heading should become `AI Diagnostic Assistant`.
   - The submit button should become `Generate safe diagnosis`.
2. Keep OS as `Windows 11` and submit a printer/spooler issue, for example:
   ```text
   My printer is stuck in the print queue, the spooler keeps stopping, and nothing prints.
   ```
3. Confirm the result shows:
   - A case ID matching `ATLAS-CASE-[A-Z0-9]{6}`.
   - Difficulty/probability labels appropriate to the issue.
   - `Provider` as `mock` when using the mock backend.
   - `Atlas Printer Doctor` under related runbooks for printer/spooler wording.
4. Click the WhatsApp CTA and verify the prefilled message contains structured context:
   - Case ID
   - OS
   - Difficulty
   - Self-service probability
   - Likely cause
   - Suggested safe steps
   - Original problem text

## Metrics verification

After submitting a diagnosis and clicking WhatsApp, query:

```bash
curl -s -H 'X-Atlas-Metrics-Key: test-metrics-key' http://127.0.0.1:8000/api/metrics | python -m json.tool
```

Expected aggregate fields include counts for:

- `events.diagnosis`
- `events.whatsapp_click`
- selected OS such as `operating_systems.windows_11`
- issue category such as `categories.printer`
- difficulty such as `difficulties.intermediate`
- locale such as `locales.en`

The metrics response should stay aggregate-only and should not contain raw issue text or uploaded image content.

## Production/staging notes

- For real provider testing, configure `AI_PROVIDER` and `AI_API_KEY` before starting the backend.
- For WordPress iframe testing, verify CORS allows only the intended Atlas domains and test on mobile width.
- Do not complete an actual WhatsApp message send unless the user explicitly asks; verifying the generated prefill is usually enough.
