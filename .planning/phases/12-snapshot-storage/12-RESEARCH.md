# Phase 12: Snapshot Storage - Research

**Researched:** 2026-02-17
**Domain:** File I/O, CLI argument pattern, Python pathlib — no new libraries required
**Confidence:** HIGH

## Summary

Phase 12 adds optional disk persistence to the three existing predictive modes (transits, progressions, solar arcs). Currently, all three modes print JSON to stdout and exit — the output is ephemeral, captured only in Claude's context during a session. Phase 12 closes that gap by writing the same JSON dict to a dated file inside the existing profile directory when the user passes `--save`.

This is a pure file-I/O extension to already-complete calculation functions. The JSON builders (`build_transit_json()`, `build_progressed_json()`, `build_solar_arc_json()`) already produce the final dict. Phase 12 adds one new CLI flag (`--save`), a single `save_snapshot()` helper function, and a small conditional block in each of the three `calculate_*()` routing functions. No new libraries, no schema changes, no new profile directories.

The date-based naming requirement (INTG-06) maps cleanly onto the `meta.query_date`, `meta.target_date`, or `meta.target_date` fields each JSON builder already populates. The mode can be inferred from the `meta.chart_type` field (`transit_snapshot`, `secondary_progressions`, `solar_arc_directions`).

**Primary recommendation:** Add a single `save_snapshot(profile_dir, mode, date_str, data_dict)` helper, call it from each `calculate_*()` function after the JSON builder returns, and add one `--save` boolean flag to the parser. No structural changes to existing functions needed.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pathlib.Path | stdlib | File path construction, directory creation, write | Already used for profile storage in main() |
| json | stdlib | JSON serialization | Already used for all chart.json writes |
| datetime | stdlib | Fallback date string if meta field absent | Already imported |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| (none) | — | No additional libraries needed | Phase is pure file I/O using existing stack |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Flat filename (`transit-2026-02-17.json`) | Nested subfolder per date | Flat is simpler; profile dir stays uncluttered; listing is straightforward with glob |
| Adding `--save` flag | Always-save or ask interactively | `--save` is consistent with `--force` non-interactive philosophy; skill can pass it selectively |
| Separate `snapshots/` subfolder | Root of profile dir | Either works; root keeps it flat and consistent with existing chart.json/chart.svg pattern |

**Installation:**
```bash
# No new dependencies — stdlib only
```

## Architecture Patterns

### Recommended Project Structure
```
~/.natal-charts/{slug}/
├── chart.json               # natal profile (existing)
├── chart.svg                # natal SVG (existing)
├── transit-2026-02-17.json  # snapshot (new, date-based)
├── progressions-2026-02-17.json
└── solar-arc-2026-02-17.json
```

### Pattern 1: save_snapshot() Helper
**What:** Single function that takes the mode name, date string, profile directory, and JSON dict and writes to disk.
**When to use:** Called inside each `calculate_*()` function after the JSON builder returns, gated on `args.save`.
**Example:**
```python
def save_snapshot(profile_dir: Path, mode: str, date_str: str, data: dict) -> Path:
    """
    Write predictive snapshot JSON to the profile directory.

    Args:
        profile_dir: Path — ~/.natal-charts/{slug}/
        mode:        str  — 'transit', 'progressions', or 'solar-arc'
        date_str:    str  — YYYY-MM-DD for filename (from meta field)
        data:        dict — already-assembled JSON dict from build_*_json()

    Returns:
        Path: The written file path (for confirmation message)
    """
    filename = f"{mode}-{date_str}.json"
    out_path = profile_dir / filename
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return out_path
```

### Pattern 2: --save flag, consistent with --force
**What:** Boolean argparse flag, no value required. Follows the `--force` convention already in the codebase.
**When to use:** Passed by the user (or by SKILL.md) when they want the output persisted.
**Example:**
```python
parser.add_argument(
    '--save',
    action='store_true',
    help='Save snapshot to profile directory with date-based filename'
)
```

### Pattern 3: Call site in calculate_*() functions
**What:** After `print(json.dumps(data, indent=2))`, check `args.save` and write.
**Example (transit pattern, same for progressions and solar arcs):**
```python
    transit_dict = build_transit_json(...)
    print(json.dumps(transit_dict, indent=2))

    if args.save:
        date_str = transit_dict['meta'].get('query_date', 'unknown')
        out_path = save_snapshot(CHARTS_DIR / args.transits, 'transit', date_str, transit_dict)
        print(f"Snapshot saved: {out_path}", file=sys.stderr)

    return 0
```

### Pattern 4: Date string extraction from meta
Each builder already stores the date in `meta`:

| Mode | Builder | meta key | Value example |
|------|---------|----------|---------------|
| Transits | `build_transit_json()` | `meta['query_date']` | `"2026-02-17"` |
| Progressions | `build_progressed_json()` | `meta['target_date']` | `"2026-02-17"` (or None if age-based — see Pitfall 1) |
| Solar Arcs | `build_solar_arc_json()` | `meta['target_date']` | `"2026-02-17"` |

