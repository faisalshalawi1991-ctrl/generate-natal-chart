# Phase 7: Current Transit Snapshots - Research

**Researched:** 2026-02-17
**Domain:** Kerykeion 5.7.2 transit-to-natal aspect calculation, house placement, retrograde detection
**Confidence:** HIGH

## Summary

Phase 7 adds a `--transits` CLI mode to the existing monolithic `backend/astrology_calc.py`. The user specifies a natal chart profile slug and an optional query date (defaults to today); the script calculates the positions of the 10 major planets at that date and computes their aspects to the natal chart planets, which natal houses they occupy, retrograde status, and whether each aspect is applying or separating.

All five requirements (TRAN-01 through TRAN-05) are fully addressable using Kerykeion 5.7.2 APIs that are already installed. Direct testing against the local installation confirms: `AspectsFactory.dual_chart_aspects()` handles transit-to-natal aspects with configurable orbs and returns `aspect_movement` ('Applying'/'Separating'/'Static'); `HouseComparisonFactory` returns which natal house each transiting planet occupies; and planet objects expose a `retrograde` boolean attribute. Zero new dependencies are required.

The key architectural decision for Phase 7 is to create a transit `AstrologicalSubject` for the query date (using UTC, with arbitrary location coordinates) and compare it against a reconstructed natal `AstrologicalSubject` loaded from the stored `chart.json` profile. This is simpler and more direct than the `EphemerisDataFactory` + `TransitsTimeRangeFactory` pipeline, which is more appropriate for Phase 8 date ranges. The natal chart functionality must remain completely untouched.

**Primary recommendation:** Add a `--transits [SLUG]` subcommand with `--date` (default: today) that reconstructs the natal chart from profile JSON, creates a UTC transit subject for the query date, and calls `AspectsFactory.dual_chart_aspects()` + `HouseComparisonFactory` to assemble a transit JSON output.

## Standard Stack

### Core (No Changes)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Kerykeion | 5.7.2 | Astrological calculations | Already installed. `AspectsFactory.dual_chart_aspects()` and `HouseComparisonFactory` handle all five TRAN requirements. PINNED — do not upgrade. |
| Python | 3.11 | Runtime | Required for pyswisseph prebuilt wheels. |
| pyswisseph | bundled | Swiss Ephemeris backend | Not called directly in Phase 7; Kerykeion wraps it. |

### Kerykeion APIs Used in Phase 7
| API | Class/Method | What It Provides |
|-----|-------------|-----------------|
| Subject creation | `AstrologicalSubjectFactory.from_birth_data()` | Creates transit subject for query date (already used for natal) |
| Transit aspects | `AspectsFactory.dual_chart_aspects(transit, natal, active_aspects=..., active_points=...)` | Returns `DualChartAspectsModel` with aspect list including `aspect_movement` |
| House placement | `HouseComparisonFactory(transit, natal, active_points=...).get_house_comparison()` | Returns which natal house each transit planet occupies |
| Retrograde status | `planet.retrograde` (bool on `AstrologicalSubjectModel` planet objects) | Directly available on transit subject's planet attributes |
| Planet speed | `planet.speed` (float, deg/day) | Negative = retrograde; positive = direct |

### No New Dependencies
No `pip install` required. All APIs verified working against local Kerykeion 5.7.2 installation.

## Architecture Patterns

### Pattern 1: Transit Snapshot Calculation
**What:** Create a transit `AstrologicalSubject` for the query date in UTC, then compare against the natal subject.
**When to use:** Any single-date transit calculation (Phase 7 scope).

