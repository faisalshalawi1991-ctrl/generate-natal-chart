# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-17)

**Core value:** Load a person's complete natal chart data into Claude's context so it can answer deeply specific questions about life path, psychology, and astrological patterns based on real calculated positions.

**Current focus:** Phase 11 - Interpretation Guide & Context Injection (v1.1 skill layer)

## Current Position

Phase: 11 of 12 (Interpretation Guide & Context Injection)
Plan: 2 of 2 complete
Status: Phase 11 complete
Last activity: 2026-02-17 — Phase 11 plan 02 executed (transit auto-load cross-references added to all three mode entry points, closing INTG-01)

Progress: [██████████████░░░░░░] 83% (11/12 phases complete, v1.1 near-complete)

## Performance Metrics

**Velocity (v1.0 + v1.1 in progress):**
- Total plans completed: 11
- Average duration: 3.8 minutes
- Total execution time: ~0.83 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1 | 1 | ~5 min | ~5 min |
| 2 | 1 | ~3 min | ~3 min |
| 3 | 2 | ~8 min | ~4 min |
| 4 | 2 | ~6 min | ~3 min |
| 5 | 1 | ~3 min | ~3 min |
| 6 | 1 | ~5 min | ~5 min |
| 7 | 1 | ~7 min | ~7 min |
| 8 | 1 | ~8 min | ~8 min |
| 9 | 1 | ~12 min | ~12 min |
| 10 | 1 | ~3 min | ~3 min |
| 11 | 2 | ~7 min | ~3.5 min |

**Recent Trend:**
- v1.0 execution was extremely fast (30 minutes total for 6 phases, 8 plans)
- v1.1 Phase 7: 7 minutes, clean execution, no deviations
- v1.1 Phase 8: 8 minutes, clean execution, no deviations
- v1.1 Phase 9: 12 minutes, clean execution, no deviations
- v1.1 Phase 10: 3 minutes, clean execution, 1 minor bug fix (wrong dict key)
- v1.1 Phase 11 plan 01: 4 minutes, 1 auto-fixed field path bug in guide
- v1.1 Phase 11 plan 02: 3 minutes, no deviations, closed INTG-01 transit auto-load gap

*Updated: 2026-02-17 after Phase 11 plan 02 completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- **Kerykeion over Flatlib**: Built-in SVG generation, active maintenance, broader feature set (v1.0)
- **Placidus house system**: Most widely used in Western astrology, Kerykeion default (v1.0)
- **Python 3.11 over 3.13**: Compatibility with pyswisseph prebuilt wheels (v1.0)
- **Monolithic backend**: Single 1,070-line Python file for simplicity (v1.0, to extend to ~1,770 LOC in v1.1)
- **Transit subject at lat=0.0 lng=0.0 UTC**: Geocentric positioning eliminates location bias for transit calculations (Phase 7)
- **Tighter transit orbs (3/3/2/2/1)**: Avoids noise in transit interpretation vs natal orbs (Phase 7)
- **UTC noon for query-date**: Consistent mid-day snapshot when date given without time (Phase 7)
- **load_natal_profile returns (subject, profile_dict) tuple**: Both subject and raw data available for future phases (Phase 7)
- **EphemerisDataFactory uses lat=0.0/lng=0.0/Etc/UTC**: Transit ecliptic positions are location-independent (Phase 8)
- **timedelta fixed-day approximations for presets**: No dateutil dependency; 89-day approx for 3m is standard (Phase 8)
- **Custom range validated at <=365 days**: Cleaner error than EphemerisDataFactory 730-day limit (Phase 8)
- **Exact hit = last Applying day before Separating transition**: Day-resolution sufficient for transit timelines (Phase 8)
- **Progressed subject uses natal lat/lng/tz**: Progressed Ascendant requires birthplace coordinates (not lat=0.0 like transits) (Phase 9)
- **365.25 Julian year as day-for-year divisor**: Standard textbook formula; negligible difference from tropical year (Phase 9)
- **PROG_DEFAULT_ORBS = 1-degree for all aspects**: Kepler College standard for progressed-to-natal aspects (Phase 9)
- **Error if both --age and --target-date provided**: Avoids ambiguity; return 1 with stderr message (Phase 9)
- **--prog-year defaults to target year portion**: Most contextually relevant for monthly Moon report (Phase 9)
- **True arc is default for solar arcs**: More accurate than Naibod constant due to seasonal Sun speed variation (Phase 10)
- **Self-aspects excluded from SA aspects**: directed_point == natal_point comparisons are redundant in SA practice (Phase 10)
- **No AspectsFactory for SA aspects**: Directed positions are plain float dicts, not Kerykeion subjects; manual nested loop is correct approach (Phase 10)
- **SARC_DEFAULT_ORBS is plain dict, not ActiveAspect list**: Phase 10 computes aspects manually without AspectsFactory (Phase 10)
- **Applying/separating via 1-year forward orb comparison**: orb_future < orb_now means Applying (Phase 10)
- **Transit auto-load only on chart open**: Only --transits auto-loads (not progressions/solar arcs) — avoids context overload (Phase 11)
- **Bash stdout as transit data**: Predictive JSON is stdout from Bash, not a Read file — consistent with ephemeral computation pattern (Phase 11)
- **Single SKILL.md for all modes**: No separate predictive guide file — consistent with Phase 6 inline pattern (Phase 11)
- **One-line cross-reference per mode section**: Minimal change that closes INTG-01 routing ambiguity without restructuring mode sections (Phase 11 plan 02)

### Pending Todos

None.

### Blockers/Concerns

None. Phase 11 shipped successfully.

**v1.1 architectural patterns established (Phases 7-11):**
- Transit routing in main() via early-return before natal validation (same pattern as --list)
- AspectsFactory.dual_chart_aspects with second_subject_is_fixed=True for transit-to-natal and progressed-to-natal
- HouseComparisonFactory(transit, natal).first_points_in_second_houses for transit planet house lookup
- load_natal_profile() and build_transit_json() are reusable for Phases 9+
- EphemerisDataFactory + TransitsTimeRangeFactory pipeline for time-range transit computation
- build_timeline_events() Applying->Separating scan for exact hit detection
- Flat chronological events list for Claude context reasoning
- compute_progressed_jd() reusable for solar arcs (Phase 10)
- build_monthly_moon() 12-call pattern reusable for any monthly progressed body tracking
- compute_solar_arc() reusable for any arc-based calculation (Phase 10)
- angular_distance() helper reusable for any ecliptic angular distance with wrap-around (Phase 10)
- build_sarc_aspects() manual nested loop pattern reusable for any non-subject aspect calculation (Phase 10)
- SKILL.md auto-load pattern: chart.json Read + --transits Bash on every chart open (Phase 11)
- Intent-to-flag routing table in SKILL.md for all 4 predictive modes (Phase 11)
- Cross-reference pattern: mode-specific loading steps delegate to shared Context Loading section for transit auto-load (Phase 11 plan 02)

## Session Continuity

Last session: 2026-02-17
Stopped at: Phase 11 plan 02 complete — transit auto-load cross-references added to all three mode entry points, closing INTG-01
Next step: Phase 12 (end-to-end v1.1 verification)
