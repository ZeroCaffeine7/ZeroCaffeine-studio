"""Model adapter for PoC allowing calling OpenAI or a local inference endpoint.

Environment variables:
- OPENAI_API_KEY: if present, use OpenAI Chat Completions endpoint
- LOCAL_MODEL_URL: if present, POST to this URL with {'prompt': ...} and expect {'text': ...}

Functionality:
- generate_text(prompt, tier): returns generated text
- generate_for_task(task): convenience wrapper that builds a prompt from task

This is intentionally minimal. For production, add retries, rate-limiting, batching, caching, costs accounting, and error handling.
"""
from __future__ import annotations

import os
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
    # naive extraction
    return data['choices'][0]['message']['content']


def _call_local_model(prompt: str) -> str:
    if not LOCAL_MODEL_URL:
        raise RuntimeError('LOCAL_MODEL_URL not set')
    r = requests.post(LOCAL_MODEL_URL, json={'prompt': prompt}, timeout=60)
    r.raise_for_status()
    data = r.json()
    return data.get('text') or data.get('result') or ''


def generate_text(prompt: str, tier: str = 'draft') -> str:
    """Generate text for a prompt using configured provider and tier."""
    # choose model name from tier
    model = MODEL_TIERS.get(tier, MODEL_TIERS['draft'])

    # Prefer local model if configured
    if LOCAL_MODEL_URL:
        try:
            return _call_local_model(prompt)
        except Exception as e:
            # fallback to openai if available
            if OPENAI_API_KEY:
                pass
            else:
                raise

    if OPENAI_API_KEY:
        messages = [
            {"role": "system", "content": "You are a helpful level design assistant. Provide structured output when possible."},
            {"role": "user", "content": prompt},
        ]
        return _call_openai_chat(messages, model=model, temperature=0.7)

    # Fallback: deterministic placeholder (no model)
    return f"[SIMULATED OUTPUT] Prompt was: {prompt[:200]}"


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
