# Phase 13: Tech Debt Cleanup - Research

**Researched:** 2026-02-17
**Domain:** Python CLI patching — JSON schema extension and control-flow wiring
**Confidence:** HIGH

## Summary

Phase 13 closes two discrete audit gaps identified in `v1.1-MILESTONE-AUDIT.md`. Both gaps are well-understood, self-contained changes with no external library dependencies. The code patterns to follow already exist in the codebase — they need to be applied to two additional sites.

**Gap 1 — meta.slug in chart.json:** `build_chart_json()` assembles the `meta` dict before the slug is computed in `main()`. The slug is derived at line 2290 (`profile_slug = slugify(args.name)`), after `build_chart_json(subject, args)` is called at line 2287. The fix is to pass `profile_slug` into `build_chart_json()` or compute it inside the function, then include it in the `meta` dict.

**Gap 2 — --save in timeline mode:** `calculate_timeline()` (lines 628-699) prints the timeline JSON and returns 0 without ever checking `args.save`. The exact same save pattern used in `calculate_transits()` (lines 494-500), `calculate_progressions()` (lines 1037-1043), and `calculate_solar_arcs()` (lines 1327-1333) must be added after `print(json.dumps(timeline_dict, indent=2))` in `calculate_timeline()`.

**Gap 3 — SKILL.md routing table:** SKILL.md line 151 says "use `meta.slug`" and line 168 says "append `--save` to any predictive command". After Gaps 1 and 2 are fixed, both statements become accurate. No SKILL.md text changes are needed if the backend is fixed; the SKILL.md wording is already correct as a forward-looking specification.

**Primary recommendation:** Fix both backend gaps first, then verify SKILL.md accuracy as a read step rather than a write step.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| python-slugify | pinned (venv) | Convert names to URL-safe slugs | Already in use at line 26 and 2290 |
| json (stdlib) | 3.11 | JSON serialization | Already used throughout |
| pathlib.Path (stdlib) | 3.11 | File path construction | Already used for profile_dir |

### Supporting

No new libraries required. All changes use existing imports and existing helpers.

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Adding slug to build_chart_json() | Updating SKILL.md to not use meta.slug | Fixing the data is more robust; slug in chart.json is useful for any consumer reading the file |
| Implementing --save for timeline | Narrowing SKILL.md to exclude timeline | SKILL.md already says "any predictive command"; fixing the backend closes the gap cleanly |

**Installation:** None. No new dependencies.

---

## Architecture Patterns

### Existing Save Pattern (replicate exactly)

The save pattern in `calculate_transits()` is the canonical form. Replicate it verbatim in `calculate_timeline()`:

```python
# Source: backend/astrology_calc.py lines 494-500 (calculate_transits)
if args.save:
    date_str = transit_dict['meta'].get('query_date', 'unknown')
    try:
        out_path = save_snapshot(CHARTS_DIR / args.transits, 'transit', date_str, transit_dict)
        print(f"Snapshot saved: {out_path}", file=sys.stderr)
    except Exception as e:
        print(f"Warning: Could not save snapshot: {e}", file=sys.stderr)
```

For timeline, adapt as:

```python
# After: print(json.dumps(timeline_dict, indent=2))
# Before: return 0
if args.save:
    date_str = timeline_dict['meta'].get('start_date', 'unknown')
    try:
        out_path = save_snapshot(CHARTS_DIR / args.timeline, 'timeline', date_str, timeline_dict)
        print(f"Snapshot saved: {out_path}", file=sys.stderr)
    except Exception as e:
        print(f"Warning: Could not save snapshot: {e}", file=sys.stderr)
```

**Date string choice:** Timeline has `start_date` and `end_date` in its meta. Using `start_date` is the natural anchor — it matches how transits use `query_date` (the primary date defining the snapshot). `end_date` would also work, but `start_date` is more intuitive as the "when does this begin" timestamp.

**Mode string for filename:** Use `'timeline'` (no hyphen). This matches the natural language of `--timeline` flag. Compare: `transit-2026-02-17.json`, `progressions-2026-02-17.json`, `solar-arc-2026-02-17.json`, `timeline-2026-03-01.json`.

