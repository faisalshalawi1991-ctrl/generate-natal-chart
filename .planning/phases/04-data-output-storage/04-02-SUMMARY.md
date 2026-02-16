---
phase: 04-data-output-storage
plan: 02
subsystem: data-output
tags: [profile-management, storage, slugification, file-io, user-data]
dependency_graph:
  requires:
    - "04-01: JSON export and SVG generation with chart.json and chart.svg output"
    - "Phase 01-03: Kerykeion 5.7.2 installation and configuration"
  provides:
    - "Profile storage system in ~/.natal-charts/{slugified-name}/ subdirectories"
    - "Profile listing with --list flag showing all stored charts"
    - "Overwrite protection with existing birth data display"
    - "Unicode-safe slugification for international names"
  affects:
    - "Future plan: Profile loading functionality will use this storage structure"
    - "Future plan: Claude skill integration will reference these profile paths"
tech_stack:
  added:
    - "python-slugify: Unicode-safe filename sanitization (added in Plan 01)"
  patterns:
    - "Non-interactive confirmation pattern: Print warning + exit with error code, require --force flag to proceed"
    - "Profile storage convention: ~/.natal-charts/{slug}/chart.{json,svg}"
    - "Check-before-write pattern: Display existing data before overwrite protection"
key_files:
  created: []
  modified:
    - path: "backend/astrology_calc.py"
      changes:
        - "Added CHARTS_DIR constant for ~/.natal-charts base directory"
        - "Added check_existing_profile() function for overwrite protection"
        - "Added list_profiles() function for profile listing"
        - "Replaced --output-dir with automatic profile storage"
        - "Added --list and --force flags"
        - "Made name, date, time arguments conditional on --list flag"
        - "Automatic profile save on every chart generation"
decisions:
  - summary: "Non-interactive overwrite protection using --force flag"
    rationale: "Script will be called from Claude Code skill which cannot handle interactive prompts (input()). Print existing data + exit with code 1, user reruns with --force if desired."
    alternatives: "input() confirmation - rejected because skill automation requires non-interactive scripts"
  - summary: "Automatic profile storage on every chart generation"
    rationale: "Removed --output-dir in favor of always saving to ~/.natal-charts/{slug}/. Profile persistence is core value, making it optional adds friction."
    impact: "Every chart generation creates a profile. Simpler UX, no optional flags to remember."
  - summary: "Display existing birth data before rejecting overwrite"
    rationale: "Users need to see what profile already exists to decide if they want to overwrite it. Showing all birth details helps verify identity."
    result: "Prints date, time, location, coordinates, timezone, and generation timestamp"
  - summary: "Profile listing shows both city/nation and coordinates"
    rationale: "Some profiles use city lookup (Greenwich, GB), others use exact coordinates. Fallback display ensures all profiles show location info."
    impact: "Robust display for mixed profile sources"
metrics:
  duration_minutes: 4
  tasks_completed: 2
  files_modified: 1
  commits: 2
  lines_added: 167
  tests_passed: 8
  completed_at: "2026-02-16T14:06:47Z"
---

# Phase 04 Plan 02: Profile Management System

**Profile storage in ~/.natal-charts/{slug}/ with listing, overwrite protection, and unicode slugification using python-slugify**

## Performance

- **Duration:** 4 minutes
- **Started:** 2026-02-16T14:01:28Z
- **Completed:** 2026-02-16T14:06:47Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments

- Automatic profile storage in organized per-person subdirectories under ~/.natal-charts/
- Profile listing with --list flag showing all stored charts with birth details
- Overwrite protection displaying existing birth data, requiring --force to overwrite
- Unicode-safe directory naming (José García → jose-garcia)
- Non-interactive confirmation pattern suitable for Claude Code skill integration

## Task Commits

Each task was committed atomically:

1. **Task 1: Add profile storage with slugified directories and overwrite protection** - `1cabe28` (feat)
2. **Task 2: Add profile listing with --list flag** - `94d7a4f` (feat)

## Files Created/Modified

- `backend/astrology_calc.py` - Added profile management system
  - CHARTS_DIR constant: ~/.natal-charts base directory
  - check_existing_profile(): Display existing birth data, return false if exists
  - list_profiles(): List all profiles with birth details from chart.json
  - Automatic profile save on every chart generation
  - --list flag for profile listing (no birth data required)
  - --force flag for non-interactive overwrite confirmation
  - Made name/date/time arguments conditional on --list

## Decisions Made

1. **Non-interactive overwrite protection:** Print warning + exit code 1 instead of input() confirmation. This is critical because the script will be called from a Claude Code skill which cannot handle interactive prompts. Users rerun with --force if they want to overwrite.

2. **Automatic profile storage:** Removed --output-dir argument from Plan 01, replaced with automatic saving to ~/.natal-charts/{slugified-name}/. Profile persistence is the core value proposition, making it optional adds friction and complexity.

3. **Display existing birth data on conflict:** Before rejecting overwrite, the script prints the existing profile's birth date, time, location (city/nation), coordinates, timezone, and generation timestamp. This helps users verify the profile identity and make an informed decision about overwriting.

