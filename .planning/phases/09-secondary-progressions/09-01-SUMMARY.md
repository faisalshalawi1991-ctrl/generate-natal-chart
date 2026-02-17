---
phase: 09-secondary-progressions
plan: 01
subsystem: api
tags: [kerykeion, astrology, progressions, swisseph, python]

# Dependency graph
requires:
  - phase: 07-current-transit-snapshots
    provides: load_natal_profile(), AspectsFactory.dual_chart_aspects() pattern, MAJOR_PLANETS constant
  - phase: 08-transit-timelines
    provides: calculate_timeline() routing pattern and early-return convention in main()

provides:
  - Secondary progressions calculation via --progressions SLUG CLI flag
  - Optional --target-date YYYY-MM-DD for any date in 1900-2100 range
  - Optional --age N for age-based target (mutually exclusive with --target-date)
  - Optional --prog-year YYYY to override monthly Moon report year
  - Progressed-to-natal aspect calculation with 1-degree orb (PROG_DEFAULT_ORBS)
  - Monthly progressed Moon positions for 12 months with sign change detection
  - Element and modality distribution shift (natal vs progressed with delta)

affects:
  - phase 10 and beyond (solar arcs, skill layer, interpretation — all build on this progressions pattern)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Progressed subject created at natal location (lat/lng/tz) — distinct from Phase 7 transit lat=0.0/lng=0.0 pattern
    - compute_progressed_jd() using swe.julday + swe.revjul for precise JD arithmetic
    - PROG_DEFAULT_ORBS (1-degree for all aspects) as separate constant from TRANSIT_DEFAULT_ORBS
    - Progressions routing in main() before --timeline check (established early-return order)
    - build_monthly_moon() creates 12 AstrologicalSubjectFactory instances, one per month

key-files:
  created: []
  modified:
    - backend/astrology_calc.py

key-decisions:
  - "Progressed subject uses natal lat/lng/tz (not lat=0.0/lng=0.0) — progressed Ascendant requires birthplace coordinates"
  - "365.25 (Julian year) as divisor for day-for-a-year formula — standard textbook approach, difference from 365.2422 is astrologically negligible"
  - "1-degree orb for all progressed aspects (PROG_DEFAULT_ORBS) — Kepler College standard, prevents aspect noise"
  - "Error if both --age and --target-date provided (exit 1) — avoids ambiguity about which takes precedence"
  - "--prog-year defaults to year portion of target date (or birth_year+age for age-based) — most useful default for monthly Moon report"

patterns-established:
  - "Progressions routing: args.progressions check fires before --timeline and --transits checks"
  - "compute_progressed_jd(): birth_jd + (target_jd - birth_jd) / 365.25 — reusable for solar arcs in Phase 10"
  - "build_monthly_moon(): 12 x from_birth_data() at 1st of each month, prev_sign tracking for sign_change detection"
  - "distribution_shift: inline helper compute_distributions_for_subject() reusing ELEMENT_MAP/MODALITY_MAP"

# Metrics
duration: 12min
completed: 2026-02-17
---

# Phase 9 Plan 01: Secondary Progressions Summary

**Secondary progressions via day-for-a-year Swiss Ephemeris JD arithmetic, outputting 10-planet progressed chart with progressed-to-natal aspects (1-degree orb), 12-month Moon tracking, and element/modality shift analysis.**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-02-17T04:25:57Z
- **Completed:** 2026-02-17T04:37:00Z
- **Tasks:** 2 (1 implementation + 1 verification)
- **Files modified:** 1

## Accomplishments
- Added PROG_DEFAULT_ORBS constant (1-degree orb for all 5 major aspects)
- Added 4 new functions: compute_progressed_jd(), build_monthly_moon(), build_progressed_json(), calculate_progressions()
- Added 4 new CLI arguments: --progressions SLUG, --target-date, --age, --prog-year
- Verified Einstein 2026-02-17: progressed date = 1879-08-08 (matches research verification), 6 aspects within 1-degree orb
- Verified Einstein age 30: progressed date = 1879-04-13 (30 days after birth — matches day-for-year formula)
- Zero regressions to --transits, --timeline, --list, and natal chart creation modes

## Task Commits

Each task was committed atomically:

1. **Task 1: Add progressions constant, functions, CLI arguments, and main() routing** - `2871fa9` (feat)
2. **Task 2: End-to-end progressions verification** - no code changes needed (all verified PASS)

**Plan metadata:** (to be added with final commit)

## Files Created/Modified
- `backend/astrology_calc.py` - Added 384 lines: 1 new constant, 4 new functions, 4 new CLI args, progressions routing in main()

## Decisions Made
- Progressed subject uses natal lat/lng/tz (not lat=0.0/lng=0.0 like transit subjects) — progressed Ascendant and house cusps are location-dependent
- 365.25 (Julian year) as divisor — standard textbook formula; difference from 365.2422 tropical year is < 0.01° per year
- 1-degree orb for all progressed aspects (PROG_DEFAULT_ORBS separate from TRANSIT_DEFAULT_ORBS) — Kepler College standard
- Error if both --age and --target-date provided simultaneously (exit 1) — prevents ambiguous input
- --prog-year defaults to target year portion — most contextually relevant for monthly Moon report

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. The Kerykeion 5.7.2 API worked exactly as documented in the research phase. Swiss Ephemeris JD arithmetic via swe.julday/swe.revjul produced the expected progressed dates. AspectsFactory.dual_chart_aspects with PROG_DEFAULT_ORBS returned 6 correct aspects for Einstein at 2026-02-17. Monthly Moon sign change detection (Ari -> Tau in July 2026) verified correct.

## User Setup Required

None - no external service configuration required. Secondary progressions work fully offline using Swiss Ephemeris data bundled with Kerykeion.

## Next Phase Readiness
- Progressions foundation complete, verified end-to-end with Einstein reference data
- compute_progressed_jd() is directly reusable for solar arcs (Phase 10) — same JD arithmetic, different planets
- load_natal_profile() + calculate_progressions() pattern established for any future progressed-chart modes
- All v1.1 routing patterns now established: --list, --transits, --timeline, --progressions all follow early-return convention

---
*Phase: 09-secondary-progressions*
*Completed: 2026-02-17*

## Self-Check: PASSED

- backend/astrology_calc.py: FOUND
- .planning/phases/09-secondary-progressions/09-01-SUMMARY.md: FOUND
- Commit 2871fa9: FOUND
- calculate_progressions() function: FOUND
- build_progressed_json() function: FOUND
- build_monthly_moon() function: FOUND
- compute_progressed_jd() function: FOUND
- PROG_DEFAULT_ORBS constant: FOUND
