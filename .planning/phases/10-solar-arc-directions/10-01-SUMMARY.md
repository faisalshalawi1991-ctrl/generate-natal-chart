---
phase: 10-solar-arc-directions
plan: 01
subsystem: api
tags: [swisseph, astrology, solar-arcs, python, kerykeion]

# Dependency graph
requires:
  - phase: 09-secondary-progressions
    provides: compute_progressed_jd() for true arc JD arithmetic, load_natal_profile() for chart.json loading, routing pattern in main()
  - phase: 07-current-transit-snapshots
    provides: MAJOR_PLANETS constant, position_to_sign_degree() function, load_natal_profile() function

provides:
  - Solar arc directions calculation via --solar-arcs SLUG CLI flag
  - True arc method (default): actual progressed Sun position via swe.calc_ut at progressed JD
  - Mean arc (Naibod) method: elapsed_years * 0.98564733 constant rate
  - Directed positions for all 10 major planets and ASC/MC
  - SA-to-natal aspects with 1-degree orb, sorted by orb, with applying/separating detection
  - Optional --target-date YYYY-MM-DD, --age N (shared with progressions, no redefinition)
  - --arc-method [true|mean] flag to switch between calculation methods

affects:
  - phase 11 (skill layer) and beyond — skill layer will route --solar-arcs alongside existing modes

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Solar arc routing in main() before --progressions check (newest mode first convention)
    - Manual aspect calculation via nested loop (no AspectsFactory — directed positions are not Kerykeion subjects)
    - Directed position as pure arithmetic: (natal_lon + arc) % 360 — no from_birth_data() calls
    - compute_solar_arc() reuses compute_progressed_jd() from Phase 9 for true arc JD lookup
    - Applying/separating detection via 1-year forward orb comparison
    - SARC_DEFAULT_ORBS as plain dict (not ActiveAspect list) — manual calculation, not AspectsFactory

key-files:
  created: []
  modified:
    - backend/astrology_calc.py

key-decisions:
  - "True arc is default (more accurate); mean arc (Naibod 0.98564733) available via --arc-method mean"
  - "Self-aspects excluded from build_sarc_aspects() — directed_point == natal_point comparisons are redundant"
  - "Applying/separating via 1-year forward arc comparison — orb decreases = Applying, orb increases = Separating"
  - "No AspectsFactory for SA aspects — directed positions are plain float dicts, not Kerykeion subjects"
  - "1.0 degree orb for all SA aspects (SARC_DEFAULT_ORBS plain dict) — Noel Tyl professional standard"
  - "SIGN_OFFSETS needed to reconstruct house cusp abs_positions — houses lack abs_position in chart.json"

patterns-established:
  - "Solar arc routing: args.solar_arcs check fires before --progressions check (order: --list, --solar-arcs, --progressions, --timeline, --transits)"
  - "angular_distance() helper: diff = abs(lon1 - lon2) % 360; return 360-diff if diff > 180 else diff — handles zodiac wrap-around"
  - "build_sarc_aspects(): nested loop on plain float dicts, skip d_name==n_name, sort by orb — reusable for any manual aspect calculation"
  - "movement detection: arc_future = compute_solar_arc(birth_jd, target_jd + 365.25, ...) — compare orb vs orb_future"

# Metrics
duration: 3min
completed: 2026-02-17
---

# Phase 10 Plan 01: Solar Arc Directions Summary

**Solar arc directions via swe.calc_ut true arc (default) and Naibod mean arc, outputting directed positions for 10 planets + ASC/MC with manually-computed SA-to-natal aspects (1-degree orb) and applying/separating detection — verified against Einstein reference values (true arc 141.935, mean arc 144.821 at 2026-02-17).**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-02-17T04:53:58Z
- **Completed:** 2026-02-17T04:57:50Z
- **Tasks:** 2 (1 implementation + 1 verification)
- **Files modified:** 1

