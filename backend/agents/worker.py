from typing import List


def generate_worker_output(role_name: str, title: str, description: str) -> str:
    role_map = {
        "level_design": "Level Design Output: a structured layout with a clear route, key encounters, and safe progression. Include 3 key zones.",
        "enemy_design": "Enemy Design Output: propose 3 enemy archetypes with behaviors and difficulty curve recommendations.",
        "story_design": "Narrative Design Output: provide a short atmospheric summary, unique hooks, and a narrative objective.",
        "qa": "QA Output: highlight risks, balance concerns, and a short playtest checklist.",
    }

    base = role_map.get(role_name, "Worker Output: generic summary")
    return f"{base}\nTask: {title}\nContext: {description}"


def merge_worker_outputs(results: List[dict]) -> str:
    merged_parts = [
        "# Manager Consolidated Output",
        "",
        "### Combined task results",
    ]

    for item in results:
        merged_parts.append(f"- {item['role_name']}: {item['result_text']}")

    merged_parts.append("")
    merged_parts.append("### Final recommendation")
    merged_parts.append("The level has a clear risk profile and is ready for prototype iteration with minor tuning.")
    return "\n".join(merged_parts)
