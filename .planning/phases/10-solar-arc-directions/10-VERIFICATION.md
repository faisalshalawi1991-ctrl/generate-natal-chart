---
phase: 10-solar-arc-directions
verified: 2026-02-17T05:05:00Z
status: passed
score: 5/5 must-haves verified
re_verification: false
---

# Phase 10: Solar Arc Directions Verification Report

**Phase Goal:** Users can calculate solar arc directions using true arc method
**Verified:** 2026-02-17T05:05:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| #   | Truth                                                                                      | Status     | Evidence                                                                                        |
| --- | ------------------------------------------------------------------------------------------ | ---------- | ----------------------------------------------------------------------------------------------- |
| 1   | User can calculate solar arc directions for any target date or age against a natal profile | VERIFIED   | `--solar-arcs albert-einstein --target-date 2026-02-17` exits 0, outputs valid JSON            |
| 2   | User can see solar arc-to-natal aspects with 1-degree orb, sorted by orb                  | VERIFIED   | 6 aspects returned, all orbs <= 1.0, sorted ascending by orb, no orb exceeds 0.431             |
| 3   | User can choose between true arc (default) and mean arc (Naibod) methods                  | VERIFIED   | True arc = 141.935, mean arc = 144.821 at same date; both match research reference exactly     |
| 4   | Directed positions include all 10 major planets plus ASC and MC                            | VERIFIED   | `directed_planets count: 10`, `directed_angles count: 2` (ASC, MC) confirmed at runtime        |
| 5   | Each aspect shows applying/separating movement                                              | VERIFIED   | All 6 aspects have `movement` field; 0 aspects missing it; detection uses 1-year forward orb   |

**Score:** 5/5 truths verified

---

### Required Artifacts

| Artifact                    | Expected                                                         | Status   | Details                                          |
| --------------------------- | ---------------------------------------------------------------- | -------- | ------------------------------------------------ |
| `backend/astrology_calc.py` | SARC_DEFAULT_ORBS constant                                       | VERIFIED | Line 109: `SARC_DEFAULT_ORBS = {` — 5-entry dict, all orbs 1.0 |
| `backend/astrology_calc.py` | NAIBOD_ARC constant                                              | VERIFIED | Line 119: `NAIBOD_ARC = 0.98564733`             |
| `backend/astrology_calc.py` | SARC_ASPECT_ANGLES constant                                      | VERIFIED | Line 122: 5-entry dict (conjunction, opposition, trine, square, sextile) |
| `backend/astrology_calc.py` | SIGN_OFFSETS constant                                            | VERIFIED | Line 133: 12-sign offset dict                   |
| `backend/astrology_calc.py` | `def compute_solar_arc`                                          | VERIFIED | Line 1017: Full implementation — true arc via `swe.calc_ut`, mean arc via NAIBOD_ARC |
| `backend/astrology_calc.py` | `def angular_distance`                                           | VERIFIED | Line 1045: Handles zodiac wrap-around correctly  |
| `backend/astrology_calc.py` | `def build_sarc_aspects`                                         | VERIFIED | Line 1060: Nested loop, self-aspect skip, sorted by orb |
| `backend/astrology_calc.py` | `def build_solar_arc_json`                                       | VERIFIED | Line 1097: Full output — meta, directed_planets, directed_angles, aspects with movement |
| `backend/astrology_calc.py` | `def calculate_solar_arcs`                                       | VERIFIED | Line 1236: Loads profile, handles all target modes, prints JSON, error handling |
| `backend/astrology_calc.py` | `--solar-arcs SLUG` CLI argument                                 | VERIFIED | Line 1878: Defined with metavar, dest, help     |
| `backend/astrology_calc.py` | `--arc-method [true|mean]` CLI argument                          | VERIFIED | Line 1884: choices=['true','mean'], default='true' |

---

### Key Link Verification

| From                    | To                         | Via                                  | Status   | Details                                                                              |
| ----------------------- | -------------------------- | ------------------------------------ | -------- | ------------------------------------------------------------------------------------ |
| `calculate_solar_arcs`  | `load_natal_profile`       | function call with `args.solar_arcs` | WIRED    | Line 1250: `natal_subject, natal_data = load_natal_profile(args.solar_arcs)` — exact pattern match |
| `compute_solar_arc`     | `compute_progressed_jd`    | true arc JD arithmetic               | WIRED    | Lines 1038-1039: `progressed_jd = compute_progressed_jd(birth_jd, target_jd)` — reuses Phase 9 function |
| `main()`                | `calculate_solar_arcs`     | `if args.solar_arcs` routing         | WIRED    | Lines 1898-1900: routing fires before `--progressions` check; order confirmed: list -> solar_arcs -> progressions -> timeline -> transits |

---

### Requirements Coverage

| Requirement                                                          | Status    | Blocking Issue |
| -------------------------------------------------------------------- | --------- | -------------- |
| User can calculate solar arc directions for any target year          | SATISFIED | None           |
| User can see solar arc-to-natal aspects with 0.5-1 degree orb       | SATISFIED | None (1.0 degree orb implemented, within stated 0.5-1 range) |
| User can choose between true arc and mean arc calculation methods    | SATISFIED | None           |

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| None | —    | —       | —        | —      |

No anti-patterns detected. No TODO/FIXME/PLACEHOLDER comments. No stub returns. No console-only handlers.

---

### Human Verification Required

None. All success criteria are verifiable programmatically via CLI output inspection.

---

## Runtime Verification Results

The following tests were executed against the actual codebase:

**True arc reference test (Einstein, 2026-02-17):**
- `arc_degrees`: 141.935 — matches research reference 141.935 exactly (diff: 0.000)
- `arc_method`: true
- `elapsed_years`: 146.93
- `directed_planets count`: 10
- `directed_angles`: ASC, MC (2 entries)
- `aspects count`: 6 (research verified 6)
- Self-aspects: 0
- Orbs exceeding 1.0: 0
- Aspects missing `movement` field: 0

**Mean arc reference test (Einstein, 2026-02-17, --arc-method mean):**
- `arc_degrees`: 144.821 — matches research reference 144.821 exactly (diff: 0.000)
- `arc_method`: mean
- Difference from true arc: 2.886 degrees (expected ~2.9)

**Age-based target test (Einstein, --age 30):**
- `arc_degrees`: 29.663 (within expected 29-30 range)
- `elapsed_years`: 30.0

**Error handling test (nonexistent-person):**
- Exit code: 1
- Stderr: "Profile 'nonexistent-person' not found."

**Regression tests:**
- `--list`: exit 0 (8 profiles listed)
- `--progressions albert-einstein --target-date 2026-02-17`: exit 0

---

## Gaps Summary

No gaps. All 5 observable truths verified. All 11 artifacts substantive and wired. All 3 key links confirmed. All 3 success criteria from ROADMAP.md satisfied. Reference values match exactly. No anti-patterns. No regressions.

---

_Verified: 2026-02-17T05:05:00Z_
_Verifier: Claude (gsd-verifier)_