```python
# Source: verified against local Kerykeion 5.7.2 installation
from kerykeion import AstrologicalSubjectFactory
from kerykeion.aspects.aspects_factory import AspectsFactory
from kerykeion.house_comparison.house_comparison_factory import HouseComparisonFactory
from kerykeion.schemas.kr_models import ActiveAspect

# Step 1: Load natal data from stored profile
import json
from pathlib import Path
from datetime import datetime

chart_json = Path(f"~/.natal-charts/{slug}/chart.json").expanduser()
with open(chart_json) as f:
    data = json.load(f)
meta = data['meta']
loc = meta['location']
birth_date = datetime.strptime(meta['birth_date'], '%Y-%m-%d')
birth_time = datetime.strptime(meta['birth_time'], '%H:%M')

# Step 2: Reconstruct natal AstrologicalSubject (offline, no GeoNames call)
natal = AstrologicalSubjectFactory.from_birth_data(
    name=meta['name'],
    year=birth_date.year, month=birth_date.month, day=birth_date.day,
    hour=birth_time.hour, minute=birth_time.minute,
    lat=loc['latitude'], lng=loc['longitude'],
    tz_str=loc['timezone'],
    online=False,
    houses_system_identifier='P'  # Placidus, matches natal chart
)

# Step 3: Create transit subject for query date (use UTC)
# Planet ecliptic longitudes depend only on UTC time, not on location
transit_date = datetime(2026, 2, 17, 12, 0)  # or datetime.utcnow()
transit = AstrologicalSubjectFactory.from_birth_data(
    name='Current Transits',
    year=transit_date.year, month=transit_date.month, day=transit_date.day,
    hour=transit_date.hour, minute=transit_date.minute,
    lat=0.0, lng=0.0,  # arbitrary — does not affect ecliptic planet positions
    tz_str='UTC',
    online=False,
    houses_system_identifier='P'
)

# Step 4: Configure orbs (TRAN-02: defaults 1-3 degrees by aspect type)
TRANSIT_DEFAULT_ORBS = [
    ActiveAspect(name='conjunction', orb=3),
    ActiveAspect(name='opposition', orb=3),
    ActiveAspect(name='trine', orb=2),
    ActiveAspect(name='square', orb=2),
    ActiveAspect(name='sextile', orb=1),
]

MAJOR_PLANETS = [
    'Sun', 'Moon', 'Mercury', 'Venus', 'Mars',
    'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto'
]

# Step 5: Calculate transit-to-natal aspects (TRAN-02, TRAN-05)
aspects_result = AspectsFactory.dual_chart_aspects(
    transit, natal,
    active_aspects=TRANSIT_DEFAULT_ORBS,
    active_points=MAJOR_PLANETS
)
# aspects_result.aspects is a list of AspectModel objects with fields:
# p1_name, p2_name, aspect, orbit, aspect_movement ('Applying'/'Separating'/'Static')

# Step 6: Calculate house placement (TRAN-03)
factory = HouseComparisonFactory(transit, natal, active_points=MAJOR_PLANETS)
comparison = factory.get_house_comparison()
# comparison.first_points_in_second_houses: transit planet -> natal house
# Fields: point_name, point_sign, point_degree, projected_house_number

# Step 7: Build transit JSON output
transit_planets = [
    ('Sun', transit.sun), ('Moon', transit.moon),
    ('Mercury', transit.mercury), ('Venus', transit.venus),
    ('Mars', transit.mars), ('Jupiter', transit.jupiter),
    ('Saturn', transit.saturn), ('Uranus', transit.uranus),
    ('Neptune', transit.neptune), ('Pluto', transit.pluto),
]

# Retrograde status + house from HouseComparisonFactory
house_map = {
    item.point_name: item.projected_house_number
    for item in comparison.first_points_in_second_houses
}

planets_out = []
for name, planet in transit_planets:
    planets_out.append({
        'name': name,
        'sign': planet.sign,
        'degree': round(planet.abs_pos % 30, 2),
        'abs_position': round(planet.abs_pos, 4),
        'retrograde': planet.retrograde,   # TRAN-04
        'natal_house': house_map.get(name),  # TRAN-03
    })

aspects_out = []
for asp in aspects_result.aspects:
    aspects_out.append({
        'transit_planet': asp.p1_name,
        'natal_planet': asp.p2_name,
        'aspect': asp.aspect,
        'orb': round(asp.orbit, 2),
        'applying': asp.aspect_movement == 'Applying',
        'movement': asp.aspect_movement,  # TRAN-05
    })
```

### Pattern 2: CLI Argument Parsing for Transit Mode
**What:** Add a new mutually exclusive subcommand alongside the existing natal chart creation mode.

```python
# Add --transits flag with SLUG and optional --date
# Must not break existing natal chart argument validation

parser.add_argument(
    '--transits',
    metavar='SLUG',
    help='Calculate transits for an existing chart profile (e.g., albert-einstein)'
)
parser.add_argument(
    '--query-date',
    type=valid_query_date,  # New validator: 1900-2100 range
    default=None,
    help='Date for transit calculation YYYY-MM-DD (default: today UTC)'
)
```

