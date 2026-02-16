# Features Research: generate-natal-chart

## Table Stakes (Must Have)

Features users expect from any natal chart tool:

| Feature | Description | Complexity | Dependencies |
|---------|-------------|------------|--------------|
| **Accurate planetary positions** | Sun, Moon, Mercury through Pluto positions by sign and degree | Low | Kerykeion core |
| **House calculations** | All 12 houses with cusps using Placidus system | Low | Kerykeion core |
| **Aspect calculations** | Major aspects (conjunction, opposition, trine, square, sextile) with orbs | Low | Planetary positions |
| **Angles** | Ascendant, Midheaven, Descendant, IC | Low | Birth time + location |
| **Birth data validation** | Verify date, time, location are valid before calculating | Low | None |
| **SVG chart visual** | Traditional wheel chart showing planets, signs, houses, aspects | Low | Kerykeion SVG |
| **JSON data export** | Structured data file with all calculated positions | Medium | All calculations |
| **Geocoding** | Convert city name to coordinates | Low | Kerykeion GeoNames |
| **Profile storage** | Save chart to named folder for later retrieval | Low | File system |
| **Profile listing** | List all saved charts | Low | File system |

## Differentiators (Competitive Advantage)

What makes this skill special vs generic chart tools:

| Feature | Description | Complexity | Dependencies |
|---------|-------------|------------|--------------|
| **Claude context loading** | Load full natal chart JSON into active conversation for AI interpretation | Medium | JSON export, Claude Code skill |
| **Astrologer guide prompt** | Interpretation framework that teaches Claude how to read the chart data astrologically | Medium | Domain expertise |
| **Smart routing** | Single command handles create, list, and load flows based on arguments | Medium | Argument parsing |
| **Maximum data depth** | Asteroids (Chiron, Lilith, Juno, Ceres, Pallas, Vesta), minor aspects, retrograde status, element/modality distribution | High | Kerykeion extended features |
| **Fixed stars** | Conjunctions to major fixed stars (Regulus, Algol, Spica, etc.) | High | Additional calculation |
| **Arabic parts** | Part of Fortune, Part of Spirit | Medium | Planetary positions + houses |
| **Dignity/debility** | Essential dignities (domicile, exaltation, detriment, fall) for each planet | Medium | Planet + sign data |
| **Overwrite protection** | Warn before replacing existing profile | Low | File system check |

## Anti-Features (Deliberately NOT Building)

| Feature | Why Not |
|---------|---------|
| **Synastry/compatibility** | Significant complexity increase — deferred to v2 |
| **Transit charts** | Requires real-time ephemeris data, different calculation model — v2 |
| **Progression charts** | Secondary progressions, solar arc — v2 |
| **Custom SVG styling** | Kerykeion default is sufficient, custom theming is scope creep |
| **Web UI** | This is a CLI skill, not a web app |
| **Horoscope text generation** | Claude generates interpretations from raw data — no need to pre-generate |
| **Chart comparison overlay** | Requires multi-chart support — v2 with synastry |
| **Ephemeris browser** | Out of scope — this is a chart generator, not an ephemeris tool |

## Feature Dependencies

```
Birth data validation
  → Geocoding (needs valid location)
    → Kerykeion calculation (needs coordinates + time)
      → Planetary positions
      → House cusps
      → Angles
        → Aspect calculations (needs positions)
        → Dignity calculations (needs planet + sign)
        → Element/modality distribution (needs all placements)
        → Arabic parts (needs ASC + planets)
          → JSON export (needs all data)
          → SVG generation (needs all data)
            → Profile storage (needs JSON + SVG files)
              → Context loading (needs stored JSON)
              → Astrologer guide prompt (needs loaded JSON)
```

## Complexity Assessment

**Overall: Medium**

The core calculation is handled by Kerykeion — the real complexity is in:
1. **JSON structure design** — comprehensive enough for deep interpretation, well-organized
2. **Astrologer guide prompt** — requires real astrological domain expertise to write well
3. **Extended data extraction** — asteroids, fixed stars, Arabic parts may require going beyond Kerykeion's basic API
4. **Claude Code skill routing** — parsing arguments and managing three distinct flows in a single command
