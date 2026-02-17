---
phase: 09-secondary-progressions
verified: 2026-02-17T04:40:00Z
status: passed
score: 6/6 must-haves verified
re_verification: false
---

# Phase 9: Secondary Progressions Verification Report

**Phase Goal:** Users can calculate secondary progressions using day-for-a-year formula
**Verified:** 2026-02-17T04:40:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | User can calculate secondary progressions for a target date with `--progressions SLUG --target-date YYYY-MM-DD` | VERIFIED | Live run: `--progressions albert-einstein --target-date 2026-02-17` exits 0, `meta.chart_type="secondary_progressions"`, `meta.target_date="2026-02-17"`, `meta.progressed_date="1879-08-08"` |
| 2 | User can calculate secondary progressions for an age with `--progressions SLUG --age N` | VERIFIED | Live run: `--age 30` exits 0, `meta.age_at_target=30`, `meta.progressed_date="1879-04-13"` (30 days after birth, matches day-for-year formula) |
| 3 | User can see progressed-to-natal aspects with 1 degree orb in the JSON output | VERIFIED | Live run: `progressed_aspects` list has 6 entries, `max_orb=1.0`, all orbs <= 1.0; `PROG_DEFAULT_ORBS` constant defined at line 98 with orb=1 for all 5 aspect types; `active_aspects=PROG_DEFAULT_ORBS` at line 818 |
| 4 | User can see monthly progressed Moon positions and sign changes for a target year | VERIFIED | Live run: `monthly_moon` has exactly 12 entries, each with `month`, `sign`, `degree`; sign changes detected and present in output; `--prog-year 2025` override produces `monthly_moon` entries starting with `"2025-"` |
| 5 | User can see element and modality distribution shifts between natal and progressed charts | VERIFIED | Live run: `distribution_shift.elements` has Fire/Earth/Air/Water each with `natal`, `progressed`, `delta` fields; `distribution_shift.modalities` has Cardinal/Fixed/Mutable same structure |
| 6 | Existing `--transits`, `--timeline`, `--list`, and natal chart creation modes continue working unchanged | VERIFIED | `--transits albert-einstein` outputs `chart_type: transit_snapshot`; `--timeline albert-einstein --range week` outputs `chart_type: transit_timeline`; `--list` returns 8 profiles, exits 0 |

**Score:** 6/6 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/astrology_calc.py` | Progressions constant, functions, CLI arguments, main() routing; contains `def calculate_progressions` | VERIFIED | 1966 lines; `PROG_DEFAULT_ORBS` at line 98; `compute_progressed_jd` at line 640; `build_monthly_moon` at line 660; `build_progressed_json` at line 710; `calculate_progressions` at line 891; 4 CLI args at lines 1538-1562; routing at lines 1572-1573 |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `main()` | `calculate_progressions(args)` | `args.progressions` check before `args.timeline` check | WIRED | Lines 1572-1573 (`if args.progressions: return calculate_progressions(args)`) fires before line 1576 (`if args.timeline`) |
| `calculate_progressions()` | `load_natal_profile()` | function call to load natal subject and data | WIRED | Line 908: `natal_subject, natal_data = load_natal_profile(args.progressions)` |
| `calculate_progressions()` | `build_progressed_json()` | function call to assemble complete progressions JSON | WIRED | Lines 968-972: `prog_dict = build_progressed_json(progressed_subject, natal_subject, natal_data, args.progressions, ...)` |
| `build_progressed_json()` | `AspectsFactory.dual_chart_aspects()` | progressed-to-natal aspect calculation with `PROG_DEFAULT_ORBS` | WIRED | Lines 814-820: `AspectsFactory.dual_chart_aspects(progressed_subject, natal_subject, active_points=MAJOR_PLANETS, active_aspects=PROG_DEFAULT_ORBS, second_subject_is_fixed=True)` |
| `build_progressed_json()` | `build_monthly_moon()` | 12-month progressed Moon tracking with sign change detection | WIRED | Line 835: `monthly_moon = build_monthly_moon(birth_jd, prog_year, natal_lat, natal_lng, natal_tz_str)` |

### Requirements Coverage

No REQUIREMENTS.md entries mapped to phase 09.

### Anti-Patterns Found

None. No TODO/FIXME/PLACEHOLDER/stub patterns found in the modified file. All functions have substantive implementations.

### Human Verification Required

None. All success criteria are verifiable programmatically via CLI output and code inspection.

---

## Implementation Details

### Key Behaviors Confirmed

- **Day-for-a-year formula:** `compute_progressed_jd` at line 657 uses `birth_jd + (target_jd - birth_jd) / 365.25` — exact formula from plan
- **Natal location used for progressed subject:** Line 949-955 uses `natal_lat`, `natal_lng`, `natal_tz` (not `lat=0.0, lng=0.0`) — critical distinction from transit mode
- **1-degree orbs only:** `PROG_DEFAULT_ORBS` constant (line 98-104) has orb=1 for all 5 aspects; live output confirms max_orb=1.0
- **Mutual exclusion enforced:** `--age` + `--target-date` together returns exit code 1 with stderr message "Cannot use both --age and --target-date"
- **Missing profile handled:** `--progressions nonexistent-person` returns exit code 1 with clear error message
- **Commit documented:** `2871fa9` verified present in git log

### Regression Verification

| Mode | Expected chart_type | Actual | Status |
|------|--------------------|----|--------|
| `--transits albert-einstein` | `transit_snapshot` | `transit_snapshot` | PASS |
| `--timeline albert-einstein --range week` | `transit_timeline` | `transit_timeline` | PASS |
| `--list` | Lists profiles | 8 profiles listed, exit 0 | PASS |

---

_Verified: 2026-02-17T04:40:00Z_
_Verifier: Claude (gsd-verifier)_
