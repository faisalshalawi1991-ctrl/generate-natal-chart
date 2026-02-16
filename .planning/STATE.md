# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-16)

**Core value:** Load a person's complete natal chart data into Claude's context so it can answer deeply specific questions about life path, psychology, and astrological patterns based on real calculated positions — not generic horoscopes.
**Current focus:** Phase 5: Claude Code Skill Layer

## Current Position

Phase: 5 of 6 (Claude Code Skill Layer)
Plan: 1 of 1 in current phase (05-01 complete)
Status: Phase 05 complete
Last activity: 2026-02-16 — Completed 05-01-PLAN.md (Natal Chart Skill Definition)

Progress: [████████▓░] 85%

## Performance Metrics

**Velocity:**
- Total plans completed: 7
- Average duration: 4.0 minutes
- Total execution time: 0.47 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01    | 1     | 6m    | 6m       |
| 02    | 1     | 4m    | 4m       |
| 03    | 2     | 8m    | 4m       |
| 04    | 2     | 8m    | 4m       |
| 05    | 1     | 3m    | 3m       |

**Recent Trend:**
- Last 5 plans: 03-02 (6m), 04-01 (4m), 04-02 (4m), 05-01 (3m)
- Trend: Improving velocity (3m for latest plan)

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Kerykeion over Flatlib: Built-in SVG generation, active maintenance, broader feature set
- Placidus house system: Most widely used in Western astrology, Kerykeion default
- Require exact birth time: Accuracy matters for house/angle calculations
- Guide prompt on load: Transforms raw data into interpretive framework for Claude
- **01-01:** Use Python 3.11 instead of 3.13 for compatibility with pyswisseph prebuilt wheels
- **01-01:** Pin only kerykeion==5.7.2, let pip resolve transitive dependencies automatically
- **02-01:** Year range 1800-current instead of 1900-current to support historical dates (Swiss Ephemeris supports antiquity)
- **02-01:** Filter aspects to major types between 10 main planets (exclude nodes, Chiron, Lilith, angles)
- **03-01:** Use 3-letter sign abbreviations (Ari, Tau, Gem) to match Kerykeion output format
- **03-01:** Enable asteroids via active_points parameter in AstrologicalSubjectFactory
- **03-01:** Day/night chart detection using Sun's house position (7-12 = day, 1-6 = night)
- **03-01:** Traditional planets only (Sun-Saturn) for dignities due to disputed modern planet assignments
- **03-02:** Swiss Ephemeris fixstar2_ut() for accurate fixed star positions with Kerykeion's bundled ephemeris data
- **03-02:** Use abs_pos attribute for absolute ecliptic longitude (position is within-sign only)
- **03-02:** 11 placements for element/modality distributions (10 planets + ASC)
- **03-02:** Display planet names per category for immediate interpretive value
- **04-01:** Dict construction instead of model_dump() for complete control over JSON structure including Phase 3 extended calculations
- **04-01:** Optional --output-dir flag maintains backward compatibility while enabling file output mode
- **04-01:** ChartDataFactory with fallback to direct subject approach handles Kerykeion API variations gracefully
- **04-01:** Add python-slugify to requirements now (needed by Plan 02) to consolidate dependency management
- **04-02:** Non-interactive overwrite protection using --force flag instead of input() for Claude Code skill compatibility
- **04-02:** Automatic profile storage on every chart generation (removed optional --output-dir, always save to ~/.natal-charts/{slug}/)
- **04-02:** Display existing birth data before rejecting overwrite to help users verify profile identity
- **05-01:** Direct interpreter path (./venv/Scripts/python) in skill ensures project venv usage regardless of system Python config
- **05-01:** SKILL-INSTALLATION.md reference document tracks skill installations outside repository

### Pending Todos

None yet.

### Blockers/Concerns

None yet.

## Session Continuity

Last session: 2026-02-16T14:40:44Z
Stopped at: Completed Phase 05 Plan 01 (Natal Chart Skill Definition)
Resume file: .planning/phases/05-claude-code-skill-layer/05-01-SUMMARY.md