4. **Dual location display in listing:** Profile listing shows city/nation if available, otherwise falls back to coordinates + timezone. This handles profiles created via city lookup vs exact coordinates gracefully.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Missing kerykeion installation**
- **Found during:** Task 1 verification
- **Issue:** ModuleNotFoundError when running script - dependencies not installed in Python 3.11 environment
- **Fix:** Ran `pip install -r backend/requirements.txt` to install kerykeion and transitive dependencies (python-slugify already in requirements from Plan 01)
- **Files modified:** None (system-level pip install)
- **Verification:** Script runs successfully, generates profiles
- **Committed in:** Not applicable (environment setup)
- **Impact:** Required for script execution, standard setup step

**No other deviations** - Plan executed exactly as written.

## Issues Encountered

- **Python version discovery:** System has both Python 3.11 and 3.13 installed. `python` command defaults to 3.13, but Kerykeion requires 3.11 for pyswisseph compatibility (as established in Phase 01). Used explicit path `/c/Users/faisa/AppData/Local/Programs/Python/Python311/python` for testing.

## Verification Results

All verification tests passed:

1. **Profile creation:** Chart generated for "Albert Einstein" created `~/.natal-charts/albert-einstein/` with chart.json (9KB) + chart.svg (211KB)
2. **Overwrite protection:** Running same command without --force displayed WARNING with existing birth details and exited with code 1
3. **Force overwrite:** Running with --force successfully overwrote existing profile
4. **Profile listing:** `--list` flag displayed all profiles alphabetically by slug with names, birth dates/times, and locations
5. **Unicode slugification:** "José García" created `jose-garcia/` directory with valid slug
6. **Hidden file filtering:** Profile listing excludes directories starting with '.' (tested implicitly via sorted output)
7. **JSON integrity:** Stored chart.json contains all 10 sections (meta, planets, houses, angles, aspects, asteroids, fixed_stars, arabic_parts, dignities, distributions)
8. **SVG integrity:** Stored chart.svg is valid SVG file starting with `<svg` XML tag

## Technical Notes

**Profile Storage Structure:**
```
~/.natal-charts/
├── albert-einstein/
│   ├── chart.json
│   └── chart.svg
├── jose-garcia/
│   ├── chart.json
│   └── chart.svg
└── test-person/
    ├── chart.json
    └── chart.svg
```

**Slugification Examples:**
- "Albert Einstein" → `albert-einstein`
- "José García" → `jose-garcia`
- "Test Person" → `test-person`

**Overwrite Protection Flow:**
1. User runs chart generation command
2. Script builds chart data (runs all calculations)
3. Before saving, checks if `{slug}/chart.json` exists
4. If exists and no --force: loads existing JSON, prints birth details, exits with code 1
5. If exists and --force: proceeds to save (overwrites)
6. If not exists: proceeds to save (creates new profile)

**Non-Interactive Confirmation Pattern:**
- Traditional interactive: `input("Overwrite? (y/n): ")`
- Our pattern: Print warning → exit with error code → user reruns with --force
- Critical for skill automation: Claude Code cannot provide interactive input to running processes

**Profile Listing Display:**
- Alphabetically sorted by directory name (slug)
- Shows person name from chart.json meta.name
- Shows birth date and time from chart.json
- Tries city/nation first, falls back to coordinates + timezone
- Shows file existence (chart.json, chart.svg)
- Handles invalid JSON gracefully with "(invalid chart data)" message

## Integration Points

**Provides to Future Plans:**
- Profile storage directory structure (~/.natal-charts/{slug}/)
- Profile listing functionality (--list flag)
- Overwrite protection pattern (--force flag)
- Unicode-safe slugification (python-slugify)

**Uses from Previous Plans:**
- build_chart_json() function from Plan 04-01
- ChartDrawer SVG generation from Plan 04-01
- All calculation logic from Phases 01-03

## Next Phase Readiness

**Ready for next phase (Phase 05: Claude Integration):**
- Profile storage structure is stable and documented
- Profile listing enables discovering available charts
- Non-interactive design compatible with skill automation
- Unicode handling ensures international name support
- Overwrite protection prevents accidental data loss

**Potential enhancements for future phases:**
- Profile loading functionality (--load flag to load existing profile into Claude context)
- Profile deletion (--delete flag)
- Profile search/filter (by date range, location, etc.)
- Profile metadata (tags, notes, custom fields)

---

## Self-Check: PASSED

**Created files verified:**
- [N/A] No new files created (modified existing file only)

**Modified files verified:**
- [FOUND] `backend/astrology_calc.py` - check_existing_profile() function exists (line 214)
- [FOUND] `backend/astrology_calc.py` - list_profiles() function exists (line 244)
- [FOUND] `backend/astrology_calc.py` - CHARTS_DIR constant exists (line 24)

**Commits verified:**
- [FOUND] `1cabe28` - feat(04-02): add profile storage with slugified directories and overwrite protection
- [FOUND] `94d7a4f` - feat(04-02): add profile listing with --list flag

**Functionality verified:**
- [PASSED] Profile creation creates ~/.natal-charts/{slug}/ with chart.json + chart.svg
- [PASSED] Overwrite protection displays existing birth data and exits with code 1
- [PASSED] Force overwrite bypasses protection with --force flag
- [PASSED] Profile listing shows all profiles with names and birth details
- [PASSED] Unicode slugification works correctly (José García → jose-garcia)
- [PASSED] --list works without requiring name/date/time arguments
- [PASSED] Chart generation validates all required arguments
- [PASSED] All verification tests passed

---
*Phase: 04-data-output-storage*
*Completed: 2026-02-16*