### meta.slug Addition Pattern

The slug is computed in `main()` at line 2290, after `build_chart_json()` is called at line 2287. Two options:

**Option A — Pass slug into build_chart_json() (preferred)**

Change function signature to `build_chart_json(subject, args, slug=None)` and add `"slug": slug` to the meta dict. In `main()`, compute the slug first, then pass it:

```python
# main() — reorder lines 2287-2290:
profile_slug = slugify(args.name)          # compute slug first
chart_dict = build_chart_json(subject, args, slug=profile_slug)  # pass slug
```

This keeps `build_chart_json()` self-contained and the meta dict complete.

**Option B — Compute slug inside build_chart_json()**

Call `slugify(args.name)` inside `build_chart_json()` directly. Simpler signature but adds a dependency on `slugify` inside the function (already imported at module level, so no import change needed).

**Recommendation:** Option B is marginally simpler — `slugify` is already a module-level import and `args.name` is already available inside `build_chart_json()`. The function already reads `args.name` at line 1448. Calling `slugify(args.name)` on line 1448 as well eliminates the need to change the call site in `main()`.

### Where to insert slug in meta dict

Add `"slug"` as the second field in the meta dict, immediately after `"name"`, for logical proximity:

```python
# Source: backend/astrology_calc.py lines 1447-1461 (build_chart_json meta section)
meta = {
    "name": args.name,
    "slug": slugify(args.name),         # ADD THIS LINE
    "birth_date": args.date.strftime("%Y-%m-%d"),
    "birth_time": args.time.strftime("%H:%M"),
    "location": { ... },
    "house_system": "Placidus",
    "chart_type": None,
    "generated_at": datetime.now(timezone.utc).isoformat()
}
```

### Anti-Patterns to Avoid

- **Changing build_chart_json() signature:** Avoid changing the function signature if Option B suffices — the function already has access to everything it needs.
- **Using end_date as timeline filename anchor:** Prefer start_date; it is the more natural "this is when the timeline begins" timestamp.
- **Using `timeline_dict['meta']['start_date']` without .get():** All other save call sites use `.get('key', 'unknown')` as a defensive fallback. Maintain that pattern.
- **Adding --save to SKILL.md's routing table description before backend is fixed:** Verification of SKILL.md accuracy should happen after the backend changes are committed.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Slug computation | Custom regex name cleaner | `slugify(args.name)` | Already used at line 2290 — same call, same result |
| File write with error handling | Custom try/except file logic | `save_snapshot()` helper + try/except shell | Pattern already established in 3 places |

**Key insight:** Both changes are pattern applications, not new patterns. The planner should copy existing code blocks rather than design new ones.

---

## Common Pitfalls

### Pitfall 1: Slug Computation Inconsistency

**What goes wrong:** Using a different slug computation in `build_chart_json()` vs. `main()`, causing `meta.slug` to differ from the actual profile directory name.

**Why it happens:** `main()` calls `slugify(args.name)` at line 2290. If `build_chart_json()` calls `slugify(args.name)` independently, the calls are identical and results match — but only if the same import and function are used.

**How to avoid:** Call `slugify` identically in both places: `slugify(args.name)`. The `slugify` function is deterministic — same input always produces same output.

**Warning signs:** After fixing, test with a name containing spaces ("John Doe" → "john-doe") and special characters ("O'Brien" → "o-brien") to confirm parity.

### Pitfall 2: Timeline --save Call Site Placement

**What goes wrong:** Placing the `if args.save:` block inside the `try:` block but after a `return 0`, making it unreachable. Or placing it outside the `try:` block, bypassing the `except` clauses.

**Why it happens:** The `calculate_timeline()` function has a single `try/except` block. The `return 0` is at line 689. The save block must go between `print(json.dumps(...))` (line 688) and `return 0` (line 689), inside the existing `try:` block.

**How to avoid:** Match the exact structure of `calculate_transits()` lines 492-502. Print first, then save (inside the same try block), then return.

