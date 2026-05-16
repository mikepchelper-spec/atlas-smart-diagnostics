# Product spec — Atlas Smart Diagnostics

## Recommended public naming

- Menu label: **Diagnóstico IA**
- Page title: **Asistente de Diagnóstico Atlas**
- Internal/repo name: `atlas-smart-diagnostics`

## User journey

1. Visitor opens the self-service page.
2. Selects OS:
   - Windows 11
   - Windows 10
   - macOS
   - Ubuntu, Debian, Fedora, Linux Mint, Arch, other Linux
3. Pastes the exact error text or describes symptoms.
4. Optionally uploads a screenshot/photo.
5. Accepts safety disclaimer.
6. Receives structured triage.
7. If risk is medium/high, clicks WhatsApp with a prefilled summary.
8. Atlas receives a case ID and structured handoff instead of an unstructured “my PC fails” message.

## Diagnosis structure

1. Summary.
2. Likely causes with confidence.
3. Difficulty for a basic user.
4. Self-service probability.
5. Risk notice.
6. Before-touching checklist.
7. Safe first steps.
8. Stop-and-contact triggers.
9. WhatsApp handoff.
10. Disclaimer.
11. Related Atlas runbook hints, when matched.

## Conversion strategy

The tool should give real value without replacing paid support. It should solve simple cases, but it should clearly escalate when:

- data can be lost,
- user skill required is advanced,
- diagnosis needs logs/hardware checks,
- remote support would be safer than trial-and-error.

## Future-proofing backlog

- Persistent metrics storage or dashboard if public traffic validates the funnel.
- Admin dashboard with top issue categories.
- Google Business Profile review prompt after successful self-service.
- CAPTCHA/Turnstile if abuse starts.
- PDF export of diagnostic result.
- Integration with Atlas PC Support panel reports.
- Vector/CMS-backed knowledge retrieval for larger Atlas runbooks.

## Upscale features included in MVP PR

- ES/EN toggle in the frontend.
- Server-side case IDs in `ATLAS-CASE-XXXXXX` format.
- Structured WhatsApp prefill with case context.
- Anonymous aggregate metrics.
- Local Atlas knowledge matcher for Printer Doctor, GPU triage, AI Readiness, RustDesk, and backup-first cases.
