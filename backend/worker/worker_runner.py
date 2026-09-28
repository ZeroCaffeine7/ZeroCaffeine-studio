#!/usr/bin/env python3
"""Worker runner for PoC using Redis-backed queues and real LLM calls.

Now calls the model_adapter to generate task output instead of simulating.
Set OPENAI_API_KEY in the environment to enable OpenAI usage.
"""
import argparse
import time
import random
import threading
import requests
import os
import sys

API = os.environ.get('POC_API_URL', 'http://localhost:8000')

from backend.services import queue_service
from backend.services import model_adapter


def process_loop(worker_id: str, role: str, stop_event: threading.Event, tier: str):
    session = requests.Session()
    while not stop_event.is_set():
        try:
            task_id = queue_service.pop_task(role, timeout=5)
            if not task_id:
                time.sleep(0.5)
                continue

            print(f"[{worker_id}] popped task {task_id}")

            # Claim the task via API
            try:
                resp = session.post(f"{API}/tasks/{task_id}/claim", json={"worker_id": worker_id}, timeout=10)
                if resp.status_code != 200:
                    print(f"[{worker_id}] failed to claim {task_id}: {resp.status_code} {resp.text}")
                    continue
            except Exception as e:
                print(f"[{worker_id}] error claiming {task_id}: {e}")
                continue

            # Fetch task details
            try:
                rtask = session.get(f"{API}/tasks/{task_id}", timeout=10)
                if rtask.status_code != 200:
                    print(f"[{worker_id}] failed to fetch task {task_id}: {rtask.status_code}")
                    continue
                task = rtask.json()
            except Exception as e:
                print(f"[{worker_id}] error fetching task {task_id}: {e}")
                continue

            # Call the model adapter to generate output
            try:
                result_text = model_adapter.generate_for_task(task, tier=tier)
            except Exception as e:
                print(f"[{worker_id}] model call failed for {task_id}: {e}")
                # mark task as failed or requeue; for PoC we'll set status back to 'new'
                # optionally could push back to queue
                continue

            # Submit result
            try:
                r = session.post(f"{API}/tasks/{task_id}/result", json={"worker_name": worker_id, "result_text": result_text}, timeout=20)
                if r.status_code == 200:
                    print(f"[{worker_id}] submitted result for {task_id}")
                else:
                    print(f"[{worker_id}] failed to submit result {task_id}: {r.status_code} {r.text}")
            except Exception as e:
                print(f"[{worker_id}] error submitting result {task_id}: {e}")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[{worker_id}] unexpected error: {e}")
            time.sleep(1)


def spawn_workers(worker_id_prefix: str, role: str, count: int, tier: str):
    threads = []
    stop_event = threading.Event()
    for i in range(count):
        wid = f"{worker_id_prefix}-{i+1}"
        t = threading.Thread(target=process_loop, args=(wid, role, stop_event, tier), daemon=True)
        t.start()
        threads.append(t)
        print(f"spawned worker thread {wid} for role {role} (tier={tier})")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping workers...")
        stop_event.set()
        for t in threads:
            t.join()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--worker-id', type=str, default='worker', help='worker id prefix')
    parser.add_argument('--role', type=str, required=True, help='role name to listen on (e.g., level_design)')
    parser.add_argument('--concurrency', type=int, default=1, help='number of worker threads to spawn')
    parser.add_argument('--tier', type=str, default='draft', choices=['draft','synthesis','review'], help='model tier to use')
    args = parser.parse_args()

    spawn_workers(args.worker_id, args.role, args.concurrency, args.tier)


if __name__ == '__main__':
    main()
