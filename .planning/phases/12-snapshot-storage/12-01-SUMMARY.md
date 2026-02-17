---
phase: 12-snapshot-storage
plan: 01
subsystem: backend-cli
tags: [snapshot-storage, predictive-modes, persistence, cli-flag]
dependency_graph:
  requires: [calculate_transits, calculate_progressions, calculate_solar_arcs, load_natal_profile, CHARTS_DIR]
  provides: [save_snapshot, --save flag, transit snapshot files, progressions snapshot files, solar-arc snapshot files]
  affects: [astrology_calc.py predictive mode functions, SKILL.md routing table]
tech_stack:
  added: []
  patterns: [conditional post-print save block, stderr-only confirmation, silent overwrite, date-based filename from meta field]
key_files:
  created: []
  modified:
    - backend/astrology_calc.py
    - ~/.claude/skills/natal-chart/SKILL.md
decisions:
  - "save_snapshot() placed after load_natal_profile() to maintain logical grouping of profile I/O helpers"
  - "Save call site placed after print() and before return 0 so JSON stdout is always complete before any file I/O"
  - "try/except around save_snapshot() call so file write failure never corrupts or suppresses already-printed JSON"
  - "Confirmation message goes to stderr only (never stdout) to preserve JSON parsability of stdout"
  - "Mode string 'solar-arc' (hyphenated) used for filename consistency with natural language convention"
  - "date_str sourced from meta field (query_date / target_date) to guarantee YYYY-MM-DD format"
metrics:
  duration: "3 minutes"
  completed: "2026-02-17"
  tasks_completed: 2
  files_modified: 2
---

# Phase 12 Plan 01: Snapshot Storage Summary

**One-liner:** --save flag with save_snapshot() helper persists transit/progressions/solar-arc snapshots as {mode}-{YYYY-MM-DD}.json files in existing profile directories, with stderr-only confirmation and silent overwrite.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add --save flag, save_snapshot() helper, call sites, SKILL.md routing | 1286424 | backend/astrology_calc.py, ~/.claude/skills/natal-chart/SKILL.md |
| 2 | End-to-end snapshot storage verification | — (verification only) | — |

## What Was Built

### save_snapshot() Helper Function

Added after `load_natal_profile()` (the logical grouping point for profile I/O helpers). The function:
- Takes `profile_dir` (Path), `mode` (str), `date_str` (str), `data` (dict)
- Writes `{mode}-{date_str}.json` to the profile directory using `json.dump()` with indent=2
- Returns the written path for use in the confirmation message

### --save Argparse Flag

Added directly after `--force` flag definition. `action='store_true'` — no value required.

### Call Sites in Three Calculate Functions

Pattern applied identically in `calculate_transits()`, `calculate_progressions()`, and `calculate_solar_arcs()`:
```python
if args.save:
    date_str = <dict>['meta'].get('<date_key>', 'unknown')
    try:
        out_path = save_snapshot(CHARTS_DIR / args.<slug_attr>, '<mode>', date_str, <dict>)
        print(f"Snapshot saved: {out_path}", file=sys.stderr)
    except Exception as e:
        print(f"Warning: Could not save snapshot: {e}", file=sys.stderr)
```

Date keys used:
- Transits: `transit_dict['meta']['query_date']`
- Progressions: `prog_dict['meta']['target_date']`
- Solar arcs: `sarc_dict['meta']['target_date']`

### SKILL.md Routing Update

Added `--save` row to the predictive mode routing table:
```
| "save this", "keep this", "store this snapshot" | append `--save` to any predictive command | `--transits albert-einstein --save` |
```

## Verification Results

### INTG-05: All Three Modes Save Snapshots

| Mode | File Created | chart_type in JSON |
|------|-------------|-------------------|
| `--transits albert-einstein --save` | `transit-2026-02-17.json` | `transit_snapshot` |
| `--progressions albert-einstein --save` | `progressions-2026-02-17.json` | `secondary_progressions` |
| `--solar-arcs albert-einstein --save` | `solar-arc-2026-02-17.json` | `solar_arc_directions` |

### INTG-06: Date-Based Naming

| Command | File Created |
|---------|-------------|
| `--transits ... --query-date 2025-06-15 --save` | `transit-2025-06-15.json` |
| `--progressions ... --target-date 2025-06-15 --save` | `progressions-2025-06-15.json` |
| `--solar-arcs ... --target-date 2025-06-15 --save` | `solar-arc-2025-06-15.json` |

### Age-Based Progressions Filename

`--progressions albert-einstein --age 30 --save` → `progressions-1909-03-14.json` (no "None" or "unknown")

### No Corruption

Stdout remains valid JSON when --save is used. All confirmations printed to stderr only.

### Silent Overwrite

Running the same `--save` command twice exits 0 both times — no error, no prompt.

### Regression

All existing modes unaffected: `--list`, `--transits` (no save), `--timeline`, `--progressions` (no save), `--solar-arcs` (no save), natal create with `--force`.

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check: PASSED

All artifacts verified:
- `backend/astrology_calc.py` — exists, contains `def save_snapshot` and `'--save'` argparse flag
- `~/.claude/skills/natal-chart/SKILL.md` — exists, contains --save routing entry
- `.planning/phases/12-snapshot-storage/12-01-SUMMARY.md` — this file
- Commit `1286424` — exists in git log
- Snapshot files created in `~/.natal-charts/albert-einstein/`: transit, progressions, solar-arc for 2026-02-17
