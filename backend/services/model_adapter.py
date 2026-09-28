"""Model adapter for PoC allowing calling OpenAI or a local inference endpoint.

Added robust retry/backoff logic to improve stability when calling remote
inference providers. Retries are configurable via environment variables.
"""
from __future__ import annotations

import os
import time
import requests
from typing import Optional

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
LOCAL_MODEL_URL = os.environ.get('LOCAL_MODEL_URL')

# Tier -> model mapping (adjust as you have access)
MODEL_TIERS = {
    'draft': os.environ.get('DRAFT_MODEL', 'gpt-3.5-turbo'),
    'synthesis': os.environ.get('SYNTHESIS_MODEL', 'gpt-4'),
    'review': os.environ.get('REVIEW_MODEL', 'gpt-4'),
}

# Retry configuration
MAX_RETRIES = int(os.environ.get('MODEL_MAX_RETRIES', '3'))
BACKOFF_BASE = float(os.environ.get('MODEL_BACKOFF_BASE', '1.0'))  # seconds
BACKOFF_MULTIPLIER = float(os.environ.get('MODEL_BACKOFF_MULTIPLIER', '2.0'))


def _call_openai_chat(messages, model: str = 'gpt-3.5-turbo', temperature: float = 0.7) -> str:
    if not OPENAI_API_KEY:
        raise RuntimeError('OPENAI_API_KEY not set')
    url = 'https://api.openai.com/v1/chat/completions'
    headers = {
        'Authorization': f'Bearer {OPENAI_API_KEY}',
        'Content-Type': 'application/json',
    }
    payload = {
        'model': model,
        'messages': messages,
        'temperature': temperature,
        'max_tokens': 1000,
    }
    r = requests.post(url, json=payload, headers=headers, timeout=60)
    r.raise_for_status()
    data = r.json()
    return data['choices'][0]['message']['content']


def _call_local_model(prompt: str) -> str:
    if not LOCAL_MODEL_URL:
        raise RuntimeError('LOCAL_MODEL_URL not set')
    r = requests.post(LOCAL_MODEL_URL, json={'prompt': prompt}, timeout=60)
    r.raise_for_status()
    data = r.json()
    return data.get('text') or data.get('result') or ''


def generate_text(prompt: str, tier: str = 'draft') -> str:
    """Generate text for a prompt using configured provider and tier.

    Retries on transient errors using exponential backoff. If all retries
    exhaust, an exception is raised to the caller.
    """
    model = MODEL_TIERS.get(tier, MODEL_TIERS['draft'])

    attempt = 0
    backoff = BACKOFF_BASE
    last_exc = None

    while attempt < MAX_RETRIES:
        try:
            # Prefer local model if configured
            if LOCAL_MODEL_URL:
                return _call_local_model(prompt)

            if OPENAI_API_KEY:
                messages = [
                    {"role": "system", "content": "You are a helpful level design assistant. Provide structured output when possible."},
                    {"role": "user", "content": prompt},
                ]
                return _call_openai_chat(messages, model=model, temperature=0.7)

            # Fallback deterministic behavior
            return f"[SIMULATED OUTPUT] Prompt was: {prompt[:200]}"

        except Exception as e:
            last_exc = e
            attempt += 1
            if attempt >= MAX_RETRIES:
                break
            # simple jitter
            sleep_time = backoff * (1 + 0.1 * (attempt % 3))
            time.sleep(sleep_time)
            backoff *= BACKOFF_MULTIPLIER
    # If we reach here, all attempts failed
    raise RuntimeError(f"Model generation failed after {MAX_RETRIES} attempts: {last_exc}")


def generate_for_task(task: dict, tier: str = 'draft') -> str:
    """Build a prompt from a task dict and call generate_text."""
    title = task.get('title')
    desc = task.get('description') or ''
    role = task.get('role_name') or task.get('role') or 'level_design'
    instructions = task.get('instructions') or ''

    prompt = (
        f"Task: {title}\nRole: {role}\nDescription: {desc}\nInstructions: {instructions}\n\n"
        "Please provide a structured output including:\n"
        "- layout_summary (short)\n- poi_list as JSON array with name/type/pos\n"
        "- connectors list (neighbor task ids or connector ids)\n"
        "- any asset_refs you recommend\n"
        "Return the answer in plain text; it's OK to include JSON fragments for structured fields."
    )
    return generate_text(prompt, tier=tier)
