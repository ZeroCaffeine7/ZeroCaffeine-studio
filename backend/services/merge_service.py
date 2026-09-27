"""Merge service for the PoC.

Provides simple merge logic for project-level merging of worker results and
creates repair tasks when structural conflicts (e.g., connector mismatches)
are detected. This is deliberately simple for the PoC; replace the text
synthesis with a real model call when integrating with LLMs.
"""
from __future__ import annotations

from typing import Dict, List, Tuple
import re


def _get(task, name, default=None):
    try:
        return getattr(task, name)
    except Exception:
        return task.get(name, default) if isinstance(task, dict) else default


def _set(task, name, value):
    if isinstance(task, dict):
        task[name] = value
    else:
        setattr(task, name, value)


def _collect_results_for_task(task_id: str, results_db: Dict[str, dict]) -> List[dict]:
    return [r for r in results_db.values() if _get(r, "task_id") == task_id]


def _simple_text_merge(texts: List[str]) -> str:
    """Very small synthesis step: deduplicate, keep order, and join with headers.
    Replace with an LLM synthesis step for production.
    """
    seen = set()
    parts = []
    for i, t in enumerate(texts, 1):
        if t in seen:
            continue
        seen.add(t)
        parts.append(f"--- Source {i} ---\n{t}\n")
    merged = "\n".join(parts)
    merged += "\n# Manager notes\nMerged using simple PoC merge. Please review for coherence."
    return merged


_CONNECTOR_REGEX = re.compile(r"connect(?:ors?)?:?\s*(\{[^}]*\}|\[[^\]]*\]|[^\n]+)", re.IGNORECASE)


def _extract_connectors(text: str) -> List[str]:
    m = _CONNECTOR_REGEX.findall(text)
    if not m:
        return []
    results = []
    for item in m:
        # strip braces or brackets
        s = item.strip()
        s = s.strip("{}[] ")
        # split by comma or whitespace
        parts = re.split(r"[,;\s]+", s)
        parts = [p for p in parts if p]
        results.extend(parts)
    return results


def merge_project(project_id: str, tasks_db: Dict[str, dict], results_db: Dict[str, dict]) -> Tuple[dict, List[str]]:
    """Merge all completed tasks for a project into a single consolidated output.

    Returns (merged_summary, created_repair_task_ids).
    """
    # Gather project tasks
    project_tasks = [t for t in tasks_db.values() if _get(t, "project_id") == project_id]

    merged_sections = []
    repair_tasks_created: List[str] = []

    # For connector conflict detection across tasks per chunk, we collect connectors per task
    connectors_map: Dict[str, List[List[str]]] = {}

    for task in project_tasks:
        task_id = _get(task, "id")
        role = _get(task, "role_name") or _get(task, "role")
        title = _get(task, "title")
        status = _get(task, "status")

        if status != "completed":
            # skip non-completed tasks
            continue

        results = _collect_results_for_task(task_id, results_db)
        texts = [(_get(r, "result_text") or "") for r in results]

        if not texts:
            # no result provided
            merged_text = "<no output>"
        elif len(texts) == 1:
            merged_text = texts[0]
        else:
            # simple merge across multiple worker outputs
            merged_text = _simple_text_merge(texts)

        merged_sections.append({"task_id": task_id, "role": role, "title": title, "merged_text": merged_text})

        # connector extraction for conflict detection
        for t in texts:
            conn = _extract_connectors(t)
            if conn:
                connectors_map.setdefault(task_id, []).append(conn)

        # mark task as merged
        _set(task, "status", "merged")

    # Detect connector conflicts and create repair tasks
    # If a task has multiple connector lists that are not identical, schedule a repair
    next_task_index = len(tasks_db) + 1
    for task_id, conn_lists in connectors_map.items():
        unique = {tuple(sorted(c)) for c in conn_lists}
        if len(unique) > 1:
            # conflict detected
            repair_id = f"task-{next_task_index}"
            next_task_index += 1
            repair_task = {
                "id": repair_id,
                "project_id": project_id,
                "title": f"Repair connectors for {task_id}",
                "description": "Resolve connector inconsistencies between worker outputs. Ensure neighbor connectivity and update connector ids.",
                "role_name": "level_design",
                "status": "new",
            }
            tasks_db[repair_id] = repair_task
            repair_tasks_created.append(repair_id)

    # Build final merged summary
    merged_summary_parts = [f"Merged project {project_id}", ""]
    for sec in merged_sections:
        merged_summary_parts.append(f"== {sec['role']} - {sec['title']} ({sec['task_id']}) ==\n{sec['merged_text']}\n")

    merged_summary = "\n".join(merged_summary_parts)

    return {"project_id": project_id, "merged_summary": merged_summary}, repair_tasks_created