### Pattern 3: Reconstructing Natal Subject from Profile JSON
**What:** Load natal birth data from stored `chart.json` and recreate `AstrologicalSubject` without GeoNames call.

The profile JSON stores all required fields:
- `meta.birth_date` — YYYY-MM-DD string
- `meta.birth_time` — HH:MM string
- `meta.location.latitude` — float
- `meta.location.longitude` — float
- `meta.location.timezone` — IANA timezone string

Use `online=False` to avoid GeoNames network call during transit mode.

### Recommended File Structure (No New Files)
```
backend/
└── astrology_calc.py   # Add transit functions here (isolated section)
    ├── [existing natal chart code - UNTOUCHED]
    ├── valid_query_date()       # New: transit date validator (1900-2100)
    ├── load_natal_profile()     # New: load + reconstruct natal subject from JSON
    ├── build_transit_json()     # New: assemble transit output dict
    ├── calculate_transits()     # New: orchestrates transit snapshot
    └── [existing main() - add --transits routing]
```

### Anti-Patterns to Avoid
- **Creating transit subject with GeoNames (`online=True`):** Unnecessary network call; transit planet positions are location-independent ecliptic longitudes. Always use `online=False` for transit subjects.
- **Using EphemerisDataFactory for a single-date snapshot:** That class is designed for date ranges (Phase 8). Overkill and more complex for a point-in-time query.
- **Modifying existing natal chart code paths:** All new transit code must be isolated in new functions. Never modify `build_chart_json()`, `valid_date()`, `valid_time()`, or `main()` natal creation logic.
- **Using natal timezone for transit time:** Users specify query date as a calendar date; always interpret as UTC midnight (or UTC noon if time not specified) to avoid DST ambiguity.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Transit-to-natal aspect calculation | Custom orb comparison loop | `AspectsFactory.dual_chart_aspects()` | Handles aspect math, applying/separating via speed comparison, orb filtering |
| Applying vs separating determination | Compare planet speeds manually | `AspectModel.aspect_movement` field | Already computed by Kerykeion from `p1_speed` and `p2_speed` |
| Transit planet house placement | Compare planet longitude vs house cusp list | `HouseComparisonFactory.get_house_comparison()` | Handles Placidus house boundary logic correctly |
| Planet retrograde status | Compute from speed or ephemeris flags | `planet.retrograde` boolean | Directly on `AstrologicalSubjectModel` planet objects |

**Key insight:** Kerykeion 5.7.2 provides all five required transit data points as first-class API features. The implementation is primarily JSON assembly and argument parsing, not astrological computation.

## Common Pitfalls

### Pitfall 1: Transit Location Affecting Planet Positions
**What goes wrong:** Developer uses natal birth location for transit subject, then notices 0.3° position differences when compared to a reference source using UTC coordinates.
**Why it happens:** Kerykeion interprets the hour/minute parameters relative to the specified timezone. `12:00` in `Europe/Berlin` (UTC+1) = `11:00 UTC`, which is a different Julian Day from `12:00 UTC`.
**How to avoid:** Always create transit subjects with `tz_str='UTC'` and pass UTC time directly. Planet ecliptic longitudes are geocentric and depend only on the UTC Julian Day number, not on geographic location. Confirmed by testing: `UTC 12:00` with `lng=0` gives identical positions to `UTC 12:00` with `lng=139.65` (Tokyo).
**Warning signs:** Transit Sun position differs by 0.3-1.0° from other astrology software for same date.

### Pitfall 2: Breaking Natal Chart Functionality
**What goes wrong:** Adding `--transits` argument parsing interacts with existing natal chart argument validation, causing natal chart creation to fail or show incorrect help text.
**Why it happens:** The existing `main()` function validates that `--date`, `--time`, and location args are all present for natal chart creation. Adding `--transits` as a new mode requires careful mutual exclusion.
**How to avoid:** Check for `--transits` FIRST in `main()`, before any natal chart validation runs. Route to `calculate_transits()` immediately and return. Never share argument validation between modes.
**Warning signs:** `--list` mode (which already uses early return) provides the correct pattern to follow.