## Accomplishments
- Added SARC_DEFAULT_ORBS, NAIBOD_ARC, SARC_ASPECT_ANGLES, SIGN_OFFSETS constants
- Added 5 new functions: compute_solar_arc(), angular_distance(), build_sarc_aspects(), build_solar_arc_json(), calculate_solar_arcs()
- Added 2 new CLI arguments: --solar-arcs SLUG, --arc-method [true|mean]
- Verified Einstein 2026-02-17: true arc 141.935 (research says 141.935), mean arc 144.821 (research says 144.821), 6 aspects within 1-degree orb matching all 6 research-verified aspects exactly
- Verified applying/separating detection: all 6 Einstein aspects correctly detected as Separating
- Zero regressions across --list, --transits, --timeline, --progressions, and natal chart creation

## Task Commits

Each task was committed atomically:

1. **Task 1: Add solar arc constants, functions, CLI arguments, and main() routing** - `1148787` (feat)
2. **Task 2: End-to-end solar arc verification against research reference values** - no code changes (all verified PASS)

**Plan metadata:** (to be added with final commit)

## Files Created/Modified
- `backend/astrology_calc.py` - Added 331 lines: 4 new constants, 5 new functions, 2 new CLI args, solar arcs routing in main()

## Decisions Made
- True arc is default method using swe.calc_ut on progressed JD — more accurate than Naibod constant since Sun's daily speed varies ~7% seasonally
- Self-aspects excluded from aspect output — a planet directing to its own natal position is redundant, not a meaningful aspect in SA practice
- Applying/separating detection uses 1-year forward comparison (orb at target_jd + 365.25) — simple and reliable for SA timing analysis
- No AspectsFactory — SA directed positions are plain float dicts, not Kerykeion AstrologicalSubjectModel instances; manual nested loop is simpler and correct
- 1.0-degree orb for all 5 aspects (SARC_DEFAULT_ORBS plain dict) — Noel Tyl professional standard; 1 degree = approximately 1-year timing window in SA
- natal_degree field reads from planet['degree'] not planet['position'] — the chart.json stores degree-within-sign as 'degree' key

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed natal_degree field using wrong key name**
- **Found during:** Task 1 (initial verification of JSON output)
- **Issue:** Code used `natal_p.get('position', 0.0)` but chart.json stores degree-within-sign as `degree` key — all natal_degree values showed 0.0
- **Fix:** Changed to `natal_p.get('degree', 0.0)` — Einstein Sun correctly shows 23.5 (Pis 23.5)
- **Files modified:** backend/astrology_calc.py
- **Verification:** natal_degree shows 23.5 for Einstein Sun (matches chart.json degree: 23.498...)
- **Committed in:** `1148787` (part of Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug — wrong dict key for degree-within-sign)
**Impact on plan:** Minor field naming fix caught during first test run. No scope creep.

## Issues Encountered

None. Swiss Ephemeris API worked exactly as documented in research. compute_progressed_jd() reuse from Phase 9 was seamless. Manual aspect calculation approach was simpler than AspectsFactory-based approach (no subject creation needed). All reference values matched within tolerance.

## User Setup Required

None - no external service configuration required. Solar arc directions work fully offline using Swiss Ephemeris data bundled with Kerykeion.

## Next Phase Readiness
- Solar arc directions complete, verified end-to-end with Einstein reference data
- All v1.1 predictive technique routing patterns now established: --list, --solar-arcs, --progressions, --timeline, --transits
- angular_distance() and build_sarc_aspects() are reusable helpers for any future manual aspect calculation
- compute_solar_arc() reusable for any future arc-based calculation

---
*Phase: 10-solar-arc-directions*
*Completed: 2026-02-17*

## Self-Check: PASSED

- backend/astrology_calc.py: FOUND
- .planning/phases/10-solar-arc-directions/10-01-SUMMARY.md: FOUND
- Commit 1148787: FOUND
- compute_solar_arc() function: FOUND
- angular_distance() function: FOUND
- build_sarc_aspects() function: FOUND
- build_solar_arc_json() function: FOUND
- calculate_solar_arcs() function: FOUND
- SARC_DEFAULT_ORBS constant: FOUND