**Warning signs:** If the confirmation message "Snapshot saved: ..." never appears even when `--save` is passed, the block is unreachable.

### Pitfall 3: Mode String Filename Collisions

**What goes wrong:** Choosing a mode string for the timeline filename that collides with an existing mode (e.g., using `'transit'` instead of `'timeline'`), causing a timeline save to overwrite a transit snapshot with the same date.

**Why it happens:** `save_snapshot()` constructs filename as `f"{mode}-{date_str}.json"`. If `mode='transit'` and `date_str='2026-03-01'`, the filename is `transit-2026-03-01.json` — same as a transit snapshot on that date.

**How to avoid:** Use `'timeline'` as the mode string. This is unique and unambiguous.

### Pitfall 4: Overwriting Existing chart.json on --force

**What goes wrong:** Adding `meta.slug` to chart.json is a schema change. Old profiles without `meta.slug` will work fine (code only adds the field on write, never reads it for routing). No migration needed.

**Why it happens:** Non-issue for this change — `meta.slug` is a read-only reference field that SKILL.md consumes. The backend never reads `meta.slug` back from disk. Old profiles without it degrade gracefully.

**How to avoid:** No action required. Confirm that no backend code attempts `chart_data['meta']['slug']` without a `.get()` fallback.

---

## Code Examples

Verified patterns from existing source:

### Pattern 1: Existing save block in calculate_transits (lines 494-500)

```python
# Source: backend/astrology_calc.py lines 491-502
# Output to stdout
print(json.dumps(transit_dict, indent=2))

if args.save:
    date_str = transit_dict['meta'].get('query_date', 'unknown')
    try:
        out_path = save_snapshot(CHARTS_DIR / args.transits, 'transit', date_str, transit_dict)
        print(f"Snapshot saved: {out_path}", file=sys.stderr)
    except Exception as e:
        print(f"Warning: Could not save snapshot: {e}", file=sys.stderr)

return 0
```

### Pattern 2: Current calculate_timeline end (lines 686-699)

```python
# Source: backend/astrology_calc.py lines 686-699
# Extract exact hit events and assemble output
timeline_dict = build_timeline_json(results, natal_data, args.timeline, start_dt, end_dt)
print(json.dumps(timeline_dict, indent=2))
return 0

except FileNotFoundError as e:
    print(f"Error: {e}", file=sys.stderr)
    return 1
except ValueError as e:
    print(f"Error: {e}", file=sys.stderr)
    return 1
except Exception as e:
    print(f"Error calculating timeline: {e}", file=sys.stderr)
    return 1
```

After fix, the `return 0` section becomes:

```python
print(json.dumps(timeline_dict, indent=2))

if args.save:
    date_str = timeline_dict['meta'].get('start_date', 'unknown')
    try:
        out_path = save_snapshot(CHARTS_DIR / args.timeline, 'timeline', date_str, timeline_dict)
        print(f"Snapshot saved: {out_path}", file=sys.stderr)
    except Exception as e:
        print(f"Warning: Could not save snapshot: {e}", file=sys.stderr)

return 0
```

### Pattern 3: Current build_chart_json meta dict (lines 1447-1461)

```python
# Source: backend/astrology_calc.py lines 1447-1461
meta = {
    "name": args.name,
    "birth_date": args.date.strftime("%Y-%m-%d"),
    "birth_time": args.time.strftime("%H:%M"),
    "location": {
        "city": getattr(subject, 'city', None),
        "nation": getattr(subject, 'nation', None),
        "latitude": subject.lat,
        "longitude": subject.lng,
        "timezone": subject.tz_str
    },
    "house_system": "Placidus",
    "chart_type": None,
    "generated_at": datetime.now(timezone.utc).isoformat()
}
```

After fix, add `"slug": slugify(args.name)` after `"name"`:

```python
meta = {
    "name": args.name,
    "slug": slugify(args.name),
    "birth_date": args.date.strftime("%Y-%m-%d"),
    ...
}
```

### Pattern 4: SKILL.md line 151 (the dead reference)

