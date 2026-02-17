# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**generate-natal-chart** — A Claude Code skill that generates natal (birth) charts using the Kerykeion Python library, stores structured chart data as JSON profiles in `~/.natal-charts/{slug}/`, and loads them into Claude's active context with an expert astrological interpretation guide.

Tech stack: Python 3.11, Kerykeion 5.7.2, python-slugify, pyswisseph (Swiss Ephemeris). v1.0 shipped.

## Commands

```bash
# Activate the Python virtual environment
source /c/NEW/backend/venv/Scripts/activate

# Run with the venv Python directly (preferred in skill context)
/c/NEW/backend/venv/Scripts/python /c/NEW/backend/astrology_calc.py

# Create a chart (GeoNames online lookup)
/c/NEW/backend/venv/Scripts/python /c/NEW/backend/astrology_calc.py "Name" --date 1990-06-15 --time 14:30 --city "London" --nation "GB"

# Create a chart (offline with coordinates)
/c/NEW/backend/venv/Scripts/python /c/NEW/backend/astrology_calc.py "Name" --date 1990-06-15 --time 14:30 --lat 51.5074 --lng -0.1278 --tz "Europe/London"

# Overwrite existing profile
# (add --force flag to any create command)

# List existing chart profiles
/c/NEW/backend/venv/Scripts/python /c/NEW/backend/astrology_calc.py --list

# Install dependencies (if venv needs rebuilding)
python -m venv backend/venv && backend/venv/Scripts/pip install -r backend/requirements.txt
```

No automated test suite exists. Verification is done manually by running the CLI in each mode.

## Architecture

Three-tier system:

1. **Skill layer** (`~/.claude/skills/natal-chart/SKILL.md`) — Claude Code skill definition that routes user intent (create vs list/load), invokes the Python backend via Bash, and injects the interpretation guide into context. Lives outside this repo.

2. **Python backend** (`backend/astrology_calc.py`, ~1,070 LOC) — Single monolithic CLI script. Handles argument parsing, input validation, Kerykeion subject creation, data extraction (planets, houses, angles, aspects, asteroids, fixed stars, Arabic parts, dignities, element/modality distributions), JSON assembly, and SVG generation.

3. **Storage** (`~/.natal-charts/{slug}/`) — Each profile gets a slugified subfolder containing `chart.json` (structured data) and `chart.svg` (visual wheel). Profiles persist across sessions.

### Key backend functions

- `main()` — CLI entry point, argument parsing, orchestrates create/list modes
- `build_chart_json()` — Extracts all Kerykeion data into a comprehensive nested dict
- `list_profiles()` — Scans `~/.natal-charts/` and displays saved profiles
- `get_planet_dignities()` — Calculates essential dignities for 7 traditional planets
- `position_to_sign_degree()` — Converts ecliptic longitude to zodiac sign + degree

### Exit codes

- `0` — Success
- `1` — Validation error, profile already exists (without `--force`), or chart generation failed
- `2` — Argument parsing error

## Key Constraints

- **Kerykeion 5.7.2 pinned** — API differs between versions; do not upgrade without testing
- **Python 3.11** — Required for pyswisseph prebuilt wheel compatibility
- **Exact birth time required** — No partial charts; house/angle accuracy depends on it
- **Placidus house system only** — Kerykeion default, hardcoded for v1.0
- **GeoNames requires internet** — City/nation lookup needs network; use `--lat`/`--lng`/`--tz` for offline mode
- **Non-interactive CLI** — Uses exit codes + `--force` flag instead of interactive prompts (designed for Claude Code skill invocation)

## Planning Documentation

Extensive planning docs live in `.planning/` — `PROJECT.md` has requirements and key decisions, `ROADMAP.md` has the phase structure, and `research/` contains architecture, stack, and risk analysis documents.
