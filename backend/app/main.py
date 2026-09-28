from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Gauge
from fastapi.responses import Response
@@
@app.get("/metrics")
def metrics():
    # Update queue length gauges before returning metrics
    from backend.services import queue_service
    # set gauge per role
    for q in queue_service.list_queues():
        # q is like 'queue:role'
        if not q.startswith('queue:'):
            continue
        role = q.split(':',1)[1]
        try:
            val = queue_service.queue_length(role)
        except Exception:
            val = 0
        QUEUE_GAUGE.labels(role=role).set(val)
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
