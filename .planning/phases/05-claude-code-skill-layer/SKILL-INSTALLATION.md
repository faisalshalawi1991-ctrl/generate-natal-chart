# Skill Installation Reference

## Installed Skill

**Location:** `~/.claude/skills/natal-chart/SKILL.md`

**Installation Date:** 2026-02-16

**Purpose:** Claude Code skill definition for natal chart generation system

## Skill Details

- **Name:** natal-chart
- **Description:** Generate natal astrological charts from birth data or list/load existing profiles
- **Allowed Tools:** Bash, Read, AskUserQuestion
- **Size:** 183 lines

## Routing Modes

1. **Create Mode** - Birth details provided → chart generation
2. **List/Load Mode** - No arguments → profile browsing and selection
3. **Name Search Mode** - Name only → search and load existing profile

## Backend Integration

- **Python Backend:** `C:/NEW/backend/astrology_calc.py`
- **Interpreter:** `./venv/Scripts/python` (direct path from C:/NEW/backend/)
- **Output Location:** `~/.natal-charts/{slug}/chart.json`

## Verification Results

All backend invocation tests passed:
- ✓ Create mode with city/nation
- ✓ Create mode with coordinates
- ✓ Overwrite protection (exit code 1)
- ✓ List profiles (exit code 0)
- ✓ chart.json readable with valid structure
- ✓ Validation error handling (exit code 2)
- ✓ Read tool instructions present in SKILL.md
- ✓ Under 200 lines (183 lines)

## Notes

The skill file is installed in the user's Claude Code skills directory (~/.claude/skills/), which is outside the git repository. This is the correct location for Claude Code skill definitions.

The skill serves as the user-facing interface to the natal chart generation system built in phases 1-4.
