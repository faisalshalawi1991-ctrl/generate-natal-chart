# generate-natal-chart

## What This Is

A global Claude Code agent skill that generates full natal (birth) charts using the Kerykeion Python library, stores structured chart data as profiles, and loads them into active chat context with an expert interpretation guide — enabling Claude to act as a hyper-specific astrological advisor based on real calculated positions.

## Core Value

Load a person's complete natal chart data into Claude's context so it can answer deeply specific questions about life path, psychology, and astrological patterns based on real calculated positions — not generic horoscopes.

## Requirements

### Validated

- ✓ Generate full natal chart from birth date, time, and location using Kerykeion — v1.0
- ✓ Produce visual SVG chart using Kerykeion's default SVG generation — v1.0
- ✓ Produce structured JSON with maximum data depth (planets, houses, aspects, angles, elements, modalities, retrogrades, asteroids, fixed stars, Arabic parts, dignities) — v1.0
- ✓ Store chart profiles in ~/.natal-charts/{name}/ subfolders (chart.json + chart.svg) — v1.0
- ✓ Smart routing: birth details → create; no args → list/load profiles — v1.0
- ✓ Load chart JSON into Claude's active context on creation and on demand — v1.0
- ✓ Inject astrologer interpretation guide alongside raw JSON on load — v1.0
- ✓ List existing chart profiles when invoked without arguments — v1.0
- ✓ Warn and confirm before overwriting existing profile — v1.0
- ✓ Require exact birth time — no partial charts — v1.0
- ✓ Placidus house system as default — v1.0
- ✓ Kerykeion GeoNames lookup for location resolution — v1.0
- ✓ Slash command wrapper as Claude Code skill in ~/.claude/ — v1.0

### Active

(None — next milestone not yet planned)

### Out of Scope

- Multi-chart synastry/compatibility analysis — deferred to v2
- Custom SVG styling — using Kerykeion defaults
- OAuth/API-based chart sources — local calculation only
- Mobile or web UI — Claude Code CLI only
- Configurable house systems — Placidus only for v1
- Transit charts or progressions — natal only for v1
- Offline mode — GeoNames required for city lookup

## Context

Shipped v1.0 with 1,070 LOC Python (backend/astrology_calc.py).
Tech stack: Python 3.11, Kerykeion 5.7.2, python-slugify, pyswisseph.
Skill installed at ~/.claude/skills/natal-chart/SKILL.md.
Chart profiles stored at ~/.natal-charts/{slug}/.
All 36 requirements satisfied across 6 phases in ~30 minutes execution time.

## Constraints

- **Python dependency**: Kerykeion must be installed (`pip install kerykeion`) — skill should check and prompt if missing
- **Storage**: All chart data stored locally in ~/.natal-charts/ — no cloud dependencies
- **Geocoding**: Relies on Kerykeion's GeoNames integration — requires internet for location lookup during chart creation
- **Skill location**: Global Claude Code skill in ~/.claude/skills/ directory
- **Birth time**: Strictly required — no partial chart generation without exact time

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Kerykeion over Flatlib | Built-in SVG generation, active maintenance, broader feature set | ✓ Good |
| Subfolders per person | Clean organization, room for future multi-chart types per person | ✓ Good |
| Placidus house system | Most widely used in Western astrology, Kerykeion default | ✓ Good |
| Require exact birth time | Accuracy matters for house/angle calculations — partial charts mislead | ✓ Good |
| Guide prompt on load | Transforms raw data into interpretive framework for Claude | ✓ Good |
| Maximum JSON depth | Asteroids, fixed stars, Arabic parts — comprehensive analysis capability | ✓ Good |
| Python 3.11 over 3.13 | Compatibility with pyswisseph prebuilt wheels | ✓ Good |
| Monolithic backend | Single 1,070-line Python file for simplicity | ✓ Good |
| Non-interactive confirmation | Exit codes + --force flag for Claude Code skill compatibility | ✓ Good |
| Traditional planets for dignities | Modern planet dignities disputed in astrological community | ✓ Good |
| Swiss Ephemeris for fixed stars | fixstar2_ut() for accurate positions with bundled ephemeris data | ✓ Good |
| Direct venv interpreter path | ./venv/Scripts/python in skill ensures correct Python environment | ✓ Good |

---
*Last updated: 2026-02-16 after v1.0 milestone*
