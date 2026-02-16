# generate-natal-chart

## What This Is

A global Claude Code agent skill that generates full natal (birth) charts using the Kerykeion Python library and loads the structured chart data into active chat context, enabling Claude to act as a hyper-specific astrological advisor. The skill lives in `~/.claude/` and is invoked via slash command, intelligently routing between chart creation, profile listing, and context loading.

## Core Value

Load a person's complete natal chart data into Claude's context so it can answer deeply specific questions about life path, psychology, and astrological patterns based on real calculated positions — not generic horoscopes.

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

(None yet — ship to validate)

### Active

<!-- Current scope. Building toward these. -->

- [ ] Generate full natal chart from birth date, time, and location using Kerykeion
- [ ] Produce visual SVG chart using Kerykeion's default SVG generation
- [ ] Produce structured JSON file with maximum data depth (planets, houses, aspects, angles, elements, modalities, retrogrades, minor aspects, asteroids, fixed stars, Arabic parts)
- [ ] Store chart profiles in `~/.natal-charts/{name}/` subfolders (chart.json + chart.svg)
- [ ] Smart routing: birth details provided → create new chart; no args → list/load existing profiles
- [ ] Load chart JSON directly into Claude's active chat context on creation and on demand
- [ ] Inject astrologer interpretation guide prompt alongside raw JSON when loading context
- [ ] List all existing chart profiles with names when invoked without arguments
- [ ] Warn and confirm before overwriting an existing profile
- [ ] Require exact birth time — no fallback to noon or partial charts
- [ ] Use Placidus house system as default
- [ ] Use Kerykeion's built-in GeoNames lookup for location → coordinates resolution
- [ ] Slash command wrapper as a Claude Code skill in `~/.claude/`

### Out of Scope

- Multi-chart synastry/compatibility analysis — deferred to v2
- Custom SVG styling — using Kerykeion defaults
- OAuth/API-based chart sources — local calculation only
- Mobile or web UI — Claude Code CLI only
- Configurable house systems — Placidus only for v1
- Transit charts or progressions — natal only for v1

## Context

- **Kerykeion** is a Python library for astrological calculations. It supports natal charts, SVG generation, and geocoding via GeoNames. Active maintenance, good documentation.
- **Claude Code skills** live in `~/.claude/` and are invoked as slash commands. They can execute bash commands, read files, and inject context into the conversation.
- Chart JSON needs to be comprehensive enough that Claude can answer questions about specific planetary aspects, house placements, dignity/debility, and pattern recognition without needing to recalculate anything.
- The astrologer guide prompt is critical — it transforms raw JSON data into meaningful astrological interpretation by giving Claude the framework to reason about the chart.

## Constraints

- **Python dependency**: Kerykeion must be installed (`pip install kerykeion`) — skill should check and prompt if missing
- **Storage**: All chart data stored locally in `~/.natal-charts/` — no cloud dependencies
- **Geocoding**: Relies on Kerykeion's GeoNames integration — requires internet for location lookup during chart creation
- **Skill location**: Must be a global Claude Code skill in `~/.claude/` directory structure
- **Birth time**: Strictly required — no partial chart generation without exact time

## Key Decisions

<!-- Decisions that constrain future work. Add throughout project lifecycle. -->

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Kerykeion over Flatlib | Built-in SVG generation, active maintenance, broader feature set | — Pending |
| Subfolders per person | Clean organization, room for future multi-chart types per person | — Pending |
| Placidus house system | Most widely used in Western astrology, Kerykeion default | — Pending |
| Require exact birth time | Accuracy matters for house/angle calculations — partial charts mislead | — Pending |
| Guide prompt on load | Transforms raw data into interpretive framework for Claude | — Pending |
| Maximum JSON depth | Asteroids, minor aspects, fixed stars — comprehensive analysis capability | — Pending |

---
*Last updated: 2026-02-16 after initialization*
