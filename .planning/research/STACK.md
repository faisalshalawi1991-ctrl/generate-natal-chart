# Stack Research: generate-natal-chart

## Recommended Stack

### Core

| Technology | Version | Rationale | Confidence |
|-----------|---------|-----------|------------|
| **Python** | 3.10+ | Kerykeion requires 3.9+. 3.10+ gives better type hints and match statements for routing logic | High |
| **Kerykeion** | 4.x (latest) | Only actively maintained Python astrology library with built-in SVG generation, GeoNames geocoding, and comprehensive planetary calculations. Supports asteroids, aspects, houses, and dignities | High |

### Supporting

| Technology | Purpose | Rationale | Confidence |
|-----------|---------|-----------|------------|
| **json (stdlib)** | JSON serialization | No external dependency needed. Python's json module handles all chart data serialization | High |
| **pathlib (stdlib)** | File/path management | Cross-platform path handling for ~/.natal-charts/ storage. Better than os.path | High |
| **argparse (stdlib)** | CLI argument parsing | Parse birth details from command line when invoked by Claude Code skill | High |
| **Kerykeion SVG** | Chart visualization | Built-in KerykeionChartSVG class generates publication-quality natal chart SVGs | High |
| **slugify (python-slugify)** | Name normalization | Convert "John Doe" → "john-doe" for folder names. Handles unicode, special chars | Medium |

### Claude Code Skill Layer

| Component | Format | Purpose |
|-----------|--------|---------|
| **Skill definition** | .md file in ~/.claude/ | Slash command definition with routing logic, argument parsing instructions |
| **Astrologer guide prompt** | Embedded in skill .md or separate .md | Interpretation framework injected alongside chart JSON |

### What NOT to Use

| Technology | Why Not |
|-----------|---------|
| **Flatlib** | Unmaintained since 2019, no SVG generation, limited asteroid support |
| **Astropy** | Astronomical library, not astrological — no house systems, aspects, or chart interpretation concepts |
| **Swiss Ephemeris (pyswisseph) directly** | Low-level C bindings, Kerykeion already wraps this properly |
| **External geocoding APIs** | Kerykeion's GeoNames integration is sufficient, avoids extra API keys |
| **Jinja2 for SVG** | Over-engineering — Kerykeion's native SVG is good enough for v1 |
| **SQLite for storage** | JSON files in folders is simpler, more portable, and sufficient for profile management |

## Version Verification

- Python 3.10+: Verified current (3.12/3.13 latest as of 2025-2026)
- Kerykeion 4.x: Verify exact latest with `pip install kerykeion --upgrade` at build time. API may differ between 3.x and 4.x — check changelog
- python-slugify: Stable, latest 8.x

**Note:** Kerykeion's API surface has changed between major versions. The skill's Python script should pin to a specific version and document which Kerykeion API it targets.

## Integration Notes

### Data Flow
```
Claude Code Skill (.md) 
  → bash: python natal_chart.py --name "John" --date "1990-03-15" --time "14:30" --location "New York"
    → Kerykeion calculates chart
    → Script outputs: ~/.natal-charts/john/chart.json + chart.svg
  → Skill reads chart.json via Read tool
  → Skill injects astrologer guide prompt + JSON into context
```

### Key Integration Points
1. **Skill ↔ Python**: The .md skill invokes Python via bash. Arguments passed as CLI flags.
2. **Python ↔ Kerykeion**: Kerykeion's `AstrologicalSubject` class is the entry point. All planetary data extracted from this object.
3. **Python ↔ Storage**: Script manages ~/.natal-charts/ directory structure, writes JSON + SVG.
4. **Skill ↔ Context**: Skill uses Read tool to load chart.json, prepends astrologer guide prompt.
