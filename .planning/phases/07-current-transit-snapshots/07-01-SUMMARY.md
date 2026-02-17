---
phase: 07-current-transit-snapshots
plan: 01
subsystem: api
tags: [kerykeion, astrology, transits, ephemeris, python]

# Dependency graph
requires:
  - phase: 01-through-06-foundation
    provides: backend/astrology_calc.py with natal chart creation, --list mode, and profile storage

provides:
  - Transit snapshot calculation via --transits SLUG CLI flag
  - Optional --query-date YYYY-MM-DD for any date in 1900-2100 range
  - Transit-to-natal aspect calculation with default orbs (conj/opp: 3, trine/sq: 2, sextile: 1)
  - Natal house placement for each transiting planet
  - Retrograde status for each transiting planet
  - Applying/separating movement for each transit aspect

affects:
  - phase 08 and beyond (progressions, solar arcs, timelines all build on this transit pattern)

# Tech tracking
tech-stack:
  added:
    - kerykeion.aspects.aspects_factory.AspectsFactory (dual_chart_aspects method)
    - kerykeion.house_comparison.house_comparison_factory.HouseComparisonFactory
    - kerykeion.schemas.kr_models.ActiveAspect (typed aspect orb config)
  patterns:
    - Transit subject created at lat=0.0 lng=0.0 UTC (geocentric, no location bias)
    - TRANSIT_DEFAULT_ORBS list of ActiveAspect TypedDicts for configurable orbs
    - second_subject_is_fixed=True in AspectsFactory.dual_chart_aspects for transit-to-natal
    - load_natal_profile() returns (subject, profile_dict) tuple for reuse in future phases
    - calculate_transits() follows early-return routing pattern identical to --list

key-files:
  created: []
  modified:
    - backend/astrology_calc.py

key-decisions:
  - "Transit subject placed at lat=0.0 lng=0.0 UTC (geocentric) — eliminates location bias for planetary positions"
  - "Default orbs tighter than natal-only: conj/opp 3, trine/sq 2, sextile 1 — avoids noise for transit interpretation"
  - "query_date uses UTC noon (12:00) for consistent mid-day snapshot when date given without time"
  - "load_natal_profile raises FileNotFoundError for missing profiles, sys.exit(1) for parse errors — distinct error types"

patterns-established:
  - "Transit routing: args.transits check fires before natal name validation — prevents spurious argument errors"
  - "dual_chart_aspects with second_subject_is_fixed=True — transit planets move, natal planets are fixed reference"
  - "HouseComparisonFactory(transit, natal).first_points_in_second_houses — transit planets in natal houses"

# Metrics
duration: 7min
completed: 2026-02-17
---

# Phase 7 Plan 01: Current Transit Snapshots Summary

**Transit snapshot calculation added to astrology CLI using Kerykeion AspectsFactory.dual_chart_aspects and HouseComparisonFactory, outputting 10-planet transit JSON with aspects (orbs 3/3/2/2/1), natal house placements, retrograde status, and applying/separating movement.**

## Performance

- **Duration:** ~7 min
- **Started:** 2026-02-17T03:20:00Z
- **Completed:** 2026-02-17T03:27:29Z
- **Tasks:** 2 (1 implementation + 1 verification)
- **Files modified:** 1

## Accomplishments
- Added 4 new functions to astrology_calc.py: valid_query_date, load_natal_profile, build_transit_json, calculate_transits
- Added 2 new CLI arguments: --transits SLUG and --query-date YYYY-MM-DD
- Transit calculation produces full JSON satisfying all 5 TRAN requirements (positions, aspects, house placements, retrograde, applying/separating)
- All existing natal chart creation and --list modes continue working unchanged

## Task Commits

Each task was committed atomically:

1. **Task 1: Add transit snapshot functions and CLI arguments** - `b1df6b9` (feat)
2. **Task 2: End-to-end transit calculation verification** - no code changes needed (all verified PASS)

**Plan metadata:** (to be added with final commit)

## Files Created/Modified
- `backend/astrology_calc.py` - Added 291 lines: 3 new imports, 2 new constants, 4 new functions, 2 new CLI args, transit routing in main()

## Decisions Made
- Transit subject placed at lat=0.0, lng=0.0, UTC — eliminates location bias since planetary positions are geocentric and don't vary by observer location for outer-planet transits
- Default orbs tighter than natal aspects (conj/opp 3, trine/sq 2, sextile 1) to keep transit output focused on significant contacts
- UTC noon (12:00) used when --query-date given without time — consistent mid-day snapshot, avoids day-boundary ambiguity
- AspectsFactory.dual_chart_aspects with second_subject_is_fixed=True — natal chart is the fixed reference, transit planets are moving
- load_natal_profile() returns a (subject, profile_dict) tuple — the profile_dict is available for future phases that may need meta fields

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. The Kerykeion 5.7.2 API worked exactly as documented in the research phase. ActiveAspect orb field accepts int (not float), which matched the plan spec. HouseComparisonFactory.get_house_comparison() returns PointInHouseModel objects with point_name and projected_house_number fields as expected.

## User Setup Required

None - no external service configuration required. Transit calculation works fully offline using the existing Swiss Ephemeris data bundled with Kerykeion.

## Next Phase Readiness
- Transit snapshot foundation is complete and verified end-to-end
- load_natal_profile() and build_transit_json() are reusable patterns for Phase 8+ (progressions, solar arcs)
- The --transits SLUG routing pattern is established for any future date-based query modes
- Skill layer (SKILL.md) will need updating to expose --transits to users (future phase)

---
*Phase: 07-current-transit-snapshots*
*Completed: 2026-02-17*
