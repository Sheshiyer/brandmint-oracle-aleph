#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path("/Volumes/madara/2026/brandmint")
SESSION_DATA = Path(
    "/Users/sheshnarayaniyer/.craft-agent/workspaces/my-workspace/sessions/260224-proud-plain/data"
)
UI_PLAN_PATH = ROOT / "ui" / "src" / "data" / "taskmaster-7waves.json"
SESSION_PLAN_PATH = SESSION_DATA / "brandmint-ui-taskmaster-7waves-detailed.json"


def make_tasks() -> list[dict]:
    lanes = [
        "frontend",
        "integration",
        "design",
        "qa",
        "platform",
        "prompt",
        "docs",
        "security",
        "ux",
        "program",
    ]

    wave_pages = {
        1: [
            ("Onboarding", "Project Selector"),
            ("Onboarding", "Scenario Picker"),
            ("Onboarding", "Config Import"),
            ("Dashboard", "Run Header"),
            ("Dashboard", "Wave Rail"),
            ("Dashboard", "Task Board"),
            ("Dashboard", "Quality Snapshot"),
            ("Dashboard", "Status Timeline"),
            ("Pipeline Graph", "Node Legend"),
            ("Pipeline Graph", "Dependency Preview"),
            ("Settings", "Port & Runtime"),
            ("Settings", "Environment Check"),
            ("Artifacts", "Catalog Skeleton"),
            ("Logs", "Console Skeleton"),
            ("Reports", "Summary Shell"),
            ("Operations", "Runbook Links"),
        ],
        2: [
            ("Design System", "Color Tokens"),
            ("Design System", "Type Scale"),
            ("Design System", "Spacing Scale"),
            ("Design System", "Border + Radius"),
            ("Design System", "Glass Surfaces"),
            ("Design System", "Skeuo Controls"),
            ("Design System", "Button Set"),
            ("Design System", "Form Controls"),
            ("Dashboard", "Card Pattern"),
            ("Dashboard", "Section Frames"),
            ("Dashboard", "Iconography"),
            ("Pipeline Graph", "Node Cards"),
            ("Pipeline Graph", "Edge Styles"),
            ("Logs", "Severity Badges"),
            ("Artifacts", "Preview Tiles"),
            ("Docs", "Component Catalog"),
        ],
        3: [
            ("Dashboard", "Header Actions"),
            ("Dashboard", "Wave Selector"),
            ("Dashboard", "Task Grid"),
            ("Dashboard", "Dependency Drawer"),
            ("Pipeline Graph", "Canvas Layout"),
            ("Pipeline Graph", "Drag Nodes"),
            ("Pipeline Graph", "Animated Edges"),
            ("Pipeline Graph", "Mini Map"),
            ("Logs", "Live Stream Panel"),
            ("Logs", "Filters + Search"),
            ("Artifacts", "Asset Explorer"),
            ("Artifacts", "Detail Pane"),
            ("Reports", "KPI Widgets"),
            ("Reports", "Progress Charts"),
            ("Operations", "Command Palette"),
            ("Operations", "Keyboard Shortcuts"),
        ],
        4: [
            ("Backend Bridge", "Process Manager"),
            ("Backend Bridge", "bm launch Runner"),
            ("Backend Bridge", "Run PID Tracker"),
            ("Backend Bridge", "Retry + Port Clear"),
            ("Backend Bridge", "Abort Handler"),
            ("Backend Bridge", "Resume Handler"),
            ("Backend Bridge", "State Endpoint"),
            ("Backend Bridge", "Task Endpoint"),
            ("Backend Bridge", "Wave Endpoint"),
            ("Backend Bridge", "Logs SSE"),
            ("Backend Bridge", "Artifacts Endpoint"),
            ("Settings", "Port 4188 Lock"),
            ("Settings", "Command Template"),
            ("Security", "Env Redaction"),
            ("Security", "Local Access Guard"),
            ("Operations", "Health Checks"),
        ],
        5: [
            ("Dashboard", "Wave Timeline"),
            ("Dashboard", "Lane Matrix"),
            ("Dashboard", "Dispatch Queue"),
            ("Dashboard", "Blocker Alerts"),
            ("Pipeline Graph", "Batch Launch View"),
            ("Pipeline Graph", "Parallel Lane Coloring"),
            ("Logs", "Run Session Tabs"),
            ("Logs", "Error Focus Mode"),
            ("Artifacts", "Publish Readiness"),
            ("Artifacts", "Diff Viewer"),
            ("Reports", "Cost Board"),
            ("Reports", "Quality Board"),
            ("Reports", "Accessibility Board"),
            ("Prompt Studio", "Prompt Sets"),
            ("Prompt Studio", "Prompt History"),
            ("Operations", "Operator Notes"),
        ],
        6: [
            ("QA", "Component Tests"),
            ("QA", "Integration Tests"),
            ("QA", "Process-control Tests"),
            ("QA", "Port-retry Tests"),
            ("QA", "Visual Regression"),
            ("QA", "Performance Budget"),
            ("QA", "Accessibility Audit"),
            ("QA", "Memory Leak Checks"),
            ("QA", "Error-recovery Drills"),
            ("QA", "Long-run Stability"),
            ("Security", "Secret Scanning"),
            ("Security", "Localhost Hardening"),
            ("Observability", "Structured Logs"),
            ("Observability", "Run Metrics"),
            ("Observability", "Trace IDs"),
            ("Operations", "Release Candidate Gate"),
        ],
        7: [
            ("Launch", "Final Polish"),
            ("Launch", "Motion Pass"),
            ("Launch", "Copy Pass"),
            ("Launch", "Onboarding Walkthrough"),
            ("Launch", "Scenario Demo: surface"),
            ("Launch", "Scenario Demo: focused"),
            ("Launch", "Scenario Demo: comprehensive"),
            ("Launch", "Acceptance Sign-off"),
            ("Docs", "Operator Manual"),
            ("Docs", "Troubleshooting Guide"),
            ("Docs", "Component Guide"),
            ("Docs", "API Bridge Guide"),
            ("Handoff", "Taskbook Export"),
            ("Handoff", "Metrics Snapshot"),
            ("Handoff", "Backlog v1.1"),
            ("Handoff", "Implementation Notes"),
        ],
    }

    tasks: list[dict] = []
    prev_wave_last_ids: list[str] = []
    for wave in range(1, 8):
        this_wave_ids: list[str] = []
        items = wave_pages[wave]
        for idx, (page, component) in enumerate(items, start=1):
            task_id = f"W{wave}-T{idx:02d}"
            lane = lanes[(idx - 1) % len(lanes)]
            depends_on: list[str] = []
            if idx > 1:
                depends_on.append(f"W{wave}-T{idx - 1:02d}")
            if prev_wave_last_ids and idx % 2 == 0:
                depends_on.append(prev_wave_last_ids[(idx // 2 - 1) % len(prev_wave_last_ids)])
            tasks.append(
                {
                    "id": task_id,
                    "wave": wave,
                    "sequence": idx,
                    "title": f"{page}: {component}",
                    "description": f"Implement {component} for {page} in the Brandmint localhost UI.",
                    "page": page,
                    "component": component,
                    "status": "pending",
                    "priority": "high" if wave <= 4 else ("medium" if wave <= 6 else "high"),
                    "dispatch_lane": lane,
                    "owner_agent": f"{lane}-agent",
                    "parallelizable": len(depends_on) <= 2,
                    "depends_on": depends_on,
                    "estimated_hours": 2 if wave <= 3 else (3 if wave <= 5 else 2),
                    "acceptance_criteria": [
                        f"{component} is visible and functional in localhost UI",
                        "Behavior aligns with wave dependency model",
                        "No regressions in fixed-port 4188 orchestration flow",
                    ],
                }
            )
            this_wave_ids.append(task_id)
        prev_wave_last_ids = this_wave_ids[-4:]
    return tasks


def main() -> None:
    tasks = make_tasks()
    wave_summary = [{"wave": w, "task_count": 16} for w in range(1, 8)]
    obj = {
        "taskmaster_version": "1.1-detailed",
        "metadata": {
            "project": "Brandmint Localhost Interactive UI Pipeline",
            "as_of": "2026-02-24T07:15:00+05:30",
            "mode": "page-by-page component-by-component detailed plan",
            "fixed_port": 4188,
        },
        "wave_summary": wave_summary,
        "totals": {
            "tasks": len(tasks),
            "estimated_hours": sum(t["estimated_hours"] for t in tasks),
            "dispatch_lanes": sorted(list({t["dispatch_lane"] for t in tasks})),
        },
        "tasks": tasks,
    }

    UI_PLAN_PATH.parent.mkdir(parents=True, exist_ok=True)
    SESSION_PLAN_PATH.parent.mkdir(parents=True, exist_ok=True)

    # backup current ui plan
    if UI_PLAN_PATH.exists():
        backup = UI_PLAN_PATH.with_suffix(".json.bak")
        backup.write_text(UI_PLAN_PATH.read_text(encoding="utf-8"), encoding="utf-8")

    serialized = json.dumps(obj, indent=2)
    UI_PLAN_PATH.write_text(serialized, encoding="utf-8")
    SESSION_PLAN_PATH.write_text(serialized, encoding="utf-8")
    print(f"WROTE_UI:{UI_PLAN_PATH}")
    print(f"WROTE_SESSION:{SESSION_PLAN_PATH}")
    print(f"TASKS:{len(tasks)}")


if __name__ == "__main__":
    main()
