import os
import redis

REDIS_URL = os.environ.get('POC_REDIS_URL', 'redis://localhost:6379/0')

_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)


def push_task(task_id: str, role: str) -> None:
    """Push a task id onto the role-specific queue (left push)."""
    key = f"queue:{role}"
    _client.lpush(key, task_id)


def pop_task(role: str, timeout: int = 5):
    """Blocking pop from the role-specific queue. Returns task_id or None."""
    key = f"queue:{role}"
    res = _client.brpop(key, timeout=timeout)
    if res:
        return res[1]
    return None


def queue_length(role: str) -> int:
    return _client.llen(f"queue:{role}")


def list_queues(prefix: str = 'queue:'):
    return _client.keys(f"{prefix}*")


# Retry tracking for tasks
def increment_retry(task_id: str) -> int:
    key = f"retries:{task_id}"
    return _client.incr(key)


def get_retry(task_id: str) -> int:
    key = f"retries:{task_id}"
    val = _client.get(key)
    return int(val) if val else 0


def reset_retry(task_id: str) -> None:
    key = f"retries:{task_id}"
    _client.delete(key)
