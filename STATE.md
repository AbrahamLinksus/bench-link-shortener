# STATE — bench-link-shortener

> Source of truth for resuming. Updated after every task.

| Field | Value |
|---|---|
| Problem | Link shortener API (FastAPI + SQLite): shorten, redirect with click count, stats |
| Repo | AbrahamLinksus/bench-link-shortener (public) |
| Stage | 7 Build |
| Milestone | M2 · Run and ship (2/3 tasks: T-04b added by CR-1) — M1 done |
| Next step | T-04b · backend-coder · start.sh shell-wins + tests/test_start_script.py + README fix — then LLD header as-built note, then handover |
| Last updated | 2026-11-09 |

## Team
| Agent | Model | Why on this project |
|---|---|---|
| backend-coder | Sonnet | API + SQLite code |
| tester | Sonnet | endpoint tests, coverage |
| reviewer | Opus (Sonnet for low-risk) | read-only review |
| debugger | Opus (Sonnet for low-risk) | failures |
| docs | Haiku | README |

## Open work
- Tasks in progress live on `wip/*` branches (see `taskgit.sh list`); their step states are in each branch's TASK_PROGRESS.md.

## Open decisions (waiting for the owner)
- none

## How to run
```bash
uv sync            # python deps
# npm ci           # frontend deps
# uv run ...       # start commands
```

## Context additions
Context gaps agents reported (`Context gap:` in a REPORT). The Orchestrator adds these to the
`Read:` field for that role on top of the per-role defaults in brief-template.md.
| Role | Also read | Why (from gap report) |
|---|---|---|
| reviewer | docs/SPEC.md §5 (API tasks) | T-03 review could not check §5 coverage without it |

## Notes for the next session
- Owner: Jake · Approval mode: batch-low-risk · Cost mode: balanced
- M1 approved 2026-11-09 (main dcff4e1). Resume with `/setup-project resume bench-link-shortener`.
- T-04 approved 2026-11-09 (main 92a72c0). M2 approved 2026-11-09 (main 9b961b0); owner chose a fresh session.
- CR-1 merged 2026-11-09 (main 138ef54) → T-04b. After T-04b: architect flips LLD header "CR-1 design only" note to as-built.
- CR-1 (owner-approved fix): shell env must win over .env in start.sh; README "Known edge case" block and LLD §10.1 edge-case list must be updated with it.
- Capture needs: `uv run --with playwright --with markdown python $CAPTURE ...` (playwright not in system python).
- Owner-provided requirements: docs/owner-spec.md (treat as full requirements) 
