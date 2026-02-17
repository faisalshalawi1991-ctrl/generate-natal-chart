---
phase: 08-transit-timelines
plan: 01
subsystem: api
tags: [kerykeion, transit-timeline, ephemeris, aspect-detection, python-cli]

# Dependency graph
requires:
  - phase: 07-current-transit-snapshots
    provides: load_natal_profile(), TRANSIT_DEFAULT_ORBS, MAJOR_PLANETS constants, and transit routing pattern in main()
provides:
  - --timeline SLUG CLI mode with week/30d/3m/year presets and custom --start/--end ranges
  - parse_preset_range() for converting preset strings to UTC noon datetime pairs
  - build_timeline_events() for Applying->Separating exact hit detection from TransitsTimeRangeModel
  - build_timeline_json() for assembling complete timeline JSON with meta and events sections
  - calculate_timeline() orchestrating EphemerisDataFactory + TransitsTimeRangeFactory pipeline
affects: [09-progressions, 10-solar-arcs, 11-interpretation-guide]

# Tech tracking
tech-stack:
  added: [EphemerisDataFactory (kerykeion 5.7.2), TransitsTimeRangeFactory (kerykeion 5.7.2)]
  patterns:
    - "EphemerisDataFactory with lat=0.0/lng=0.0/tz_str='Etc/UTC' for geocentric location-independent ephemeris"
    - "TransitsTimeRangeFactory with explicit TRANSIT_DEFAULT_ORBS and MAJOR_PLANETS (not defaults)"
    - "Applying->Separating transition scan for exact hit event detection"
    - "timedelta fixed-day approximations for preset ranges (no dateutil dependency)"

key-files:
  created: []
  modified: [backend/astrology_calc.py]

key-decisions:
  - "EphemerisDataFactory uses lat=0.0/lng=0.0/tz_str='Etc/UTC' not natal chart location (transit ecliptic positions are location-independent)"
  - "Year preset uses timedelta(days=364) = 365 inclusive days, avoiding dateutil dependency"
  - "Custom range validated at <=365 days before factory call for cleaner error message than EphemerisDataFactory's 730-day limit"
  - "Exact hit = last Applying day before Separating/Static transition (day-resolution is sufficient for transit timelines)"
  - "sampling_note in meta documents Moon daily-resolution limitation inline with data"

patterns-established:
  - "Timeline routing in main() via if args.timeline before if args.transits (same early-return pattern)"
  - "build_timeline_events() uses defaultdict(list) to track (transit, aspect, natal) triples, then consecutive-pair scan"
  - "Events list is flat and chronological (sorted by date string) for easy Claude context reasoning"

# Metrics
duration: 8min
completed: 2026-02-17
---

# Phase 8 Plan 01: Transit Timelines Summary

**Transit timeline generation via `--timeline SLUG` using EphemerisDataFactory + TransitsTimeRangeFactory with Applying->Separating exact hit detection, outputting chronological event JSON across 4 preset ranges (week/30d/3m/year) and custom date ranges**

## Performance

- **Duration:** 8 min
- **Started:** 2026-02-17T03:48:24Z
- **Completed:** 2026-02-17T03:56:00Z
- **Tasks:** 2 (1 implementation + 1 verification)
- **Files modified:** 1

## Accomplishments

- Added `--timeline SLUG` CLI mode with `--range {week,30d,3m,year}` and `--start`/`--end` custom range arguments
- Implemented Applying->Separating exact hit detection via `build_timeline_events()` — 400 events detected for Einstein year range, all correctly sorted and within 3.0 deg orb limit
- Zero regressions to existing `--transits`, `--list`, and natal chart creation modes

## Task Commits

Each task was committed atomically:

1. **Task 1: Add timeline functions, CLI arguments, and main() routing** - `9c8552f` (feat)
2. **Task 2: End-to-end timeline verification** - No code changes (verification only)

**Plan metadata:** (pending docs commit)

## Files Created/Modified

- `backend/astrology_calc.py` - Added 2 new imports (EphemerisDataFactory, TransitsTimeRangeFactory), timedelta, defaultdict; 4 new functions (parse_preset_range, build_timeline_events, build_timeline_json, calculate_timeline); 4 new CLI args; timeline routing in main()

## Decisions Made

- Used `lat=0.0, lng=0.0, tz_str='Etc/UTC'` for EphemerisDataFactory — transit planet ecliptic positions depend only on UTC Julian Day, not observer location. Using natal chart location would introduce sub-degree offsets.
- Chose `timedelta` fixed-day approximations over `dateutil.relativedelta` — no new dependency, 89-day approximation for 3m is standard industry practice for transit timelines.
- Custom range validated at <=365 days in `calculate_timeline()` before calling `EphemerisDataFactory` — provides cleaner error message than the factory's 730-day limit exception.
- Reported "last Applying day" as exact hit date — day-resolution is appropriate and sufficient for transit timelines; sub-day precision not required.
- Added `sampling_note` field in meta to document Moon fast-aspect limitation inline with data.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Timeline foundation complete with chronological event JSON output
- `parse_preset_range()`, `build_timeline_events()`, `build_timeline_json()`, and `calculate_timeline()` all ready for Phase 9+ reuse if needed
- The flat chronological events list structure is well-suited for Claude context loading and temporal reasoning

---
*Phase: 08-transit-timelines*
*Completed: 2026-02-17*
