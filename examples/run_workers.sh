#!/usr/bin/env bash
# Simple helper to start multiple worker runners in background for demo

ROLE=${1:-level_design}
COUNT=${2:-4}

for i in $(seq 1 $COUNT); do
  python3 backend/worker/worker_runner.py --worker-id ${ROLE}_auto --role ${ROLE} --concurrency 1 &
  sleep 0.2
done

echo "Started $COUNT worker processes for role $ROLE"