### Pitfall 3: Using `NatalAspects` (Deprecated) Instead of `AspectsFactory`
**What goes wrong:** Developer copies existing v1.0 code that uses `NatalAspects(subject)` and tries to adapt it for transit calculations.
**Why it happens:** The existing `astrology_calc.py` uses the legacy `NatalAspects` class (imported at line 16). This class is a compatibility shim and only handles single-chart aspects, not dual-chart transit-to-natal.
**How to avoid:** Import and use `AspectsFactory.dual_chart_aspects(transit, natal)` for transit calculations. Do not use `NatalAspects` for transit mode.
**Warning signs:** `NatalAspects` does not accept two subjects; trying to pass both will raise a `TypeError`.

### Pitfall 4: Query Date Validation Range Mismatch
**What goes wrong:** Using the existing `valid_date()` validator for transit query dates. It rejects years before 1800, but transit queries should support 1900-2100 (and "today" is 2026, which passes — but future dates would fail).
**Why it happens:** The existing `valid_date()` was designed for birth dates (historical), not query dates (past + future).
**How to avoid:** Create a separate `valid_query_date()` function that accepts 1900-2100.
**Warning signs:** User tries `--query-date 2030-01-01` and gets "Year must be between 1800 and 2026" error.

### Pitfall 5: Pydantic Deprecation Warning on Model Field Access
**What goes wrong:** Accessing `.model_fields` or `.model_computed_fields` on instances of Kerykeion Pydantic models raises deprecation warnings in Pydantic 2.11+.
**Why it happens:** Kerykeion 5.7.2 uses Pydantic v2, which deprecated instance-level `model_fields` access.
**How to avoid:** Access `model_fields` on the CLASS, not the instance: `AspectModel.model_fields` not `asp.model_fields`. Better yet, simply access the field directly by name (e.g., `asp.aspect_movement`, `asp.orbit`).
**Warning signs:** Warning output like "Accessing the 'model_fields' attribute on the instance is deprecated."

## Code Examples

Verified patterns from direct testing against local Kerykeion 5.7.2 installation.

### Creating Transit Subject (UTC, Location-Independent)
```python
# Source: verified against local Kerykeion 5.7.2 installation (2026-02-17)
from kerykeion import AstrologicalSubjectFactory
from datetime import datetime, timezone

now_utc = datetime.now(timezone.utc)
transit = AstrologicalSubjectFactory.from_birth_data(
    name='Current Transits',
    year=now_utc.year, month=now_utc.month, day=now_utc.day,
    hour=now_utc.hour, minute=now_utc.minute,
    lat=0.0, lng=0.0,    # location irrelevant for ecliptic positions
    tz_str='UTC',
    online=False,
    houses_system_identifier='P'
)
# Access planet data
print(transit.sun.abs_pos)   # ecliptic longitude (0-360)
print(transit.mars.retrograde)  # True or False
print(transit.jupiter.speed)    # deg/day, negative = retrograde
```

### Transit-to-Natal Aspects with Custom Orbs
```python
# Source: verified against local Kerykeion 5.7.2 installation (2026-02-17)
from kerykeion.aspects.aspects_factory import AspectsFactory
from kerykeion.schemas.kr_models import ActiveAspect

# TRAN-02: configurable orbs (defaults 1-3 deg by aspect type)
TRANSIT_DEFAULT_ORBS = [
    ActiveAspect(name='conjunction', orb=3),
    ActiveAspect(name='opposition', orb=3),
    ActiveAspect(name='trine', orb=2),
    ActiveAspect(name='square', orb=2),
    ActiveAspect(name='sextile', orb=1),
]
MAJOR_PLANETS = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars',
                 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto']

result = AspectsFactory.dual_chart_aspects(
    transit,  # first subject = transiting planets
    natal,    # second subject = natal chart
    active_aspects=TRANSIT_DEFAULT_ORBS,
    active_points=MAJOR_PLANETS
)

for asp in result.aspects:
    print(f"{asp.p1_name} {asp.aspect} natal {asp.p2_name}")
    print(f"  orb: {asp.orbit:.2f}°")
    print(f"  movement: {asp.aspect_movement}")  # 'Applying', 'Separating', or 'Static'
    print(f"  applying: {asp.aspect_movement == 'Applying'}")  # TRAN-05
```

