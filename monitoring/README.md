# Prometheus + Grafana + Alertmanager

This folder contains a minimal working configuration to run a monitoring stack for the PoC.

Usage

1. Start the monitoring stack (from repo root):
   docker compose up -d prometheus grafana alertmanager

2. Open Grafana: http://localhost:3000 (login: admin / admin)
   The dashboard "ZeroCaffeine Studio PoC" will be provisioned automatically.

3. Prometheus will scrape the API metrics exposed at http://host.docker.internal:8000/metrics
   and the worker metrics at host.docker.internal:9125. On Linux you may need to adjust
   host.docker.internal to point to the host or update prometheus.yml accordingly.

4. Configure Alertmanager notifications by setting SLACK_WEBHOOK_URL in your environment
   (or edit monitoring/alertmanager/config.yml to provide SMTP credentials for email).
