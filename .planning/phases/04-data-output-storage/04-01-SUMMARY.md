---
phase: 04-data-output-storage
plan: 01
subsystem: data-output
tags: [json-export, svg-generation, structured-output, file-io]
dependency_graph:
  requires:
    - "03-01: Asteroids, Arabic Parts, Essential Dignities calculations"
    - "03-02: Fixed Stars, Element/Modality distributions"
    - "Phase 01-03: Kerykeion 5.7.2 installation and configuration"
  provides:
    - "Comprehensive JSON export with all chart data sections"
    - "SVG natal wheel chart generation via Kerykeion ChartDrawer"
    - "Optional file output mode via --output-dir flag"
  affects:
    - "04-02: Profile storage system will use these output functions"
tech_stack:
  added:
    - "json (stdlib): JSON serialization with UTF-8 encoding"
    - "datetime.timezone (stdlib): ISO 8601 timestamp generation"
    - "kerykeion.charts.chart_drawer.ChartDrawer: SVG natal wheel rendering"
    - "kerykeion.chart_data_factory.ChartDataFactory: Chart data model creation (with fallback)"
    - "python-slugify: Filename sanitization (added to requirements for Plan 02)"
  patterns:
    - "Optional feature flag pattern: --output-dir enables file output without breaking existing CLI behavior"
    - "Graceful API fallback: Try ChartDataFactory approach, fall back to direct subject approach for Kerykeion API compatibility"
    - "Dictionary construction from domain objects: Extract all calculations into JSON-serializable structure"
key_files:
  created: []
  modified:
    - path: "backend/astrology_calc.py"
      changes:
        - "Added build_chart_json() function (294 lines) that constructs comprehensive chart data dictionary"
        - "Added --output-dir argument for optional file output mode"
        - "Added file writing logic: JSON with UTF-8 encoding, SVG via ChartDrawer"
        - "Import additions: json, datetime.timezone, ChartDrawer"
        - "Maintained backward compatibility: script behavior unchanged when --output-dir not provided"
    - path: "backend/requirements.txt"
      changes:
        - "Added python-slugify dependency (needed by Plan 02 for profile filename generation)"
decisions:
  - summary: "Use dict construction instead of model_dump() for custom JSON structure"
    rationale: "Need complete control over structure including Phase 3 extended calculations, not just Kerykeion's default model fields"
    alternatives: "ChartDataModel.model_dump_json() - rejected because it doesn't include our custom calculations (fixed stars, distributions, etc.)"
  - summary: "Optional --output-dir flag instead of always writing files"
    rationale: "Maintains backward compatibility for existing CLI usage patterns (print-only mode)"
    impact: "Zero disruption to current workflows, opt-in file output"
  - summary: "Try/except fallback for ChartDataFactory vs direct subject approach"
    rationale: "Kerykeion 5.7.2 API may differ from documentation, ensure robustness across API variations"
    result: "ChartDataFactory approach worked successfully in testing"
  - summary: "Add python-slugify now instead of waiting for Plan 02"
    rationale: "Keep dependency management consolidated in one commit, avoid mid-plan pip install interruptions"
    impact: "Plan 02 can proceed without dependency setup steps"
metrics:
  duration_minutes: 4
  tasks_completed: 2
  files_modified: 2
  commits: 2
  lines_added: 348
  tests_passed: 6
  completed_at: "2026-02-16T14:00:12Z"
---

# Phase 04 Plan 01: JSON Export and SVG Chart Generation

**One-liner:** Structured JSON export with comprehensive chart data and SVG natal wheel generation via Kerykeion ChartDrawer, using optional --output-dir flag for backward compatibility.

## Overview

Transformed the print-based astrology calculation CLI into a data export system that generates both structured JSON (all chart data) and visual SVG (natal wheel) files. The existing script now builds a comprehensive chart data dictionary internally and can optionally write it to disk along with a rendered chart image.

This provides the foundation for Plan 02's profile storage system and enables loading complete chart data into Claude's context for astrological interpretation.

## Tasks Completed

### Task 1: Add JSON export with comprehensive chart data structure

**Commit:** `2b0908f`

**Implementation:**
- Created `build_chart_json(subject, args)` function that extracts all calculation logic from main()
- Returns Python dict with 10 top-level sections matching Phase 3 extended calculations
- Reuses existing calculation code (aspects, dignities, fixed stars, distributions, etc.)
- Imports: Added `json` and `datetime.timezone` for serialization and timestamps

**JSON Structure Sections:**
1. `meta`: Birth data, location, house system, chart type, generation timestamp
2. `planets`: All 10 planets with sign, degree, abs_position, house, retrograde
3. `houses`: 12 house cusps with sign and degree
4. `angles`: ASC, MC, DSC, IC with sign, degree, abs_position
5. `aspects`: Major aspects between planets with type, orb, movement
6. `asteroids`: 7 asteroids (Chiron, Liliths, Ceres, Pallas, Juno, Vesta) with positions
7. `fixed_stars`: Conjunctions within 1° orb to planets/angles
8. `arabic_parts`: Part of Fortune and Part of Spirit with positions
9. `dignities`: Essential dignities for 7 traditional planets
10. `distributions`: Element and modality counts/percentages/planet lists

**Data Accuracy:** All values match existing print output format, verified with Albert Einstein test chart.

**Files Modified:** `backend/astrology_calc.py` (+294 lines)

### Task 2: Add SVG generation and output file writing