### Transit House Placement (TRAN-03)
```python
# Source: verified against local Kerykeion 5.7.2 installation (2026-02-17)
from kerykeion.house_comparison.house_comparison_factory import HouseComparisonFactory

factory = HouseComparisonFactory(transit, natal, active_points=MAJOR_PLANETS)
comparison = factory.get_house_comparison()

# comparison.first_points_in_second_houses = transit planets in natal houses
for item in comparison.first_points_in_second_houses:
    print(f"Transit {item.point_name}: {item.point_sign} {item.point_degree:.1f}°")
    print(f"  -> natal house {item.projected_house_number}")
```

### Retrograde Status (TRAN-04)
```python
# Source: verified against local Kerykeion 5.7.2 installation (2026-02-17)
planets = [
    ('Sun', transit.sun), ('Moon', transit.moon),
    ('Mercury', transit.mercury), ('Venus', transit.venus),
    ('Mars', transit.mars), ('Jupiter', transit.jupiter),
    ('Saturn', transit.saturn), ('Uranus', transit.uranus),
    ('Neptune', transit.neptune), ('Pluto', transit.pluto),
]
for name, planet in planets:
    retro_str = " (R)" if planet.retrograde else ""
    print(f"{name}: {planet.sign} {planet.abs_pos % 30:.2f}°{retro_str}")
    # Jupiter retrograde confirmed: retrograde=True, speed=-0.069 (2026-02-17)
```

### ActiveAspect TypedDict Usage
```python
# Source: verified against local Kerykeion 5.7.2 installation (2026-02-17)
# ActiveAspect is a TypedDict (NOT a Pydantic model)
# Valid aspect names: 'conjunction', 'semi-sextile', 'semi-square', 'sextile',
#                    'quintile', 'square', 'trine', 'sesquiquadrate',
#                    'biquintile', 'quincunx', 'opposition'
from kerykeion.schemas.kr_models import ActiveAspect
orb_config = ActiveAspect(name='conjunction', orb=3)  # orb must be int
```

### Loading Natal Profile and Reconstructing Subject
```python
# Source: verified against local Kerykeion 5.7.2 installation (2026-02-17)
import json
from pathlib import Path
from datetime import datetime
from kerykeion import AstrologicalSubjectFactory

def load_natal_subject(slug: str):
    chart_path = Path(f"~/.natal-charts/{slug}/chart.json").expanduser()
    if not chart_path.exists():
        raise FileNotFoundError(f"Profile '{slug}' not found")
    with open(chart_path) as f:
        data = json.load(f)
    meta = data['meta']
    loc = meta['location']
    birth_date = datetime.strptime(meta['birth_date'], '%Y-%m-%d')
    birth_time = datetime.strptime(meta['birth_time'], '%H:%M')
    return AstrologicalSubjectFactory.from_birth_data(
        name=meta['name'],
        year=birth_date.year, month=birth_date.month, day=birth_date.day,
        hour=birth_time.hour, minute=birth_time.minute,
        lat=loc['latitude'], lng=loc['longitude'],
        tz_str=loc['timezone'],
        online=False,
        houses_system_identifier='P'
    )
```

### Complete Transit JSON Output Structure
```python
# Target output structure for transit snapshot
transit_output = {
    "meta": {
        "natal_name": "Albert Einstein",
        "natal_slug": "albert-einstein",
        "query_date": "2026-02-17",
        "query_time_utc": "12:00",
        "chart_type": "transit_snapshot",
        "calculated_at": "2026-02-17T12:00:00+00:00",
        "orbs_used": {
            "conjunction": 3, "opposition": 3,
            "trine": 2, "square": 2, "sextile": 1
        }
    },
    "transit_planets": [
        {
            "name": "Jupiter",
            "sign": "Can",
            "degree": 15.85,
            "abs_position": 105.85,
            "retrograde": True,
            "natal_house": 1
        }
        # ... all 10 planets
    ],
    "transit_aspects": [
        {
            "transit_planet": "Sun",
            "natal_planet": "Uranus",
            "aspect": "opposition",
            "orb": 2.46,
            "applying": True,
            "movement": "Applying"
        }
        # ... all matching aspects within orb
    ]
}
```

## State of the Art

