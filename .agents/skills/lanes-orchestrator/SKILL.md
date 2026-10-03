---
name: lanes-orchestrator
description: Coordinate substantial LANES tasks using actual subagents for independent investigation, implementation, and review. Use when the user requests a LANES agent team or parallel agent work; keep small or tightly dependent tasks in one agent.
---

# LANES Orchestrator

Skills supply instructions; they do not start separate agents. Use the runtime's actual subagent tools when available. If unavailable, explain the limitation and continue in one agent without claiming parallel execution.

## Establish scope

Read the repository's `AGENTS.md` and `DESIGN.md`, inspect the active branch and working-tree changes, and identify the user's requested outcome. Preserve existing work. Resolve paths from the active checkout, including worktrees, rather than a developer's absolute machine path.

Honor existing authorization. Delegation does not authorize schema changes, commits, pushes, merges, or external messages. Follow the repository's specific approval rules for those actions.

## Delegate bounded work

Use subagents when independent questions or disjoint implementation areas would benefit from separate contexts. Keep short tasks and dependent decisions in the coordinator. Respect the runtime's available concurrency; do not assume a fixed team size.

Give each subagent:
- The requested outcome and a bounded question or implementation assignment.
- The active checkout, relevant inputs, and applicable skill paths.
- Read-only status or explicit ownership of files it may edit.
- Required checks and the expected report: evidence, findings, changed files, verification, and unresolved concerns.

Tell subagents to read applicable repository instructions and their assigned skills before editing. Investigators report findings without changing files. Assign a single writer per file; shared files, manifests, and integration changes remain with the coordinator unless explicitly handed off. Do not have agents switch branches in a shared checkout. Avoid nested delegation unless the coordinator explicitly assigns it.

## Route by actual task

Load only the skills needed by each assignment:
- News discovery, flood extraction, claim specificity, evidence, and placement: [news-intelligence-agent](../news-intelligence-agent/SKILL.md), with api-agent for backend implementation.
- Backend endpoints, services, NLP/geocoding, and spatial queries: [api-agent](../api-agent/SKILL.md).
- React components and desktop/mobile presentation: [ui-agent](../ui-agent/SKILL.md).
- Regression tests and verification: [test-agent](../test-agent/SKILL.md).
- Permissions, secrets, and security review: [security-agent](../security-agent/SKILL.md).
- File organization and architecture: [architecture-agent](../architecture-agent/SKILL.md).
- Plans and documentation synchronization: [senior-planner-agent](../senior-planner-agent/SKILL.md).
- Branch comparisons and authorized merges: [merge-coordinator-agent](../merge-coordinator-agent/SKILL.md).

A role label does not require a new skill folder. Assign domain-specific investigations through the relevant existing skill and concrete task context.

## Integrate and verify

Compare findings against code and evidence, choose the approach, and coordinate dependent edits. Review returned diffs rather than accepting completion claims alone. Use an independent reviewer for substantial changes when useful; run appropriate checks and fix material findings. Keep verification honest about unavailable services or environments.

Update only documentation affected by the completed work. Report the outcome, important findings, verification, and remaining limitations. Commit or push only when requested, following the repository protocol.
