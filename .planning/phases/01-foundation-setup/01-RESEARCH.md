# Phase 1: Foundation & Setup - Research

**Researched:** 2026-02-16
**Domain:** Python CLI development, Kerykeion astrology library, cross-platform path handling
**Confidence:** HIGH

## Summary

Phase 1 establishes the Python backend foundation with Kerykeion library integration and cross-platform compatibility. The technical stack is mature and well-documented: Kerykeion v5.7.2 (latest as of Feb 2026) provides robust astrological calculations with offline mode support, Python's standard library argparse handles CLI parsing, and pathlib ensures cross-platform path handling.

The primary challenge is proper configuration management: Kerykeion requires explicit timezone strings and coordinates in offline mode, and version pinning in requirements.txt is critical for reproducibility. The library's AGPL-3.0 license requires attention for closed-source projects but poses no restriction for this MCP skill use case.

**Primary recommendation:** Use Kerykeion v5.7.2 in offline mode with explicit coordinates/timezone, implement argparse-based CLI with proper validation, use pathlib for all path operations, and pin exact versions in requirements.txt.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| kerykeion | 5.7.2 | Astrological calculations and SVG generation | Active maintenance (Feb 2026 release), modern type-safe API, offline mode support, comprehensive documentation |
| argparse | stdlib | CLI argument parsing | Python standard library, zero dependencies, sufficient for this use case |
| pathlib | stdlib | Cross-platform path handling | Python standard library since 3.4, replaces os.path, automatic platform detection |
| pytz | 2024.2+ | IANA timezone handling | Kerykeion dependency, industry standard for timezone operations |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pyswisseph | >2.10.3.1 | Astronomical calculations (Kerykeion dependency) | Automatically installed with Kerykeion |
| pydantic | >2.5 | Data validation (Kerykeion dependency) | Automatically installed with Kerykeion |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| argparse | typer | Typer offers better UX (auto-completion, styled help) but adds dependency; argparse sufficient for simple CLI |
| pytz | zoneinfo (stdlib) | Python 3.9+ zoneinfo is modern standard, but Kerykeion depends on pytz, so no choice |
| venv | poetry/pipenv | Poetry/pipenv offer better dependency management but add complexity; venv sufficient for single-script project |

**Installation:**
```bash
# Create virtual environment
python -m venv venv

# Activate (bash/Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install kerykeion==5.7.2

# Generate pinned requirements
pip freeze > requirements.txt
```

## Architecture Patterns

### Recommended Project Structure
```
skill/
├── backend/
│   ├── astrology_calc.py    # Main CLI script
│   ├── requirements.txt      # Pinned dependencies
│   └── venv/                 # Virtual environment (not committed)
├── skill.sh                  # Bash wrapper that calls Python
└── README.md
```

### Pattern 1: CLI Entry Point with Main Function
**What:** Encapsulate CLI logic in a main() function, invoke via `if __name__ == "__main__"` guard
**When to use:** All Python scripts that can be imported as modules
**Example:**
```python
# Source: https://realpython.com/python-main-function/
import argparse
import sys

def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(description="Generate astrological chart")
    parser.add_argument("name", help="Person's name")
    parser.add_argument("--date", required=True, help="Birth date (YYYY-MM-DD)")
    # ... other arguments

    args = parser.parse_args()

    # Business logic here
    try:
        result = process_birth_data(args)
        print(result)
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

### Pattern 2: Kerykeion Offline Mode
**What:** Use AstrologicalSubjectFactory.from_birth_data with explicit coordinates and timezone
**When to use:** Always (avoid GeoNames API dependency and rate limits)
**Example:**
```python
# Source: https://github.com/g-battaglia/kerykeion
from kerykeion import AstrologicalSubjectFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    name="John Doe",
    year=1990, month=6, day=15,
    hour=14, minute=30,
    lng=-74.006,      # Longitude (decimal)
    lat=40.7128,      # Latitude (decimal)
    tz_str="America/New_York",  # IANA timezone
    online=False      # Critical: prevents GeoNames API calls
)

# Access calculated data
print(f"Sun: {subject.sun.sign} at {subject.sun.abs_pos:.2f}°")
```

### Pattern 3: Cross-Platform Path Handling
**What:** Use pathlib.Path for all file operations, never string concatenation
**When to use:** All file I/O, especially cross-platform scripts
**Example:**
```python
# Source: https://docs.python.org/3/library/pathlib.html
from pathlib import Path

# Home directory (cross-platform)
home = Path.home()  # /home/user on Linux, C:\Users\user on Windows

# Join paths with / operator
output_dir = home / ".config" / "astrology-skill"
output_file = output_dir / "chart.svg"

