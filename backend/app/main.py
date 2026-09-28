from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Gauge
from fastapi.responses import Response
@@
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from prometheus_client import Gauge as PromGauge
# Gauge for queue lengths per role
QUEUE_GAUGE = PromGauge('zc_queue_length', 'Queue length per role', ['role'])

@@
@app.get("/metrics")
def metrics():
    # Update queue length gauges before returning metrics
    from backend.services import queue_service
    # set gauge per role
    try:
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
    except Exception:
        # be resilient if redis not available
        pass
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
