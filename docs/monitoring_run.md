# Monitoring: update docs

Added a Prometheus + Grafana + Alertmanager stack to docker-compose and provisioning files.

How to run

1. Start core infra + monitoring:
   docker compose up -d

2. Initialize DB (if not done):
   python scripts/init_db.py

3. Start API + front-end as before (start_demo.sh)

4. Start worker(s) with metrics enabled (they start a Prometheus metrics server on port 9125):
   python backend/worker/worker_runner.py --worker-id level_ai --role level_design --concurrency 1 --tier synthesis

5. Open Grafana at http://localhost:3000 (admin / admin) and view the "ZeroCaffeine Studio PoC" dashboard.