# Create directories if needed
output_dir.mkdir(parents=True, exist_ok=True)

# Write file
output_file.write_text("<svg>...</svg>")
```

### Pattern 4: Custom Argparse Type for Date Validation
**What:** Use custom type function to validate and parse dates at CLI boundary
**When to use:** When accepting structured input (dates, coordinates, etc.) via CLI
**Example:**
```python
# Source: https://gist.github.com/monkut/e60eea811ef085a6540f
import argparse
from datetime import datetime

def valid_date(s):
    """Validate date string in YYYY-MM-DD format."""
    try:
        return datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid date: {s} (expected YYYY-MM-DD)")

parser = argparse.ArgumentParser()
parser.add_argument("--date", type=valid_date, required=True)
```

### Anti-Patterns to Avoid
- **Global variables in script scope:** Put all logic in functions, use main() entry point
- **String path concatenation:** Use pathlib.Path, not `"path" + "/" + "file"`
- **Unpinned dependencies:** Always use exact versions in requirements.txt
- **Kerykeion online mode:** Requires GeoNames API key, subject to rate limits, adds external dependency
- **Mixing coordinate sources:** Always pass explicit lng/lat/tz_str in offline mode

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Astrological calculations | Custom ephemeris math | Kerykeion library | Swiss Ephemeris integration handles edge cases (precession, nutation, topocentric calculations), decades of astronomical research |
| Timezone handling | UTC offset parsing | pytz with IANA strings | Daylight saving time transitions, historical timezone changes, 500+ zones with complex rules |
| CLI argument parsing | Manual sys.argv parsing | argparse | Automatic help generation, type validation, error messages, subcommands |
| Path handling | os.path.join with conditionals | pathlib.Path | Automatic separator detection, platform-specific path types, cleaner API |
| Coordinate validation | String parsing/regex | Simple range checks or Pydantic | Latitude (-90 to 90), longitude (-180 to 180) bounds, decimal precision |

**Key insight:** Astrological calculations are deceptively complex. Kerykeion wraps Swiss Ephemeris, which implements algorithms from astronomical almanacs. Hand-rolling coordinate math would miss edge cases like houses near polar latitudes, topocentric vs geocentric calculations, and sidereal mode adjustments.

## Common Pitfalls

### Pitfall 1: Forgetting online=False in Kerykeion
**What goes wrong:** Script makes network calls to GeoNames API, fails without API key, hits rate limits
**Why it happens:** online=True is convenient for demos but requires geonames_username parameter
**How to avoid:** Always pass `online=False` and provide explicit `lng`, `lat`, `tz_str` parameters
**Warning signs:** Script hangs on first run, "GeoNames username warning" messages, network timeouts

### Pitfall 2: Unpinned Kerykeion Version in requirements.txt
**What goes wrong:** Kerykeion v6.x releases with breaking API changes, script breaks in production
**Why it happens:** Bare `pip install kerykeion` or `kerykeion>=5.0` in requirements.txt
**How to avoid:** Use exact version pinning: `kerykeion==5.7.2` in requirements.txt, regenerate with `pip freeze`
**Warning signs:** Script works in dev but fails after deployment, "AttributeError" on AstrologicalSubject methods

### Pitfall 3: Using pytz.localize() Instead of IANA Timezone Strings
**What goes wrong:** Timezone passed to Kerykeion is incorrect, birth time calculations are wrong
**Why it happens:** Confusion between pytz usage patterns and Kerykeion's tz_str parameter
**How to avoid:** Pass plain IANA timezone string ("America/New_York"), not pytz object or UTC offset
**Warning signs:** Chart houses/angles don't match expected values, off-by-hours errors

### Pitfall 4: String Path Concatenation on Windows
**What goes wrong:** Paths fail on Windows due to forward/backslash confusion, UNC paths break
**Why it happens:** Developer tests on Linux/Mac with forward slashes, Windows needs backslashes
**How to avoid:** Use `pathlib.Path()` exclusively, Path.home() for user directories, `/` operator for joining
**Warning signs:** "FileNotFoundError" only on Windows, paths like "/home/user" in error messages

### Pitfall 5: Missing sys.exit() Return Code
**What goes wrong:** Bash script can't detect Python script failure, continues after errors
**Why it happens:** Python prints exception but exits with code 0, bash sees success
**How to avoid:** Wrap main() in try/except, return 0 on success, sys.exit(1) on error
**Warning signs:** Bash script continues after obvious Python error, Claude doesn't see failure messages

### Pitfall 6: Invalid Coordinate Ranges
**What goes wrong:** Kerykeion accepts but produces incorrect results with out-of-range coordinates
**Why it happens:** No built-in validation in AstrologicalSubjectFactory for coordinate bounds
**How to avoid:** Validate before passing to Kerykeion: `-90 <= lat <= 90`, `-180 <= lng <= 180`
**Warning signs:** Bizarre planetary positions, impossible house cusps, silent calculation errors

### Pitfall 7: Virtual Environment Not Activated
**What goes wrong:** Kerykeion installed globally or not found, version mismatches between dev/prod
**Why it happens:** Developer forgets to activate venv before pip install or running script
**How to avoid:** Always activate venv in bash script: `source venv/bin/activate`, verify with `which python`
**Warning signs:** "ModuleNotFoundError: kerykeion", pip installs to system Python, version skew

## Code Examples

Verified patterns from official sources:

### Basic CLI Script Structure
```python
# Source: https://realpython.com/python-main-function/
#!/usr/bin/env python3
"""
Astrology calculation CLI for MCP skill.
Generates birth chart data from command-line arguments.
"""
import argparse
import sys
from pathlib import Path
from datetime import datetime
from kerykeion import AstrologicalSubjectFactory

