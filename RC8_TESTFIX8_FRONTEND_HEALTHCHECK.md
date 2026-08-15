# RC8 TESTFIX8 — Frontend healthcheck interpolation fix

## Root cause
The previous frontend healthcheck resolved the container IP through `$HOSTNAME` and embedded an `awk "...$1..."` expression. Docker Compose variable interpolation and shell expansion could corrupt the command, producing either:

- `wget: bad address ':3000'`
- `wget: bad address '172.18.0.5 <container-id>:3000'`

This is a healthcheck-only failure: the Next.js process itself is listening on the container network address and the application is reachable by IP.

## Fix
The healthcheck now reads the container hostname from `/etc/hostname` and uses a single-quoted awk program, while escaping Compose variables with `$$`:

`HOST_IP=$(getent hosts "$(cat /etc/hostname)" | awk 'NR==1 {print $1}')`

The rest of the check remains `/login` over port 3000.

## Expected result
After `docker compose up -d --build`, frontend should transition to `healthy` and `docker inspect ... .State.Health` should show exit code `0`.