| Old Approach | Current Approach | Impact for Phase 7 |
|---|---|---|
| `NatalAspects(subject1, subject2)` (legacy dual-chart) | `AspectsFactory.dual_chart_aspects(s1, s2)` | Use new API; old one deprecated |
| Manual retrograde detection (speed < 0) | `planet.retrograde` boolean attribute | Direct attribute access, no custom logic needed |
| `synastry_aspects()` method | `dual_chart_aspects()` method | `synastry_aspects` is now a deprecated alias |
| `natal_aspects()` method | `single_chart_aspects()` method | `natal_aspects` is now a deprecated alias |

**Deprecated in current codebase (`astrology_calc.py`):**
- `NatalAspects` (line 16 import) — used only in natal chart path; do NOT use for transits. The import is fine (needed for natal chart mode), but don't call it for dual-chart transit calculations.

## Open Questions

1. **Where to output transit results**
   - What we know: Transit data will be a JSON dict. The existing natal chart writes to `~/.natal-charts/{slug}/chart.json`.
   - What's unclear: Phase 7 says "fresh calculation" (no persistent storage). Phase 12 adds optional save. So the output is printed to stdout, not saved to disk.
   - Recommendation: Print transit JSON to stdout (consistent with skill loading transit data into context). Do NOT write to disk in Phase 7. Add `--save` flag in Phase 12.

2. **Default query date/time when user omits `--query-date`**
   - What we know: TRAN-01 says "for any date" — date argument is user-specified. But "current" implies today.
   - What's unclear: Should default be `datetime.utcnow()` (current UTC moment) or just today's date at UTC midnight?
   - Recommendation: Default to current UTC moment (`datetime.now(timezone.utc)`), which gives the most accurate "current" position for all planets including fast-moving Moon.

3. **Orb configurability via CLI vs hardcoded defaults**
   - What we know: TRAN-02 specifies "configurable orbs (default: 1-3° by aspect type)."
   - What's unclear: Whether CLI flags like `--orb-conjunction 5` are needed now, or if the 1-3° defaults suffice for Phase 7.
   - Recommendation: Implement defaults (3/3/2/2/1 for conj/opp/trine/sq/sext) as constants in the code. Add CLI orb overrides as a stretch goal or defer to Phase 11 when the interpretation guide is built.

## Sources

### Primary (HIGH confidence)
- Local Kerykeion 5.7.2 installation — direct Python REPL testing of all APIs (2026-02-17)
  - `AspectsFactory.dual_chart_aspects()` — confirmed returns `DualChartAspectsModel` with `aspects` list
  - `AspectModel` fields: `p1_name`, `p2_name`, `aspect`, `orbit`, `aspect_movement` ('Applying'/'Separating'/'Static')
  - `HouseComparisonFactory(t, n).get_house_comparison()` — returns `first_points_in_second_houses` list
  - `PointInHouseModel` fields: `point_name`, `point_sign`, `point_degree`, `projected_house_number`
  - `planet.retrograde` (bool) and `planet.speed` (float deg/day) confirmed on all 10 planets
  - `ActiveAspect` is a TypedDict with `name` (Literal) and `orb` (int) fields
  - Transit planet positions confirmed location-independent when same UTC moment used
- `.planning/research/STACK.md` — prior v1.1 research confirming zero new dependencies needed
- `.planning/research/PITFALLS.md` — prior research on timezone handling and natal regression prevention

### Secondary (MEDIUM confidence)
- Kerykeion GitHub (https://github.com/g-battaglia/kerykeion) — factory architecture, class list
- Kerykeion package `__doc__` — class inventory including `TransitsTimeRangeFactory`, `EphemerisDataFactory`, `AspectsFactory`, `HouseComparisonFactory`

### Tertiary (LOW confidence)
- Prior STACK.md mention of `TransitsTimeRangeFactory` for snapshot — SUPERSEDED by direct testing. For a single-date snapshot, `AspectsFactory.dual_chart_aspects()` is simpler and more direct. `TransitsTimeRangeFactory` + `EphemerisDataFactory` is the correct approach for Phase 8 (date ranges), not Phase 7.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — verified against installed Kerykeion 5.7.2 with working code
- Architecture: HIGH — all key API calls tested end-to-end with Albert Einstein profile
- Pitfalls: HIGH — most pitfalls verified empirically (UTC timezone confirmed, retrograde confirmed, ActiveAspect TypedDict confirmed)

**Research date:** 2026-02-17
**Valid until:** 2026-03-17 (30 days — Kerykeion pinned at 5.7.2, APIs are stable)