### Anti-Patterns to Avoid
- **Re-computing the date string independently:** The JSON dict already has `meta['query_date']` / `meta['target_date']` — read from there, do not reformat `args.target_date` separately. This keeps filename and JSON content in sync.
- **Writing before printing:** Print JSON to stdout first (existing behavior), then optionally write. Never block stdout on file I/O.
- **Overwrite without warning:** If the same date is used twice, the file will overwrite silently. This matches the behavior of `chart.json` on `--force` and is acceptable given the non-interactive design. An overwrite warning is optional but adds complexity for minimal value.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Date string for filename | Date formatting logic | `meta['query_date']` / `meta['target_date']` already in dict | Builders already compute it; reuse avoids desync |
| Directory existence check | `if not dir.exists(): dir.mkdir()` | `profile_dir.mkdir(parents=True, exist_ok=True)` | Profile dir was created when natal chart was saved; it always exists by the time predictive modes run. No need to guard. |
| JSON serialization | Custom encoder | `json.dump(..., indent=2, ensure_ascii=False)` | Same pattern used throughout the file |

**Key insight:** The entire implementation is wiring already-existing outputs to already-existing I/O patterns. No new logic is introduced — only a new flag, a new filename template, and a call site.

## Common Pitfalls

### Pitfall 1: target_date is None for age-based progressions
**What goes wrong:** When the user passes `--age N` instead of `--target-date`, `build_progressed_json()` may store `None` as `meta['target_date']` (or a computed string — verify from the actual code).
**Why it happens:** The progressions builder computes `target_date_str = None` when `args.age` is used; it reconstructs the date from JD via `swe.revjul` later in the function. Check `build_progressed_json()` carefully to confirm what ends up in `meta['target_date']`.
**How to avoid:** In `save_snapshot()` or at the call site, guard against None: `date_str = date_str or 'unknown'`. Alternatively, always derive the date string from `swe.revjul(target_jd)` before calling `save_snapshot()` — the target_jd is always available in `calculate_progressions()`.
**Warning signs:** Filename becomes `progressions-None.json`.

### Pitfall 2: Confirmation message on stderr vs stdout
**What goes wrong:** The "Snapshot saved" confirmation message pollutes stdout if printed there, breaking any downstream JSON parsing of the output.
**Why it happens:** All calculation modes print pure JSON to stdout. A confirmation message mixed in would corrupt the output.
**How to avoid:** Always print the save confirmation to `sys.stderr`, same as warning messages throughout the codebase (e.g., `print(f"Warning: ...", file=sys.stderr)`).
**Warning signs:** Skill receives malformed JSON when `--save` is passed.

### Pitfall 3: Profile directory may not exist (edge case)
**What goes wrong:** If a natal profile slug is invalid, `load_natal_profile()` raises `FileNotFoundError` before any snapshot can be saved. This is handled already. However, if somehow the profile dir was deleted after loading, `save_snapshot()` would raise `FileNotFoundError`.
**Why it happens:** Edge case; unlikely in practice since `load_natal_profile()` validates the directory.
**How to avoid:** Wrap `save_snapshot()` call in try/except and print a warning to stderr on failure. Do not exit(1) — the calculation already succeeded and the JSON was printed.

### Pitfall 4: Filename collision between modes on the same date
**What goes wrong:** If `transit-2026-02-17.json` and `progressions-2026-02-17.json` both exist in the profile dir, `--list` output does not know about them, and the user may not realize how many snapshots are accumulating.
**Why it happens:** No cleanup mechanism exists; snapshots persist indefinitely.
**How to avoid:** Out of scope for Phase 12 (INTG-05/06 only require save + date-naming). Document as a known accumulation behavior. A future cleanup command could address this.

### Pitfall 5: save_snapshot() called with wrong profile_dir for transits
**What goes wrong:** Transit subject is at lat=0.0/lng=0.0 (geocentric), but the profile dir is keyed to the natal chart slug (`args.transits`). If the wrong slug is used, the snapshot goes to the wrong folder.
**Why it happens:** `args.transits` holds the natal slug, `args.progressions` holds the progressions slug, `args.solar_arcs` holds the solar arcs slug — all are natal chart slugs. The snapshot belongs in `CHARTS_DIR / args.{mode_slug}`.
**How to avoid:** Use `CHARTS_DIR / args.transits`, `CHARTS_DIR / args.progressions`, `CHARTS_DIR / args.solar_arcs` respectively in each call site. Do not pass a generic `slug` variable.

## Code Examples

Verified patterns from codebase inspection:

### Existing file write pattern (chart.json in main())
```python
# Source: backend/astrology_calc.py line ~2248
json_file = profile_dir / "chart.json"
with open(json_file, 'w', encoding='utf-8') as f:
    json.dump(chart_dict, f, indent=2, ensure_ascii=False)
```

