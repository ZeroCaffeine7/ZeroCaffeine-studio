# Monitoring: updated notes for containerized services

After containerizing the API and worker, Prometheus now scrapes the internal
compose service names directly (api:8000, worker:9125). This avoids host
network issues like depending on host.docker.internal.

Usage (one-liner)

1. Ensure you have a `.env` file at repo root containing GF_SECURITY_ADMIN_PASSWORD and optional SLACK_WEBHOOK_URL.
   cp .env.example .env
   # edit .env and set a strong GF_SECURITY_ADMIN_PASSWORD value

2. Start all services including API and worker:

   docker compose up -d

3. Initialize DB (first run):

   docker compose exec api python scripts/init_db.py

4. Check services:

   docker compose ps

5. Access:
   - API: http://localhost:8000
   - Frontend: http://localhost:8080/index.html (if you run start_demo.sh locally or containerize frontend)
   - Prometheus: http://localhost:9090
   - Grafana: http://localhost:3000
   - Alertmanager: http://localhost:9093

Notes
- The api service is built from the repository Dockerfile and exposes port 8000.
- The worker service runs the PoC worker script and exposes metrics on port 9125.
- If you prefer to run multiple worker containers, consider adding a docker-compose scale configuration
  or switch to Docker Swarm / Kubernetes for orchestration.