def valid_date(s):
    """Validate date in YYYY-MM-DD format."""
    try:
        return datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid date: {s}")

def valid_latitude(s):
    """Validate latitude in range -90 to 90."""
    try:
        lat = float(s)
        if not -90 <= lat <= 90:
            raise ValueError
        return lat
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid latitude: {s} (must be -90 to 90)")

def valid_longitude(s):
    """Validate longitude in range -180 to 180."""
    try:
        lng = float(s)
        if not -180 <= lng <= 180:
            raise ValueError
        return lng
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid longitude: {s} (must be -180 to 180)")

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate astrological birth chart data"
    )
    parser.add_argument("name", help="Person's name")
    parser.add_argument("--date", type=valid_date, required=True,
                        help="Birth date (YYYY-MM-DD)")
    parser.add_argument("--time", required=True,
                        help="Birth time (HH:MM in 24-hour format)")
    parser.add_argument("--lat", type=valid_latitude, required=True,
                        help="Birth latitude (decimal)")
    parser.add_argument("--lng", type=valid_longitude, required=True,
                        help="Birth longitude (decimal)")
    parser.add_argument("--tz", required=True,
                        help="IANA timezone (e.g., America/New_York)")

    args = parser.parse_args()

    # Parse time
    try:
        birth_time = datetime.strptime(args.time, "%H:%M")
    except ValueError:
        print(f"Error: Invalid time format: {args.time} (expected HH:MM)",
              file=sys.stderr)
        return 1

    # Create astrological subject
    try:
        subject = AstrologicalSubjectFactory.from_birth_data(
            name=args.name,
            year=args.date.year,
            month=args.date.month,
            day=args.date.day,
            hour=birth_time.hour,
            minute=birth_time.minute,
            lng=args.lng,
            lat=args.lat,
            tz_str=args.tz,
            online=False  # Critical: offline mode
        )

        # Output results (placeholder)
        print(f"Successfully created chart for {subject.name}")
        print(f"Sun: {subject.sun.sign} at {subject.sun.abs_pos:.2f}°")

        return 0

    except Exception as e:
        print(f"Error creating chart: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

### Cross-Platform Path Handling in Bash Wrapper
```bash
# Source: https://docs.python.org/3/library/pathlib.html
# skill.sh - Bash wrapper for Python backend

# Get script directory (cross-platform)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$SCRIPT_DIR/backend"
VENV_DIR="$BACKEND_DIR/venv"

# Activate virtual environment
if [[ -f "$VENV_DIR/bin/activate" ]]; then
    # Linux/Mac
    source "$VENV_DIR/bin/activate"
elif [[ -f "$VENV_DIR/Scripts/activate" ]]; then
    # Windows (Git Bash)
    source "$VENV_DIR/Scripts/activate"
else
    echo "Error: Virtual environment not found at $VENV_DIR" >&2
    exit 1
fi

# Run Python script with arguments
python "$BACKEND_DIR/astrology_calc.py" "$@"
exit $?
```

### Generating Pinned requirements.txt
```bash
# Source: https://pip.pypa.io/en/stable/topics/repeatable-installs/
# After installing Kerykeion in activated venv

# Install specific version
pip install kerykeion==5.7.2

# Generate pinned requirements with all transitive dependencies
pip freeze > requirements.txt

# Result: requirements.txt with exact versions
# kerykeion==5.7.2
# pyswisseph==2.10.3.2
# pydantic==2.5.3
# ... (all dependencies with ==)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Kerykeion v4 API with direct AstrologicalSubject() | Kerykeion v5 AstrologicalSubjectFactory | v5.0.0 (2024) | Factory pattern separates computation/data/rendering, better type safety |
| pytz for timezone operations | zoneinfo (stdlib) preferred | Python 3.9 (2020) | Kerykeion still uses pytz, so no migration possible yet |
| os.path for path handling | pathlib.Path | Python 3.4 (2014) | Standard practice as of 2026, cleaner API |
| Manual sys.argv parsing | argparse standard library | Always standard | argparse sufficient, typer/click add dependencies |
| Unpinned dependencies | Exact version pinning with pip freeze | Ongoing best practice | Critical for reproducibility, prevents supply chain attacks |

**Deprecated/outdated:**
- **Kerykeion v4 API:** v5 is ground-up redesign, v4 patterns no longer recommended
- **GeoNames online mode for production:** Rate limits, API key management, network dependency
- **pytz localize() patterns:** Use plain IANA strings with Kerykeion, not pytz objects
- **String path concatenation:** pathlib is standard as of 2026

## Open Questions

1. **Hash verification for requirements.txt**
   - What we know: `pip freeze` generates exact versions, `pip install --require-hashes` adds integrity checks
   - What's unclear: Whether hash verification is overkill for this simple use case
   - Recommendation: Start with exact version pinning (`==`), add hashes if supply chain security becomes concern

2. **Poetry vs pip for dependency management**
   - What we know: Poetry offers better lock files, dependency resolution, and is community standard for serious projects (2026)
   - What's unclear: Whether Poetry's complexity is justified for single-script project
   - Recommendation: Use plain pip + venv + requirements.txt for simplicity, migrate to Poetry if project grows

3. **Error handling for Swiss Ephemeris edge cases**
   - What we know: Kerykeion wraps Swiss Ephemeris, may fail for extreme dates or polar latitudes
   - What's unclear: Exact failure modes and error messages
   - Recommendation: Test with edge cases (ancient dates, polar coordinates) during verification, add defensive error handling

## Sources

### Primary (HIGH confidence)
- [Kerykeion GitHub Repository](https://github.com/g-battaglia/kerykeion) - Current API, examples, version info
- [Kerykeion PyPI Package](https://pypi.org/project/kerykeion/) - Version 5.7.2 confirmed, dependencies list
- [Kerykeion Official Documentation](https://www.kerykeion.net/content/docs/astrological_subject_factory) - AstrologicalSubjectFactory API
- [Python argparse Documentation](https://docs.python.org/3/library/argparse.html) - Official Python docs
- [Python pathlib Documentation](https://docs.python.org/3/library/pathlib.html) - Official Python docs
- [Python __main__ Documentation](https://docs.python.org/3/library/__main__.html) - Entry point patterns

### Secondary (MEDIUM confidence)
- [Real Python: Python Main Function](https://realpython.com/python-main-function/) - Best practices for main() pattern
- [Real Python: pathlib Guide](https://realpython.com/python-pathlib/) - Cross-platform path handling
- [Real Python: argparse Tutorial](https://realpython.com/command-line-interfaces-python-argparse/) - CLI patterns
- [pip Repeatable Installs](https://pip.pypa.io/en/stable/topics/repeatable-installs/) - Version pinning, hash verification
- [Custom argparse Date Validation](https://gist.github.com/monkut/e60eea811ef085a6540f) - Date type validation pattern
- [Kerykeion GitHub Issues #136](https://github.com/g-battaglia/kerykeion/issues/136) - GeoNames username pitfall
- [Python venv Documentation](https://docs.python.org/3/library/venv.html) - Virtual environment best practices

### Tertiary (LOW confidence - verified with official sources)
- WebSearch results for Python virtual environment best practices (2026) - Cross-verified with official docs
- WebSearch results for requirements.txt version pinning - Cross-verified with pip documentation
- WebSearch results for coordinate validation ranges - Standard geographic bounds (-90/90, -180/180)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All tools verified via PyPI/official docs, Kerykeion 5.7.2 confirmed Feb 2026 release
- Architecture: HIGH - Patterns from official Python docs and Real Python tutorials
- Pitfalls: MEDIUM-HIGH - GeoNames issue verified via GitHub, other pitfalls based on library documentation and common Python mistakes
- Code examples: HIGH - All examples sourced from official docs, GitHub repo, or established Python tutorials

**Research date:** 2026-02-16
**Valid until:** 2026-04-16 (60 days - stable ecosystem, Kerykeion v5 mature, Python stdlib patterns unchanging)
