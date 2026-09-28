# Frontend containerization notes

The frontend is now containerized and included in docker-compose as the `frontend` service.
It is built from ./frontend/Dockerfile and served by nginx on container port 80, mapped to
host port 8080 by default.

How to run the full stack

1. Ensure you have a `.env` file with GF_SECURITY_ADMIN_PASSWORD at repo root (see .env.example).
   cp .env.example .env
   # edit .env and set GF_SECURITY_ADMIN_PASSWORD

2. Start all services (API, worker, DB, Redis, monitoring, frontend):
   docker compose up -d

3. Initialize the database (first run):
   docker compose exec api python scripts/init_db.py

4. Verify services:
   docker compose ps

5. Access interfaces:
   - Frontend: http://localhost:8080
   - API: http://localhost:8000
   - Grafana: http://localhost:3000
   - Prometheus: http://localhost:9090

Troubleshooting

- If the frontend build fails because the ./frontend directory is missing or has unexpected files,
  ensure your repo contains the compiled frontend artifacts (index.html, static assets) in ./frontend.
  If your current workflow serves frontend from host (start_demo.sh), copy the served files into ./frontend
  before building the container.

- If you prefer the frontend to be served on a different port, update the ports mapping in docker-compose.yml.
