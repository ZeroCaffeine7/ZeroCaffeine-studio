# Model integration notes

This file documents how to enable real LLM calls for workers in the PoC.

1) OpenAI
- Set OPENAI_API_KEY in your environment. Example:
  export OPENAI_API_KEY="sk-..."

- The model_adapter will default to gpt-3.5-turbo for draft tier and gpt-4 for synthesis/review if available. If you don't have access to gpt-4, override via env:
  export SYNTHESIS_MODEL=gpt-3.5-turbo
  export REVIEW_MODEL=gpt-3.5-turbo

2) Local model
- If you run a local inference endpoint, set LOCAL_MODEL_URL to the URL that accepts POST {"prompt": "..."} and returns JSON {"text": "..."}.

3) Running workers with model calls
- Start API and Redis and initialize DB (docs/db_run.md)
- Start API + frontend (start_demo.sh)
- Start workers that call real models:
  python backend/worker/worker_runner.py --worker-id level_ai --role level_design --concurrency 2 --tier synthesis

Notes & cautions
- Real model calls incur costs and latency. Be conservative with concurrency and batch size when you have a billing-sensitive account.
- Add retry/backoff and error handling when integrating in production.
- For high throughput, consider a separate inference service with batching (vLLM, Triton, Ray Serve, or cloud endpoints).
