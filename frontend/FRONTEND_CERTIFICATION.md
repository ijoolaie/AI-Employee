# Frontend RC8 Certification

The backend API container intentionally does not contain `npm`. Frontend validation is performed by the dedicated `frontend` Compose service using Node 22.

## Commands

```powershell
docker compose up -d --build frontend

docker compose ps

docker compose logs frontend --tail=100
```

The frontend image runs the repository's `npm run test` contract suite and `npm run build` during image construction, then serves the Next.js standalone build on port 3000.

## Local smoke

Open `http://localhost:3000/login` and verify the login page renders. The backend API remains at `http://localhost:8000`.
