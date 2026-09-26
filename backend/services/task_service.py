from backend.agents.manager import build_subtasks
from backend.agents.worker import generate_worker_output, merge_worker_outputs


def run_project_poc(project_title: str, project_description: str) -> dict:
    subtasks = build_subtasks(project_title, project_description)

    task_results = []
    for task in subtasks:
        worker_output = generate_worker_output(
            task["role_name"],
            task["title"],
            task["description"],
        )
        task_results.append({
            "role_name": task["role_name"],
            "result_text": worker_output,
        })

    merged = merge_worker_outputs(task_results)

    return {
        "project_title": project_title,
        "subtasks": subtasks,
        "task_results": task_results,
        "merged_output": merged,
    }