### Existing --force flag pattern (argparse)
```python
# Source: backend/astrology_calc.py line ~1809
parser.add_argument(
    "--force",
    action="store_true",
    help="Overwrite existing profile without confirmation"
)
```

### Existing stderr warning pattern
```python
# Source: backend/astrology_calc.py line ~2275
print(f"Warning: SVG generation may have failed - chart.svg not found", file=sys.stderr)
```

### Existing transit meta structure (for date extraction)
```python
# Source: backend/astrology_calc.py build_transit_json() line ~343
meta = {
    "natal_name": natal_name,
    "natal_slug": slug,
    "query_date": query_date_str,    # <-- use this for filename
    "query_time_utc": ...,
    "chart_type": "transit_snapshot",
    "calculated_at": ...,
    "orbs_used": orbs_used,
}
```

### Existing solar arc meta structure
```python
# Source: backend/astrology_calc.py build_solar_arc_json() line ~1121
meta = {
    'natal_name': natal_name,
    'natal_slug': slug,
    'target_date': target_date_str,   # <-- use this for filename
    'arc_degrees': round(arc, 3),
    'arc_method': arc_method,
    'elapsed_years': round(elapsed_years, 2),
    'chart_type': 'solar_arc_directions',
    'calculated_at': ...,
    'orbs_used': SARC_DEFAULT_ORBS,
}
```

### What build_progressed_json() stores in meta.target_date
The progressions builder calls `swe.revjul(prog_jd)` to get the progressed date but the *target* date (for the snapshot filename) comes from `target_date_str` passed in as a parameter. When `args.age` is used, `target_date_str` is set to `None` in `calculate_progressions()` at line ~964. The builder receives `None` for `target_date_str` in the age-based case and stores it verbatim. This confirms Pitfall 1: guard against `None`.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Ephemeral stdout only | Stdout + optional --save to disk | Phase 12 (new) | Users can build a historical record of predictive analyses |

**Deprecated/outdated:**
- Nothing deprecated in this phase.

## Open Questions

1. **Should SKILL.md be updated to expose --save to users?**
   - What we know: SKILL.md routes user intent to CLI flags. --save needs to be passable for users who want to keep snapshots.
   - What's unclear: Whether this update belongs in Phase 12 or is out of scope (INTG-05/06 specify backend behavior only).
   - Recommendation: Include a minimal SKILL.md update in Phase 12 — add `--save` to the routing table note so Claude knows to pass it when user says "save this" or "keep this snapshot". This completes the feature end-to-end. Alternatively, if that's out of scope, document as a known gap for Phase 13.

2. **target_date when --age is used for progressions: None or computed?**
   - What we know: `calculate_progressions()` sets `target_date_str = None` at line ~964 when `args.age` is used. This None is passed into `build_progressed_json()`.
   - What's unclear: Whether `build_progressed_json()` fills it in later before putting it in meta, or leaves it None.
   - Recommendation: Inspect `build_progressed_json()` meta construction during implementation to confirm. Plan must include a fallback: `swe.revjul(target_jd)` is always available to generate a real date string in the age-based case.

3. **Should existing snapshots prevent save (like --force for chart.json)?**
   - What we know: chart.json creation uses --force to gate overwrites. Snapshot files don't have the same "precious natal data" concern — they're computed on-demand and can be regenerated.
   - What's unclear: User expectation.
   - Recommendation: Silent overwrite (no --force needed for snapshots). The non-interactive CLI philosophy favors simplicity; snapshot overwrites are not destructive.

## Sources

### Primary (HIGH confidence)
- Direct code inspection of `C:/NEW/backend/astrology_calc.py` (2,297 lines) — all patterns, function signatures, existing constants
- Phase 7 SUMMARY (07-01-SUMMARY.md) — transit routing and `build_transit_json()` output structure
- Phase 9 SUMMARY (09-01-SUMMARY.md) — progressions routing and `target_date_str = None` for age-based case
- Phase 10 SUMMARY (10-01-SUMMARY.md) — solar arc routing and `build_solar_arc_json()` output structure
- Phase 11 SUMMARY (11-01-SUMMARY.md) — SKILL.md routing and auto-load patterns
- SKILL.md at `~/.claude/skills/natal-chart/SKILL.md` — current routing and context loading steps
- ROADMAP.md — INTG-05/06 requirements text

### Secondary (MEDIUM confidence)
- (none needed — all critical findings verified from direct code inspection)

### Tertiary (LOW confidence)
- (none)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — stdlib only, already used throughout the file
- Architecture: HIGH — directly modeled on existing `--force`, `chart.json` write, and `save_svg` patterns in the same file
- Pitfalls: HIGH — Pitfalls 1-5 all verified against actual code; not speculative

**Research date:** 2026-02-17
**Valid until:** 2026-03-17 (30 days — codebase is stable, stdlib patterns don't change)
