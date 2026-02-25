#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

ROOT = Path("/Volumes/madara/2026/brandmint")
SESSION_DATA = Path(
    "/Users/sheshnarayaniyer/.craft-agent/workspaces/my-workspace/sessions/260224-proud-plain/data"
)


def sprint_tasks() -> list[dict]:
    return [
        {
            "phase_id": "P0",
            "name": "Documentation & Narrative Foundation",
            "objective": "Define user-first product narrative and docs before implementation.",
            "sprints": [
                {
                    "sprint_id": "S1",
                    "duration_weeks": 1,
                    "focus": "Repo documentation baseline from inspiration and current gaps",
                    "tasks": [
                        ("Audit current UI gaps vs inspiration references", "product", "Product Designer", 8),
                        ("Define UX principles for premium non-technical front UI", "product", "Product Designer", 8),
                        ("Write Product MD intake requirements spec", "product", "Product Manager", 6),
                        ("Write Brand Config mapping specification", "data", "Solutions Architect", 8),
                        ("Define target user personas and JTBD matrix", "product", "Product Researcher", 6),
                        ("Define information architecture for user-friendly flow", "frontend", "UX Designer", 8),
                        ("Draft microcopy/content style guide", "product", "Content Designer", 6),
                        ("Publish documentation baseline v1 sign-off", "product", "Product Manager", 5),
                    ],
                },
                {
                    "sprint_id": "S2",
                    "duration_weeks": 1,
                    "focus": "Journey and success criteria docs",
                    "tasks": [
                        ("Map end-to-end journey: Product MD to launch execution", "product", "UX Designer", 8),
                        ("Create storyboard for 8 key user screens", "product", "UX Designer", 8),
                        ("Define onboarding states and edge-case matrix", "product", "Product Manager", 7),
                        ("Define error handling copy and validation matrix", "product", "Content Designer", 6),
                        ("Define north-star metrics and adoption KPIs", "product", "Product Analyst", 6),
                        ("Set accessibility baseline and readability standards", "qa", "Accessibility QA", 6),
                        ("Define performance budget for front UI interactions", "infra", "Frontend Architect", 6),
                        ("Publish documentation pack v1 for delivery waves", "product", "Product Manager", 5),
                    ],
                },
            ],
        },
        {
            "phase_id": "P1",
            "name": "Prompt Scaffolding First",
            "objective": "Create and validate prompt scaffolds before visual and integration execution.",
            "sprints": [
                {
                    "sprint_id": "S3",
                    "duration_weeks": 1,
                    "focus": "Prompt architecture and templates",
                    "tasks": [
                        ("Design prompt architecture for UI narrative generation", "data", "Prompt Engineer", 8),
                        ("Create Product MD extraction prompt scaffold", "data", "Prompt Engineer", 8),
                        ("Create brand-config draft synthesis prompt scaffold", "data", "Prompt Engineer", 8),
                        ("Create aesthetic direction prompt from inspiration refs", "data", "Prompt Engineer", 7),
                        ("Create component copy variant prompt templates", "data", "Prompt Engineer", 6),
                        ("Create error/help text rewriting prompt templates", "data", "Prompt Engineer", 6),
                        ("Define prompt evaluation rubric and scorecard", "qa", "QA Engineer", 6),
                        ("Freeze prompt pack v1 for implementation", "product", "Product Manager", 5),
                    ],
                },
                {
                    "sprint_id": "S4",
                    "duration_weeks": 1,
                    "focus": "Prompt operations and validation harness",
                    "tasks": [
                        ("Define prompt registry schema and naming conventions", "data", "Prompt Engineer", 6),
                        ("Implement prompt versioning/changelog workflow", "infra", "DevOps Engineer", 6),
                        ("Build prompt test harness script", "data", "ML Engineer", 8),
                        ("Create 10 golden examples for prompt validation", "product", "Product Designer", 8),
                        ("Run prompt QA scoring and capture failures", "qa", "QA Engineer", 6),
                        ("Refine top failing prompts through focused iterations", "data", "Prompt Engineer", 8),
                        ("Write prompt usage docs for UI teams", "docs", "Technical Writer", 6),
                        ("Sign-off prompt scaffolding wave", "product", "Product Manager", 5),
                    ],
                },
            ],
        },
        {
            "phase_id": "P2",
            "name": "Front UI Core Journey",
            "objective": "Deliver user-friendly flow from Product MD intake to Brand Config creation.",
            "sprints": [
                {
                    "sprint_id": "S5",
                    "duration_weeks": 2,
                    "focus": "Intake experience (Product MD first)",
                    "tasks": [
                        ("Build friendly landing page replacing terminal-first entry", "frontend", "Frontend Eng", 10),
                        ("Build Product MD upload/dropzone component", "frontend", "Frontend Eng", 8),
                        ("Implement parsed section preview for uploaded MD", "frontend", "Frontend Eng", 10),
                        ("Create extracted fields review table", "frontend", "Frontend Eng", 8),
                        ("Implement inline correction editor for extracted fields", "frontend", "Frontend Eng", 10),
                        ("Add save draft intake session functionality", "backend", "Backend Eng", 8),
                        ("Add draft recovery and resume flow", "backend", "Backend Eng", 8),
                        ("Write intake flow integration tests", "qa", "QA Engineer", 8),
                    ],
                },
                {
                    "sprint_id": "S6",
                    "duration_weeks": 2,
                    "focus": "Brand Config wizard generation",
                    "tasks": [
                        ("Build multi-step wizard shell framework", "frontend", "Frontend Eng", 10),
                        ("Implement Brand Basics wizard step", "frontend", "Frontend Eng", 8),
                        ("Implement Audience & Positioning wizard step", "frontend", "Frontend Eng", 8),
                        ("Implement Voice & Tone wizard step", "frontend", "Frontend Eng", 8),
                        ("Implement Visual Direction wizard step", "frontend", "Frontend Eng", 8),
                        ("Implement Review & Confirm wizard step", "frontend", "Frontend Eng", 8),
                        ("Implement export to brand-config yaml/json", "backend", "Backend Eng", 10),
                        ("Implement config-ready success handoff card", "frontend", "Frontend Eng", 6),
                    ],
                },
            ],
        },
        {
            "phase_id": "P3",
            "name": "Visual Design Elevation",
            "objective": "Transform functional dashboard into premium, appealing user-facing experience.",
            "sprints": [
                {
                    "sprint_id": "S7",
                    "duration_weeks": 2,
                    "focus": "Design system premium revamp",
                    "tasks": [
                        ("Revamp design tokens for glass/skeuomorphic aesthetic", "frontend", "Design Systems Eng", 10),
                        ("Implement elevation and layered shadow system", "frontend", "Design Systems Eng", 8),
                        ("Calibrate dark-mode palette for readability and beauty", "frontend", "Design Systems Eng", 8),
                        ("Refine typography hierarchy for friendly clarity", "frontend", "Design Systems Eng", 8),
                        ("Build iconography system for key workflow states", "frontend", "Design Systems Eng", 8),
                        ("Define motion and interaction guidelines", "product", "Interaction Designer", 8),
                        ("Implement reusable component variant library", "frontend", "Frontend Eng", 10),
                        ("Create illustration placeholders and hero surfaces", "frontend", "UI Designer", 8),
                    ],
                },
                {
                    "sprint_id": "S8",
                    "duration_weeks": 2,
                    "focus": "Page-by-page polish for user appeal",
                    "tasks": [
                        ("Polish onboarding pages with narrative visual hierarchy", "frontend", "Frontend Eng", 8),
                        ("Polish wizard pages for calm progressive flow", "frontend", "Frontend Eng", 8),
                        ("Polish dashboard home for non-technical readability", "frontend", "Frontend Eng", 8),
                        ("Polish graph canvas with simplified semantics", "frontend", "Frontend Eng", 8),
                        ("Polish logs panel into actionable activity feed", "frontend", "Frontend Eng", 8),
                        ("Polish artifacts gallery as visual outcome wall", "frontend", "Frontend Eng", 8),
                        ("Polish reports preview with executive summary framing", "frontend", "Frontend Eng", 8),
                        ("Tune responsive breakpoints across laptop/tablet", "frontend", "Frontend Eng", 8),
                    ],
                },
            ],
        },
        {
            "phase_id": "P4",
            "name": "Orchestration UX Upgrade",
            "objective": "Make pipeline control intuitive while preserving execution power.",
            "sprints": [
                {
                    "sprint_id": "S9",
                    "duration_weeks": 1,
                    "focus": "Control center and dispatch UX",
                    "tasks": [
                        ("Redesign run controls top bar with clear intent states", "frontend", "Frontend Eng", 8),
                        ("Redesign wave timeline for narrative progression", "frontend", "Frontend Eng", 8),
                        ("Upgrade task cards with meaningful status language", "frontend", "Frontend Eng", 8),
                        ("Visualize dependency ribbons and blockers", "frontend", "Frontend Eng", 8),
                        ("Implement dispatch lane board for parallel execution", "frontend", "Frontend Eng", 10),
                        ("Add command palette with guided actions", "frontend", "Frontend Eng", 8),
                        ("Add quick action macros for common operations", "frontend", "Frontend Eng", 8),
                        ("Add keyboard shortcuts overlay", "frontend", "Frontend Eng", 6),
                    ],
                },
                {
                    "sprint_id": "S10",
                    "duration_weeks": 1,
                    "focus": "Trust, guidance, and recoverability",
                    "tasks": [
                        ("Build contextual tips system for each core page", "frontend", "Frontend Eng", 8),
                        ("Build assistant coach panel for first-run guidance", "frontend", "Frontend Eng", 8),
                        ("Design rich empty states with next-step guidance", "frontend", "Frontend Eng", 6),
                        ("Implement progressive disclosure for advanced settings", "frontend", "Frontend Eng", 8),
                        ("Implement confirmations for destructive actions", "frontend", "Frontend Eng", 6),
                        ("Build retry flow wizard with clear cause/resolution", "frontend", "Frontend Eng", 8),
                        ("Build failure triage cards with suggested actions", "frontend", "Frontend Eng", 8),
                        ("Add glossary/tooltips for non-technical users", "docs", "Technical Writer", 6),
                    ],
                },
            ],
        },
        {
            "phase_id": "P5",
            "name": "Backend Integration & Data Intelligence",
            "objective": "Back the front UI with robust APIs, persistence, and insights.",
            "sprints": [
                {
                    "sprint_id": "S11",
                    "duration_weeks": 2,
                    "focus": "Bridge API hardening and feature completion",
                    "tasks": [
                        ("Define typed bridge contract for UI/backend parity", "backend", "Backend Eng", 8),
                        ("Harden start/retry/abort process handling", "backend", "Backend Eng", 10),
                        ("Implement run queue and lifecycle state machine", "backend", "Backend Eng", 10),
                        ("Structure log streams by category and severity", "backend", "Backend Eng", 8),
                        ("Improve artifact indexing and metadata enrichment", "backend", "Backend Eng", 8),
                        ("Add config generation endpoint from wizard payload", "backend", "Backend Eng", 10),
                        ("Add prompt scaffold endpoint for UI prompts", "backend", "Backend Eng", 8),
                        ("Write bridge API integration test suite", "qa", "QA Engineer", 10),
                    ],
                },
                {
                    "sprint_id": "S12",
                    "duration_weeks": 2,
                    "focus": "Persistence, analytics, and reporting intelligence",
                    "tasks": [
                        ("Design local project/session store schema", "data", "Data Engineer", 8),
                        ("Implement autosave for intake and wizard states", "backend", "Backend Eng", 8),
                        ("Implement config snapshot version history", "backend", "Backend Eng", 8),
                        ("Capture run analytics events and timelines", "data", "Data Engineer", 8),
                        ("Compute quality score from validation rubric", "data", "Data Engineer", 8),
                        ("Add cost estimate model for planned waves", "data", "Data Engineer", 8),
                        ("Generate report summary endpoint for UI cards", "backend", "Backend Eng", 8),
                        ("Sync frontend with live backend state deltas", "frontend", "Frontend Eng", 10),
                    ],
                },
            ],
        },
        {
            "phase_id": "P6",
            "name": "QA Hardening & Launch",
            "objective": "Ship confidently with quality, docs, and rollout readiness.",
            "sprints": [
                {
                    "sprint_id": "S13",
                    "duration_weeks": 1,
                    "focus": "Quality hardening and reliability",
                    "tasks": [
                        ("Create E2E happy path: Product MD to pipeline run", "qa", "QA Engineer", 10),
                        ("Create E2E validation/error recovery path tests", "qa", "QA Engineer", 8),
                        ("Run visual regression for critical journey screens", "qa", "QA Engineer", 8),
                        ("Run accessibility audit and remediation pass", "qa", "Accessibility QA", 8),
                        ("Run performance optimization and bundle tuning", "infra", "Frontend Architect", 8),
                        ("Run reliability chaos tests around retry flows", "qa", "QA Engineer", 8),
                        ("Run security/privacy review for local data", "security", "Security Engineer", 8),
                        ("Publish QA sign-off checklist", "qa", "QA Lead", 6),
                    ],
                },
                {
                    "sprint_id": "S14",
                    "duration_weeks": 1,
                    "focus": "Launch readiness and execution handoff",
                    "tasks": [
                        ("Build in-app docs hub for guided usage", "docs", "Technical Writer", 8),
                        ("Create quickstart tutorial for first-time users", "docs", "Technical Writer", 8),
                        ("Write stakeholder demo script and runbook", "product", "Product Manager", 6),
                        ("Finalize release checklist and rollback plan", "infra", "DevOps Engineer", 6),
                        ("Prepare onboarding walkthrough media assets", "product", "Content Designer", 6),
                        ("Create telemetry dashboard definitions", "data", "Data Engineer", 6),
                        ("Prioritize v2 backlog from test feedback", "product", "Product Manager", 6),
                        ("Launch candidate sign-off and handoff", "product", "Product Manager", 5),
                    ],
                },
            ],
        },
    ]


