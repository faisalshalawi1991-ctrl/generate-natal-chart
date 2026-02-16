---
phase: 02-core-calculation-engine
plan: 01
subsystem: calculation
tags: [kerykeion, swiss-ephemeris, astrology, geonames, argparse, validation]

# Dependency graph
requires:
  - phase: 01-foundation-setup
    provides: Python backend environment with kerykeion library installed and basic CLI scaffold
provides:
  - Dual-mode location handling (GeoNames online + offline coordinates)
  - Complete natal chart calculation extraction (planets, houses, angles, aspects)
  - Enhanced input validation (dates, birth time, location modes)
  - Full astrological data output formatting
affects: [03-chart-generation, 04-claude-integration]

# Tech tracking
tech-stack:
  added: [NatalAspects class from kerykeion, KerykeionException handling, os module]
  patterns: [Dual-mode location pattern, argparse type validation, safe attribute access with getattr]

key-files:
  created: []
  modified: [backend/astrology_calc.py]

key-decisions:
  - "Changed year range validation from 1900-current to 1800-current to support historical dates (Swiss Ephemeris supports antiquity)"
  - "Filter aspects to only major types (conjunction, opposition, trine, square, sextile) between 10 main planets (exclude nodes, Chiron, Lilith, angles)"
  - "Use Placidus house system (P) as default with verification after subject creation"

patterns-established:
  - "Location validation: must provide either (city/nation) OR (lat/lng/tz), not both, not neither"
  - "GeoNames error handling: catch KerykeionException, display clear error with details and tip"
  - "Safe retrograde detection: use getattr(planet, 'retrograde', False) for backward compatibility"

# Metrics
duration: 4min
completed: 2026-02-16
---

# Phase 2 Plan 01: Core Calculation Engine Summary

**Dual-mode natal chart calculator with GeoNames geocoding, full planetary/house/angle/aspect extraction, and comprehensive input validation**

## Performance

- **Duration:** 4 minutes
- **Started:** 2026-02-16T12:41:26Z
- **Completed:** 2026-02-16T12:45:26Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments
- Dual-mode location handling: GeoNames online lookup (city/nation) and offline coordinates (lat/lng/tz)
- Complete natal chart calculations: 10 planets, 12 houses (Placidus), 4 angles, major aspects with orbs
- Enhanced validation: date range (1800-current year), birth time required, location mode validation
- Clear error messages for GeoNames failures, invalid dates, missing arguments

## Task Commits

Each task was committed atomically:

1. **Task 1: Add dual-mode location handling and enhanced input validation** - `37d8c35` (feat)
2. **Task 2: Extract and display full natal chart calculations** - `1b96443` (feat)

## Files Created/Modified
- `backend/astrology_calc.py` - Complete natal chart CLI with dual-mode location, full calculation output, and comprehensive validation

## Decisions Made
- **Year range 1800-current:** Changed from plan's 1900-current to support historical dates like Einstein (1879). Swiss Ephemeris supports dates back to antiquity, so 1800 is a reasonable lower bound while still preventing clearly invalid dates.
- **Aspect filtering:** Filter aspects to only show major types (conjunction, opposition, trine, square, sextile) between the 10 main planets. Exclude nodes, Chiron, Lilith, and angles from aspect list to match standard astrological practice.
- **Placidus verification:** Add warning to stderr if houses_system_identifier is not 'P' after subject creation to catch any unexpected house system changes.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Year range validation conflicted with verification test**
- **Found during:** Task 1 (Enhanced input validation)
- **Issue:** Plan specified 1900-current year range, but verification test used Einstein's birth date (1879), which is before 1900. This created a conflict where the test would fail even though it should pass.
- **Fix:** Changed year range from 1900-current to 1800-current. Swiss Ephemeris (used by Kerykeion) supports historical dates back to antiquity, so 1800 is a reasonable lower bound while still preventing clearly invalid dates.
- **Files modified:** backend/astrology_calc.py
- **Verification:** Einstein test (1879) now passes, future dates (2099) still rejected, exit codes correct
- **Committed in:** 37d8c35 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug fix)
**Impact on plan:** Auto-fix was necessary to resolve conflict between plan requirement and verification test. The 1800 lower bound is more appropriate for astrological calculations while still providing reasonable validation. No scope creep.

## Issues Encountered
None - plan executed smoothly with one bug fix for year range validation.

## User Setup Required

None - no external service configuration required.

GeoNames online mode works with Kerykeion's default shared username (limited to 2000 requests/hour). Users can optionally set `KERYKEION_GEONAMES_USERNAME` environment variable with their own free GeoNames account for unlimited requests, but this is not required for basic functionality.

## Next Phase Readiness
- Core calculation engine complete and verified
- All 10 phase success criteria from ROADMAP.md met:
  1. 10 planetary positions with sign, degree accuracy ✓
  2. 12 house cusps using Placidus system ✓
  3. Major aspects with correct orbs ✓
  4. 4 angles with sign and degree ✓
  5. Retrograde status identified ✓
  6. Invalid calendar dates rejected ✓
  7. Birth time required ✓
  8. Location resolves via GeoNames ✓
  9. Resolved city/country displayed ✓
  10. GeoNames failures produce clear errors ✓
- Ready for Phase 3 (Chart Generation) to build SVG output on top of this calculation foundation

---
*Phase: 02-core-calculation-engine*
*Completed: 2026-02-16*

## Self-Check: PASSED

Verified files and commits:
- ✓ backend/astrology_calc.py exists
- ✓ Commit 37d8c35 exists (Task 1)
- ✓ Commit 1b96443 exists (Task 2)
