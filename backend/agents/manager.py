from typing import List


ROLE_LIBRARY = {
    "level_design": {
        "name": "Level Designer",
        "description": "Designs spatial layout, flow, and encounter pacing for a level.",
    },
    "enemy_design": {
        "name": "Enemy Designer",
        "description": "Designs enemy types, composition, and difficulty tuning.",
    },
    "story_design": {
        "name": "Narrative Designer",
        "description": "Creates world context and narrative hook for the level.",
    },
    "qa": {
        "name": "QA Tester",
        "description": "Reviews playability, balance, and bug risk.",
    },
}


def build_subtasks(project_title: str, project_description: str) -> List[dict]:
    return [
        {
            "title": f"{project_title} - Level Design",
            "description": f"Design the layout and pacing for: {project_description}",
            "role_name": "level_design",
        },
        {
            "title": f"{project_title} - Enemy Design",
            "description": f"Design enemy composition and difficulty for: {project_description}",
            "role_name": "enemy_design",
        },
        {
            "title": f"{project_title} - Narrative Design",
            "description": f"Add narrative context and world flavor for: {project_description}",
            "role_name": "story_design",
        },
        {
            "title": f"{project_title} - QA Review",
            "description": f"Review the level for risks and usability: {project_description}",
            "role_name": "qa",
        },
    ]