**Commit:** `77d42b1`

**Implementation:**
- Added `--output-dir` optional argument to argparse parser
- When flag provided: creates directory, writes chart.json and chart.svg
- When flag omitted: script behaves identically to before (print-only mode)

**SVG Generation:**
- Imports `ChartDrawer` and `ChartDataFactory` from Kerykeion
- Try ChartDataFactory.create_natal_chart_data() approach first (modern API)
- Fall back to ChartDrawer(subject) if import/attribute fails (older API)
- Handles Kerykeion's filename variations (may generate chart_natal_chart.svg)
- Normalizes to `chart.svg` for consistent naming

**File Output:**
- JSON: UTF-8 encoding, indent=2, ensure_ascii=False for international characters
- SVG: Generated by Kerykeion with remove_css_variables=True for standalone files
- Directory auto-creation with parents=True, exist_ok=True
- Confirmation message with file sizes

**Dependency Update:**
- Added `python-slugify` to requirements.txt (needed by Plan 02 for filename sanitization)
- Keeps dependency management consolidated

**Files Modified:**
- `backend/astrology_calc.py` (+54 lines)
- `backend/requirements.txt` (+1 line)

## Verification Results

All verification tests passed:

1. **Test chart generation:** `/tmp/test-chart/chart.json` (10671 bytes) and `chart.svg` (226159 bytes) created successfully
2. **JSON schema completeness:** All 10 sections present (meta, planets, houses, angles, aspects, asteroids, fixed_stars, arabic_parts, dignities, distributions)
3. **SVG validity:** File exists, non-empty (226KB), starts with `<svg` XML tag
4. **Planet count:** Exactly 10 planets in JSON
5. **House count:** Exactly 12 houses in JSON
6. **Backward compatibility:** Running without `--output-dir` produces identical print output (no files created)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Missing kerykeion installation**
- **Found during:** Task 1 verification
- **Issue:** ModuleNotFoundError when running script - dependencies not installed
- **Fix:** Ran `pip install -r requirements.txt` to install kerykeion and transitive dependencies
- **Files modified:** None (system-level pip install)
- **Commit:** Not applicable (environment setup)
- **Impact:** Required for script execution, standard setup step

**No other deviations** - Plan executed exactly as written.

## Key Decisions Made

1. **Dict construction over model_dump():** Chose manual dictionary building to include all Phase 3 extended calculations, giving complete control over JSON structure
2. **Optional file output flag:** Maintained backward compatibility by making `--output-dir` optional rather than always writing files
3. **API fallback pattern:** Implemented try/except for ChartDataFactory vs direct subject approaches to handle Kerykeion API variations gracefully
4. **Consolidated dependency management:** Added python-slugify to requirements now (needed by Plan 02) to avoid mid-plan pip install interruptions

## Technical Notes

**JSON Structure Design:**
- Follows domain-driven design: one section per astrological domain
- All positions use consistent units: degrees within sign (0-30) and absolute ecliptic longitude (0-360)
- Retrograde as boolean flag (consistent with print output)
- House names as strings (matches Kerykeion output format)
- Timestamps in ISO 8601 format with UTC timezone

**SVG Generation:**
- Kerykeion ChartDrawer creates complete natal wheel with aspects, house cusps, and planetary positions
- File size ~200-230KB (includes embedded styles and Kerykeion attribution)
- Valid standalone SVG (can be opened in browser or image viewer)
- Chart layout matches Kerykeion defaults: traditional circular format with inner/outer rings

**Python Version Compatibility:**
- Script tested with Python 3.11 (project standard from Phase 01)
- Uses standard library features (json, datetime.timezone, pathlib)
- No Python 3.13-specific features

## Output Artifacts

**Generated Files (when --output-dir provided):**
1. `chart.json` - Comprehensive chart data in JSON format (9-11KB depending on number of aspects/stars)
2. `chart.svg` - Visual natal wheel chart (211-226KB)

**Modified Files:**
- `backend/astrology_calc.py` - Now exports JSON and generates SVG
- `backend/requirements.txt` - Includes python-slugify for Plan 02

## Integration Points

**Provides to Plan 02 (Profile Storage System):**
- `build_chart_json()` function for generating chart data structure
- File output logic for writing JSON and SVG
- python-slugify dependency already in requirements

**Uses from Phase 03:**
- Asteroids calculation (03-01)
- Arabic Parts calculation (03-01)
- Essential Dignities (03-01)
- Fixed Stars conjunctions (03-02)
- Element/Modality distributions (03-02)

## Next Steps

Plan 02 will build profile storage on top of this foundation:
- Create profiles directory structure
- Add --save-profile flag to save named profiles
- Add --list-profiles and --load-profile for retrieval
- Generate guide prompts for Claude context loading

---

## Self-Check: PASSED

**Created files verified:**
- [N/A] No new files created (modified existing files only)

**Modified files verified:**
- [FOUND] `backend/astrology_calc.py` - build_chart_json() function exists (line 207)
- [FOUND] `backend/requirements.txt` - python-slugify present (line 2)

**Commits verified:**
- [FOUND] `2b0908f` - feat(04-01): add comprehensive JSON export structure
- [FOUND] `77d42b1` - feat(04-01): add SVG generation and file output with --output-dir flag

**Functionality verified:**
- [PASSED] JSON export with all 10 sections
- [PASSED] SVG generation creates valid natal wheel chart
- [PASSED] Backward compatibility maintained
- [PASSED] All verification tests passed
