# generate-natal-chart

## What This Is

A global Claude Code agent skill that generates full natal (birth) charts and predictive astrology (transits, timelines, secondary progressions, solar arc directions) using the Kerykeion Python library, stores structured chart data as profiles, and loads them into active chat context with expert interpretation guides — enabling Claude to act as a hyper-specific astrological advisor based on real calculated positions.

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
- ✓ Current transit snapshots against natal charts with configurable orbs, house placement, retrograde, applying/separating — v1.1
- ✓ Transit timelines with preset (week/30d/3m/year) and custom date ranges with exact hit detection — v1.1
- ✓ Secondary progressions (day-for-a-year) with progressed aspects, monthly Moon, distribution shifts — v1.1
- ✓ Solar arc directions with true arc (default) and mean arc methods — v1.1
- ✓ Auto-load transits on chart open with predictive interpretation guide — v1.1
- ✓ Skill routing for targeted predictive queries — v1.1
- ✓ Snapshot storage with --save flag for all 4 predictive modes — v1.1

### Active

(No active requirements — next milestone not yet defined)

### Out of Scope

- Multi-chart synastry/compatibility analysis — deferred to v2
- Solar/lunar return charts — deferred to v2
- Transit alerts/notifications — requires scheduling infrastructure beyond CLI scope
- Custom SVG styling — using Kerykeion defaults
- OAuth/API-based chart sources — local calculation only
- Mobile or web UI — Claude Code CLI only
- Configurable house systems — Placidus only
- Minor aspects for transits — low signal-to-noise
- Real-time updating transits — no benefit for CLI tool

## Context

Shipped v1.1 with 2,360 LOC Python (backend/astrology_calc.py).
Tech stack: Python 3.11, Kerykeion 5.7.2, python-slugify, pyswisseph (Swiss Ephemeris).
Skill installed at ~/.claude/skills/natal-chart/SKILL.md (537 lines).
Chart profiles stored at ~/.natal-charts/{slug}/.
13 phases completed across 2 milestones (v1.0 + v1.1) in ~1 hour total execution time.

**Capabilities:**
- Natal chart generation (planets, houses, aspects, angles, asteroids, fixed stars, Arabic parts, dignities)
- Current transit snapshots with aspect analysis
- Transit timelines with exact hit detection
- Secondary progressions with monthly Moon tracking
- Solar arc directions with true/mean arc methods
- Snapshot persistence for all predictive modes
- Automatic transit loading on chart open
- Expert interpretation guides for natal and predictive astrology

## Constraints

- **Python dependency**: Kerykeion must be installed (`pip install kerykeion`) — skill should check and prompt if missing
- **Storage**: All chart data stored locally in ~/.natal-charts/ — no cloud dependencies
- **Geocoding**: Relies on Kerykeion's GeoNames integration — requires internet for location lookup during chart creation
- **Skill location**: Global Claude Code skill in ~/.claude/skills/ directory
- **Birth time**: Strictly required — no partial chart generation without exact time
- **Monolithic backend**: Single 2,360-line Python file — manageable for current scope but consider splitting if v2 adds significantly

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
| Monolithic backend | Single Python file for simplicity (1,070 → 2,360 LOC across v1.0-v1.1) | ✓ Good |
| Non-interactive confirmation | Exit codes + --force flag for Claude Code skill compatibility | ✓ Good |
| Transit subject at lat=0.0 lng=0.0 UTC | Geocentric positioning eliminates location bias for transit calculations | ✓ Good |
| Tighter transit orbs (3/3/2/2/1) | Avoids noise in transit interpretation vs natal orbs | ✓ Good |
| True arc default for solar arcs | More accurate than Naibod constant due to seasonal Sun speed variation | ✓ Good |
| Transit auto-load only (not progressions) | Avoids context overload — transits are most time-relevant | ✓ Good |
| save_snapshot() with stderr-only confirm | Preserves JSON parsability of stdout when --save is used | ✓ Good |
| Single SKILL.md for all modes | No separate predictive guide file — consistent with v1.0 inline pattern | ✓ Good |

---
*Last updated: 2026-02-17 after v1.1 milestone completion*
