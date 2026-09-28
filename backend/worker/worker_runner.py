#!/usr/bin/env python3
"""Worker runner for PoC using Redis-backed queues.

This simple worker pops task IDs from a role queue and then calls the API
endpoints to claim, simulate work, and submit a result. Run many instances
to simulate scale, or use the --concurrency switch to spawn multiple
processes/threads within one container.

Example:
  python backend/worker/worker_runner.py --worker-id level_worker_1 --role level_design --concurrency 4

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


def process_loop(worker_id: str, role: str, stop_event: threading.Event):
    session = requests.Session()
    while not stop_event.is_set():
        try:
            task_id = queue_service.pop_task(role, timeout=5)
            if not task_id:
                # idle sleep
                time.sleep(0.5)
                continue

            print(f"[{worker_id}] popped task {task_id}")

            # Claim the task via API
            try:
                resp = session.post(f"{API}/tasks/{task_id}/claim", json={"worker_id": worker_id}, timeout=10)
                if resp.status_code != 200:
                    print(f"[{worker_id}] failed to claim {task_id}: {resp.status_code} {resp.text}")
                    # continue to next
                    continue
            except Exception as e:
                print(f"[{worker_id}] error claiming {task_id}: {e}")
                continue

            # Simulate work (replace with real model call)
            work_time = random.uniform(0.5, 2.0)
            time.sleep(work_time)

            result_text = f"Auto-result by {worker_id} for {task_id} (simulated work {work_time:.2f}s)"

            # Submit result
            try:
                r = session.post(f"{API}/tasks/{task_id}/result", json={"worker_name": worker_id, "result_text": result_text}, timeout=10)
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


def spawn_workers(worker_id_prefix: str, role: str, count: int):
    threads = []
    stop_event = threading.Event()
    for i in range(count):
        wid = f"{worker_id_prefix}-{i+1}"
        t = threading.Thread(target=process_loop, args=(wid, role, stop_event), daemon=True)
        t.start()
        threads.append(t)
        print(f"spawned worker thread {wid} for role {role}")
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
    args = parser.parse_args()

    spawn_workers(args.worker_id, args.role, args.concurrency)


if __name__ == '__main__':
    main()