def map_lane(area: str) -> str:
    return {
        "frontend": "frontend",
        "backend": "integration",
        "data": "prompt",
        "infra": "platform",
        "qa": "qa",
        "product": "ux",
        "docs": "docs",
        "security": "security",
    }.get(area, "program")


def build_plan() -> dict:
    phases = sprint_tasks()
    last_task_id_by_sprint: dict[tuple[str, str], str] = {}
    flat_count = 0

    for p in phases:
        for s in p["sprints"]:
            task_rows = s.pop("tasks")
            built = []
            for idx, (title, area, owner, est) in enumerate(task_rows, start=1):
                task_id = f"{p['phase_id']}-{s['sprint_id']}-{idx:02d}"
                deps: list[str] = []
                prev_phase_sprint_key = None
                if idx == 1:
                    # Depend on last task of previous sprint
                    prev_phase_index = phases.index(p)
                    sprint_index = p["sprints"].index(s)
                    if sprint_index > 0:
                        prev_phase_sprint_key = (p["phase_id"], p["sprints"][sprint_index - 1]["sprint_id"])
                    elif prev_phase_index > 0:
                        prev_p = phases[prev_phase_index - 1]
                        prev_phase_sprint_key = (prev_p["phase_id"], prev_p["sprints"][-1]["sprint_id"])
                    if prev_phase_sprint_key and prev_phase_sprint_key in last_task_id_by_sprint:
                        deps = [last_task_id_by_sprint[prev_phase_sprint_key]]
                elif idx in (2, 3):
                    deps = [f"{p['phase_id']}-{s['sprint_id']}-01"]
                elif idx in (4, 5):
                    deps = [f"{p['phase_id']}-{s['sprint_id']}-02"]
                elif idx == 6:
                    deps = [f"{p['phase_id']}-{s['sprint_id']}-03"]
                elif idx == 7:
                    deps = [f"{p['phase_id']}-{s['sprint_id']}-04", f"{p['phase_id']}-{s['sprint_id']}-05"]
                elif idx == 8:
                    deps = [f"{p['phase_id']}-{s['sprint_id']}-06", f"{p['phase_id']}-{s['sprint_id']}-07"]

                lane = map_lane(area)
                built.append(
                    {
                        "id": task_id,
                        "title": title,
                        "area": area,
                        "owner_role": owner,
                        "est_hours": est,
                        "dependencies": deps,
                        "deliverable": f"{title} completed and available in the UI workflow.",
                        "acceptance": "Feature is testable end-to-end and passes defined quality criteria.",
                        "dispatch_lane": lane,
                        "parallelizable": len(deps) <= 2,
                        "wave": p["phase_id"],
                        "sprint": s["sprint_id"],
                    }
                )
                flat_count += 1
            s["tasks"] = built
            last_task_id_by_sprint[(p["phase_id"], s["sprint_id"])] = built[-1]["id"]

    return {
        "schema_version": "1.0",
        "project": {
            "name": "Brandmint Front UI Replacement Plan",
            "repo_root": str(ROOT),
            "generated_on": datetime.now().strftime("%Y-%m-%d"),
            "generated_by": "task-master-planner + dispatching-parallel-agents",
            "assumptions": [
                "Fixed UI port remains 4188 with clear-and-retry policy.",
                "Brandmint CLI (`bm launch`) remains execution backend.",
                "Initial user entry point must be Product MD upload and wizard flow.",
            ],
            "risks": [
                "Over-optimizing orchestration dashboard may delay user-friendly front flow.",
                "Prompt scaffolding quality impacts extraction and wizard confidence.",
                "Lack of real sample Product MD files may cause validation blind spots.",
            ],
            "totals": {
                "tasks": flat_count,
                "phases": 7,
                "sprints": 14,
            },
            "dispatch_strategy": "Run sprint tasks in parallel by dispatch_lane where dependencies permit.",
        },
        "phases": phases,
    }


def main() -> None:
    plan = build_plan()
    out_repo = ROOT / "ui" / "src" / "data" / "taskmaster-front-ui-v2.json"
    out_session = SESSION_DATA / "brandmint-front-ui-taskmaster-v2.json"
    out_repo.parent.mkdir(parents=True, exist_ok=True)
    out_session.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(plan, indent=2)
    out_repo.write_text(serialized, encoding="utf-8")
    out_session.write_text(serialized, encoding="utf-8")
    print(f"WROTE:{out_repo}")
    print(f"WROTE:{out_session}")
    print(f"TASKS:{plan['project']['totals']['tasks']}")


if __name__ == "__main__":
    main()
