# Operations Runbook

## Paths and services

- Repo path (Oracle): `/home/ubuntu/servicios/atlas-smart-diagnostics`
- Compose file: `docker-compose.prod.yml`
- Containers:
  - `atlasdiag-web`
  - `atlasdiag-api`

## Daily checks

```bash
cd /home/ubuntu/servicios/atlas-smart-diagnostics
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.RunningFor}}"
curl -s https://diagnostico.atlaspcsupport.com/health
```

## Logs

```bash
docker logs atlasdiag-web --tail 200
docker logs atlasdiag-api --tail 200
```

Follow logs live:

```bash
docker logs -f atlasdiag-api
```

## Restart

Safe restart:

```bash
cd /home/ubuntu/servicios/atlas-smart-diagnostics
docker-compose -f docker-compose.prod.yml restart
```

Rebuild after code updates:

```bash
cd /home/ubuntu/servicios/atlas-smart-diagnostics
git pull
docker-compose -f docker-compose.prod.yml up -d --build
```

## Rollback (git-based)

1. Find previous commit:

```bash
git log --oneline -n 20
```

2. Checkout known good commit (detached):

```bash
git checkout <good_commit_sha>
docker-compose -f docker-compose.prod.yml up -d --build
```

3. Once stable, create a rollback branch from that commit:

```bash
git switch -c rollback/<date>
```

## Backup reminders

- Keep backup of `backend/.env` outside repo.
- Take periodic VM snapshots before major deployment changes.
- Export WordPress DB separately (app is independent, but ecosystem is shared).

## Incident quick triage

1. Domain down:
   - Validate DNS record.
   - Check NPM proxy host and SSL.
2. Homepage works but diagnose fails:
   - Check `atlasdiag-api` logs.
   - Confirm provider key and model in `backend/.env`.
3. Slow response:
   - Verify VM CPU/RAM pressure (`top`, `htop`).
   - Check external provider latency/errors.
