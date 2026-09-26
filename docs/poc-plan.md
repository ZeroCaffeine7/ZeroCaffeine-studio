# PoC Plan

This document describes the first working prototype of the ZeroCaffeine Studio AI game studio.

## Goal

Build the smallest possible system that proves the following:

- A boss can submit a complex game task
- A manager can split the task into sub-tasks across multiple roles
- Multiple worker agents can process the tasks concurrently
- Manager can merge and review results
- The system provides a clean workflow for future expansion

## Example scenario

Project: "Mist Dungeon - Level 1"

Tasks:
- Level design
- Enemy design
- Narrative / world context
- Quality assurance

## Core flow

1. Boss submits a project brief
2. Manager creates the project tasks
3. Tasks are assigned to worker roles
4. Worker agents generate outputs
5. Manager reviews and merges outputs
6. Boss sees the final result and can request revisions

## Proposed modules

- Backend API
- Manager agent
- Worker agents
- Task & project storage
- Review pipeline
- Minimal frontend dashboard

## Data model

### Project
- id
- title
- description
- status
- created_at

### Task
- id
- project_id
- parent_task_id (nullable)
- title
- description
- role_name
- status
- created_at

### Result
- id
- task_id
- worker_name
- result_text
- created_at

### Review
- id
- project_id
- reviewer_name
- status
- comments
- created_at

## MVP behaviors

- Create a project via POST /projects
- Create child tasks under that project via Manager logic
- Assign tasks to workers by role
- Worker generates a response
- Manager merges worker output into a final review object
- Boss gets final summary

## Notes

This PoC is intentionally simple and does not yet include enterprise-scale orchestration, distributed queues, or thousands of agents. It aims to validate the architecture before scaling to departments and large AI staff pools.