```
# Source: ~/.claude/skills/natal-chart/SKILL.md line 151
   - If chart.json is already loaded in context: use `meta.slug`
```

After Gap 1 is fixed, this reference becomes valid — no SKILL.md edit needed.

### Pattern 5: SKILL.md line 168 (the overstated scope)

```
# Source: ~/.claude/skills/natal-chart/SKILL.md line 168
   | "save this", "keep this", "store this snapshot" | append `--save` to any predictive command | `--transits albert-einstein --save` |
```

After Gap 2 is fixed, "any predictive command" becomes accurate — no SKILL.md edit needed.

---

## State of the Art

| Old State | New State | When Changed | Impact |
|-----------|-----------|--------------|--------|
| `meta` in chart.json has no `slug` field | `meta` includes `"slug": "name-slug"` | Phase 13 | SKILL.md line 151 reference becomes valid |
| `calculate_timeline()` ignores `--save` silently | `calculate_timeline()` saves snapshot when `--save` is passed | Phase 13 | User intent to save a timeline is fulfilled |
| SKILL.md routing table overstates `--save` scope | SKILL.md routing table is accurate | Phase 13 (via backend fix) | No text change to SKILL.md required |

**No deprecated items.** This phase adds new behavior, not replacements.

---

## Open Questions

1. **Which date field to use as the timeline snapshot filename anchor?**
   - What we know: Timeline meta has `start_date`, `end_date`, and `range_days`. Transit uses `query_date`. Progressions use `target_date`. Solar arc uses `target_date`.
   - What's unclear: No prior decision specifies which timeline meta field to use.
   - Recommendation: Use `start_date`. It uniquely identifies the snapshot origin and follows the "primary date" convention of other modes. A `timeline-2026-03-01.json` is self-explanatory.

2. **Should SKILL.md be updated even if backend fixes make the wording accurate?**
   - What we know: After both backend fixes, SKILL.md line 151 and line 168 become accurate without any text change.
   - What's unclear: Whether the success criterion "SKILL.md routing table accurately reflects which modes support --save" requires a text change or just a verification read.
   - Recommendation: Treat SKILL.md verification as a read-only step. If the wording is accurate post-fix, no edit is needed. Document the verification in the plan as a check step, not a write step.

3. **Do existing chart.json profiles need backfill?**
   - What we know: The backend never reads `meta.slug` from disk — it only reads `meta.name`, `meta.birth_date`, `meta.birth_time`, `meta.location`. Profiles without `meta.slug` remain fully functional.
   - What's unclear: Whether the planner should include a backfill task.
   - Recommendation: No backfill needed. Old profiles work correctly. New profiles will include the field. If a user runs `--force` on an existing profile, the new chart.json will include the slug field.

---

## Sources

### Primary (HIGH confidence)

- Direct code inspection: `C:/NEW/backend/astrology_calc.py` — lines 320-337 (save_snapshot), 443-509 (calculate_transits with --save), 586-699 (calculate_timeline, no --save), 1037-1043 (calculate_progressions --save), 1327-1333 (calculate_solar_arcs --save), 1447-1461 (build_chart_json meta), 2287-2304 (main slug computation and chart.json write)
- Direct code inspection: `~/.claude/skills/natal-chart/SKILL.md` — lines 150-168 (predictive mode routing table with meta.slug and --save references)
- `C:/NEW/.planning/v1.1-MILESTONE-AUDIT.md` — lines 110-124 (tech debt items 1 and 2, verified gap descriptions)

### Secondary (MEDIUM confidence)

- Phase 12 prior decisions (from phase_context) — confirmed save pattern decisions: stderr-only confirmation, try/except shell, JSON stdout before file I/O, date_str from meta field

### Tertiary (LOW confidence)

None. All findings are based on direct source code inspection.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new libraries; all patterns verified from existing code
- Architecture: HIGH — replicate existing patterns from 3 verified call sites
- Pitfalls: HIGH — slug consistency and call site placement verified by code inspection

**Research date:** 2026-02-17
**Valid until:** This research is based on the current codebase state and will remain valid until `astrology_calc.py` is modified. No external dependency changes.
