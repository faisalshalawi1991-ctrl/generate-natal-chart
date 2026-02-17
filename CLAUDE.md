# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**generate-natal-chart** — A Claude Code skill that generates natal (birth) charts and predictive astrology (transits, timelines, secondary progressions, solar arc directions) using the Kerykeion Python library, stores structured chart data as JSON profiles in `~/.natal-charts/{slug}/`, and loads them into Claude's active context with expert interpretation guides.

Tech stack: Python 3.11, Kerykeion 5.7.2, python-slugify, pyswisseph (Swiss Ephemeris). v1.1 shipped.

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

# Current transits against a profile
/c/NEW/backend/venv/Scripts/python /c/NEW/backend/astrology_calc.py --transits SLUG
/c/NEW/backend/venv/Scripts/python /c/NEW/backend/astrology_calc.py --transits SLUG --query-date 2026-06-15

# Transit timeline
/c/NEW/backend/venv/Scripts/python /c/NEW/backend/astrology_calc.py --timeline SLUG --range 3m
/c/NEW/backend/venv/Scripts/python /c/NEW/backend/astrology_calc.py --timeline SLUG --start 2026-01-01 --end 2026-06-30

# Secondary progressions
/c/NEW/backend/venv/Scripts/python /c/NEW/backend/astrology_calc.py --progressions SLUG --age 35
/c/NEW/backend/venv/Scripts/python /c/NEW/backend/astrology_calc.py --progressions SLUG --target-date 2026-06-15

# Solar arc directions
/c/NEW/backend/venv/Scripts/python /c/NEW/backend/astrology_calc.py --solar-arcs SLUG --target-year 2026
/c/NEW/backend/venv/Scripts/python /c/NEW/backend/astrology_calc.py --solar-arcs SLUG --target-year 2026 --arc-method mean

# Save any predictive snapshot to profile directory
# (add --save flag to any predictive command above)

# Install dependencies (if venv needs rebuilding)
python -m venv backend/venv && backend/venv/Scripts/pip install -r backend/requirements.txt
```

No automated test suite exists. Verification is done manually by running the CLI in each mode.

## Architecture

Three-tier system:

1. **Skill layer** (`~/.claude/skills/natal-chart/SKILL.md`, 537 lines) — Claude Code skill definition that routes user intent (create, list/load, predictive queries), invokes the Python backend via Bash, auto-loads transits on chart open, and injects natal + predictive interpretation guides into context. Lives outside this repo.

2. **Python backend** (`backend/astrology_calc.py`, ~2,360 LOC) — Single monolithic CLI script. Handles argument parsing, input validation, Kerykeion subject creation, natal data extraction (planets, houses, angles, aspects, asteroids, fixed stars, Arabic parts, dignities, element/modality distributions), transit snapshots, transit timelines, secondary progressions, solar arc directions, snapshot storage, JSON assembly, and SVG generation.

3. **Storage** (`~/.natal-charts/{slug}/`) — Each profile gets a slugified subfolder containing `chart.json` (structured data), `chart.svg` (visual wheel), and optional predictive snapshots (`transit-YYYY-MM-DD.json`, `progressions-YYYY-MM-DD.json`, `solar-arc-YYYY-MM-DD.json`, `timeline-YYYY-MM-DD.json`). Profiles persist across sessions.

### Key backend functions

- `main()` — CLI entry point, argument parsing, orchestrates create/list/predictive modes
- `build_chart_json()` — Extracts all Kerykeion natal data into a comprehensive nested dict
- `list_profiles()` — Scans `~/.natal-charts/` and displays saved profiles
- `load_natal_profile()` — Loads chart.json and recreates Kerykeion subject for predictive calculations
- `calculate_transits()` — Current transit positions and aspects against natal chart
- `calculate_timeline()` — Transit timeline with exact aspect hit detection over date ranges
- `calculate_progressions()` — Secondary progressions (day-for-a-year) with monthly Moon tracking
- `calculate_solar_arcs()` — Solar arc directions with true/mean arc methods
- `save_snapshot()` — Persists predictive JSON to profile directory with date-based naming
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
- **Placidus house system only** — Kerykeion default, hardcoded
- **GeoNames requires internet** — City/nation lookup needs network; use `--lat`/`--lng`/`--tz` for offline mode
- **Non-interactive CLI** — Uses exit codes + `--force` flag instead of interactive prompts (designed for Claude Code skill invocation)
- **Transit positions are geocentric** — lat=0.0, lng=0.0, UTC for location-independent ecliptic positions

## Planning Documentation

Extensive planning docs live in `.planning/` — `PROJECT.md` has requirements and key decisions, `ROADMAP.md` has the phase structure, `MILESTONES.md` has shipped version history, and `research/` contains architecture, stack, and risk analysis documents.
