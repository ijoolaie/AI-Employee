# RC8 Test Fix 9 — Frontend Healthcheck

## Root cause
The previous healthcheck depended on resolving the container hostname and parsing `getent hosts` output. On the reported Docker Desktop environment this produced an invalid host string such as `172.18.0.5 43f6b2b3cbb1 43f6b2b3cbb1:3000`.

## Fix
- Set `HOSTNAME=0.0.0.0` for the Next.js standalone runner.
- Use Node's built-in `fetch()` against `127.0.0.1:3000/login`.
- Remove dependency on container hostname, `getent`, `awk`, and `wget`.

## Expected verification
After rebuilding the stack, `docker compose ps` should show the frontend as `healthy`, and:

```powershell
docker inspect ai_employee_platform_rc8-frontend-1 --format '{{json .State.Health}}'
```

should report `Status` as `healthy`.
