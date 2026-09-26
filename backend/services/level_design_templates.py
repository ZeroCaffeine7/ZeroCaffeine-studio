"""Level design task generator for PoC

Provides helper to split a project map into chunks and emit microtask dicts.
"""

def split_into_chunks(project_title: str, project_description: str, width: int, height: int, chunk_size: int):
    """Split a map of width x height into chunks of chunk_size and return list of microtasks."""
    chunks = []
    cols = max(1, width // chunk_size)
    rows = max(1, height // chunk_size)
    idx = 0
    for r in range(rows):
        for c in range(cols):
            idx += 1
            chunk_id = f"chunk-{idx:04d}"
            bounds = {"x": c * chunk_size, "y": r * chunk_size, "w": chunk_size, "h": chunk_size}
            task = {
                "task_id": chunk_id,
                "project": project_title,
                "chunk_index": idx,
                "bounds": bounds,
                "instructions": f"Design the terrain and 2-4 POIs for chunk {chunk_id}. Ensure connectors to neighbors are specified.",
                "role": "level_design",
                "redundancy": 1,
            }
            chunks.append(task)
    return chunks


if __name__ == "__main__":
    # quick demo
    demo = split_into_chunks("Mist Dungeon - Level 1", "A foggy dungeon", 640, 640, 64)
    import json
    print(json.dumps(demo[:3], indent=2, ensure_ascii=False))
