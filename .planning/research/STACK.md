# Technology Stack

**Project:** generate-natal-chart v1.1 (Transits & Progressions)
**Researched:** 2026-02-17
**Confidence:** HIGH

## Recommended Stack

### Core Framework (NO CHANGES)
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Kerykeion | 5.7.2 | Astrological calculations, chart generation | Native transit support via `TransitsTimeRangeFactory` + `EphemerisDataFactory`. Modern factory architecture (v5+). Confirmed compatibility with existing natal chart system. |
| Python | 3.11 | Runtime environment | Required for pyswisseph prebuilt wheels. Already validated in v1.0. |
| pyswisseph | (bundled with Kerykeion) | Swiss Ephemeris engine | High-precision planetary positions. Accessed via `swisseph` module through Kerykeion. Supports `calc_ut()` for arbitrary date calculations. |

### NEW Transit/Progression Capabilities (Kerykeion 5.7.2 Built-In)

| Component | Purpose | Integration Point |
|-----------|---------|-------------------|
| `TransitsTimeRangeFactory` | Calculate transits over time periods | Accepts `AstrologicalSubjectModel` (natal chart) + `EphemerisDataFactory` output. Returns transit aspects between transiting and natal positions. |
| `EphemerisDataFactory` | Generate time-series planetary positions | Creates planetary snapshots at configurable intervals (days/hours/minutes). Max 730 days, 8760 hours, or 525600 minutes by default. |
| `PlanetaryReturnFactory` | Solar/lunar returns | Calculates exact return moments using Swiss Ephemeris. Generates full charts for return times. NOT for secondary progressions. |
| `swisseph.calc_ut()` | Direct Swiss Ephemeris access | Low-level function for calculating planetary positions at any Julian Day. Required for implementing secondary progressions and solar arc (NOT natively supported by Kerykeion). |

### Supporting Libraries (NO CHANGES)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| python-slugify | latest | Profile directory naming | Already used in v1.0 for `~/.natal-charts/{slug}/`. No changes needed. |
| pydantic | 2.x | Data validation (Kerykeion dependency) | Bundled with Kerykeion. Powers `AstrologicalSubjectModel` and `ChartDataModel`. Already in use. |
| pytz | latest | Timezone handling (Kerykeion dependency) | Bundled with Kerykeion. No changes needed. |

### NEW Dependencies Required

**NONE.** All transit and progression features can be implemented using existing Kerykeion 5.7.2 + direct `swisseph` access.

## Installation

```bash
# Existing dependencies (no changes)
pip install -r backend/requirements.txt
```

```
# backend/requirements.txt (UNCHANGED)
kerykeion==5.7.2
python-slugify
```

## What Kerykeion 5.7.2 Provides Natively

### Transits (BUILT-IN)
**Class:** `TransitsTimeRangeFactory`
**Status:** Fully supported
**Capabilities:**
- Compare natal chart positions against time-series ephemeris data
- Calculate aspects between transiting and natal planets
- Configurable active points (Sun, Moon, planets, asteroids, angles, fixed stars, Arabic parts)
- Configurable aspect types (conjunction, opposition, trine, square, sextile, quintile)
- Configurable orbs per aspect type
- Returns structured transit moments with aspect details

**Integration:**
```python
# 1. Load natal chart (existing v1.0 functionality)
natal = AstrologicalSubjectFactory.from_birth_data(...)

# 2. Generate ephemeris for date range
from datetime import datetime
ephemeris_factory = EphemerisDataFactory(
    start_datetime=datetime(2026, 1, 1),
    end_datetime=datetime(2026, 12, 31),
    step_type="days",
    step=1,
    lat=natal.lat,
    lng=natal.lng,
    tz_str=natal.tz_str
)
ephemeris_subjects = ephemeris_factory.get_ephemeris_data_as_astrological_subjects()

# 3. Calculate transits
transit_factory = TransitsTimeRangeFactory(
    natal_chart=natal,
    ephemeris_data_points=ephemeris_subjects,
    active_points=["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"],
    active_aspects=[
        {"name": "conjunction", "orb": 10},
        {"name": "opposition", "orb": 10},
        {"name": "trine", "orb": 8},
        {"name": "square", "orb": 6}
    ]
)
transits = transit_factory.get_transit_moments()
```

**Data Structure:**
Returns list of transit moments with:
- `transit_date`: Date/time of transit
- `transiting_point`: Which planet/point is transiting
- `natal_point`: Which natal point is being aspected
- `aspect_name`: Type of aspect (e.g., "conjunction")
- `orb`: Exact orb of aspect
- `aspect_angle`: Expected angle for this aspect type

### Planetary Returns (BUILT-IN)
**Class:** `PlanetaryReturnFactory`
**Status:** Fully supported (solar/lunar returns)
**Capabilities:**
- Calculate exact moment when Sun/Moon returns to natal position
- Generate full astrological chart for return moment
- Supports online (GeoNames) or offline (coordinates) location lookup

**NOT for secondary progressions** — this is for solar/lunar returns (annual/monthly charts cast for return moment at current location).

### Secondary Progressions (NOT BUILT-IN)
**Status:** Must implement manually
**Method:** Day-for-a-year symbolic formula
**Implementation:**
```python
# Calculate progressed date for age 30 (born 1990-06-15)
birth_date = datetime(1990, 6, 15, 14, 30)
age_in_years = 30
progressed_date = birth_date + timedelta(days=age_in_years)
# = 1990-07-15 14:30 (30 days after birth = 30 years progressed)

# Generate progressed chart using swisseph.calc_ut()
# OR create an AstrologicalSubject for the progressed date
# with NATAL location (not current location)
progressed_subject = AstrologicalSubjectFactory.from_birth_data(
    name=f"{original_name} Progressed Age {age_in_years}",
    year=progressed_date.year,
    month=progressed_date.month,
    day=progressed_date.day,
    hour=progressed_date.hour,
    minute=progressed_date.minute,
    lat=natal_lat,  # NATAL location
    lng=natal_lng,
    tz_str=natal_tz_str
)
```

**Rationale:** Kerykeion doesn't have a dedicated `ProgressionFactory`. Instead:
1. Calculate progressed date (birth date + age in days)
2. Create `AstrologicalSubject` for that progressed date at NATAL location
3. Compare progressed positions to natal positions
4. Use existing `AspectsFactory` for progressed-to-natal aspects

### Solar Arc Directions (NOT BUILT-IN)
**Status:** Must implement manually
**Method:** Calculate solar arc, apply to all natal positions
**Implementation:**
```python
# 1. Calculate natal Sun position
natal_sun_longitude = natal.sun.abs_pos  # e.g., 84.123 degrees

# 2. Calculate progressed Sun position (day-for-a-year)
progressed_date = birth_date + timedelta(days=age_in_years)
# Use swisseph.calc_ut() to get Sun position on progressed_date
import swisseph as swe
jd = swe.julday(progressed_date.year, progressed_date.month, progressed_date.day,
                progressed_date.hour + progressed_date.minute/60.0)
progressed_sun_data = swe.calc_ut(jd, swe.SUN)
progressed_sun_longitude = progressed_sun_data[0]

# 3. Calculate solar arc
solar_arc = progressed_sun_longitude - natal_sun_longitude

# 4. Apply arc to ALL natal positions
solar_arc_moon = natal.moon.abs_pos + solar_arc
solar_arc_mercury = natal.mercury.abs_pos + solar_arc
# ... etc for all planets

# 5. Convert back to sign + degree format using existing utilities
# 6. Check aspects between solar arc positions and natal positions
```

**Rationale:** Kerykeion doesn't have a solar arc factory. Must:
1. Calculate solar arc manually (progressed Sun - natal Sun)
2. Add arc to all natal positions
3. Use `swisseph.calc_ut()` for precise progressed Sun calculation
4. Reuse existing aspect calculation logic

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `immanuel-python` library | Adds unnecessary dependency. Kerykeion 5.7.2 already has transits. Progressions would require implementing day-for-a-year logic regardless of library choice. | Kerykeion's `TransitsTimeRangeFactory` + manual progression calculation |
| `flatlib` library | Deprecated, no SVG generation, incompatible with existing v1.0 codebase. | Kerykeion (already in use) |
| Direct `pyswisseph` for transits | Reinventing the wheel. Kerykeion's `TransitsTimeRangeFactory` provides structured transit data with aspect detection. | `TransitsTimeRangeFactory` + `EphemerisDataFactory` |
| Custom ephemeris generation | Kerykeion's `EphemerisDataFactory` handles time-series generation with safety limits (max 730 days daily data). | `EphemerisDataFactory` |
| Separate progression library | No Python library provides Kerykeion-compatible progression models. Day-for-a-year calculation is trivial (`birth_date + timedelta(days=age)`). | Manual calculation + existing `AstrologicalSubjectFactory` |

## Stack Patterns by Feature

### Current Transits (Snapshot)
**Use:**
- `EphemerisDataFactory` with `start_datetime=now`, `end_datetime=now`, `step=1`, `step_type="days"`
- Creates single ephemeris point for current moment
- `TransitsTimeRangeFactory` with natal chart + single ephemeris point
- Returns current transiting aspects

**Implementation:**
```python
now = datetime.now()
ephemeris = EphemerisDataFactory(now, now, step_type="days", step=1, ...)
current_ephemeris = ephemeris.get_ephemeris_data_as_astrological_subjects()
transits = TransitsTimeRangeFactory(natal, current_ephemeris, ...)
current_aspects = transits.get_transit_moments()
```

### Transit Timeline (Date Range)
**Use:**
- `EphemerisDataFactory` with configurable date range + step interval
- Default: daily steps (86400 seconds between points)
- Safety limits: max 730 days (2 years) for daily data
- `TransitsTimeRangeFactory` returns chronological list of transit moments

**Implementation:**
```python
# 30-day transit forecast
start = datetime.now()
end = start + timedelta(days=30)
ephemeris = EphemerisDataFactory(start, end, step_type="days", step=1, ...)
ephemeris_points = ephemeris.get_ephemeris_data_as_astrological_subjects()
transits = TransitsTimeRangeFactory(natal, ephemeris_points, ...)
timeline = transits.get_transit_moments()
```

### Secondary Progressions
**Use:**
- Manual date calculation: `birth_date + timedelta(days=age_in_years)`
- `AstrologicalSubjectFactory.from_birth_data()` with progressed date at NATAL location
- Existing aspect calculation between progressed and natal charts

**Implementation:**
```python
# Age 35 progressions
progressed_date = birth_date + timedelta(days=35)
progressed_chart = AstrologicalSubjectFactory.from_birth_data(
    name="Progressed Age 35",
    year=progressed_date.year,
    month=progressed_date.month,
    day=progressed_date.day,
    hour=progressed_date.hour,
    minute=progressed_date.minute,
    lat=natal_lat,  # CRITICAL: natal location, not current
    lng=natal_lng,
    tz_str=natal_tz_str
)
# Compare progressed_chart.sun, progressed_chart.moon, etc. to natal positions
```

### Solar Arc Directions
**Use:**
- `swisseph.calc_ut()` for precise progressed Sun calculation
- Manual arc calculation: `progressed_sun_longitude - natal_sun_longitude`
- Apply arc to all natal positions
- Aspect detection between solar arc positions and natal positions

**Implementation:**
```python
import swisseph as swe

# Calculate progressed Sun
progressed_date = birth_date + timedelta(days=age_in_years)
jd = swe.julday(progressed_date.year, progressed_date.month,
                progressed_date.day, progressed_date.hour + progressed_date.minute/60.0)
prog_sun = swe.calc_ut(jd, swe.SUN)
solar_arc = prog_sun[0] - natal.sun.abs_pos

# Apply to all natal positions
solar_arc_positions = {
    "Sun": natal.sun.abs_pos + solar_arc,
    "Moon": natal.moon.abs_pos + solar_arc,
    "Mercury": natal.mercury.abs_pos + solar_arc,
    # ... etc
}

# Convert to sign + degree and check aspects
```

## Version Compatibility

| Package | Version | Compatible With | Notes |
|---------|---------|-----------------|-------|
| Kerykeion | 5.7.2 | Python 3.11 | Pinned. Factory architecture introduced in v5.0. Transit support in 5.7.x. DO NOT UPGRADE without testing. |
| pyswisseph | (bundled) | Kerykeion 5.7.2 | Accessed via `import swisseph as swe` when Kerykeion imported. No separate installation needed. |
| pydantic | 2.x | Kerykeion 5.7.2 | Kerykeion dependency. Models use Pydantic v2 syntax. |
| Python | 3.11 | pyswisseph prebuilt wheels | DO NOT UPGRADE to 3.13 without verifying pyswisseph wheel availability. |

## Integration with Existing v1.0 Backend

### Existing Assets (Reusable)
| Asset | Location | Reuse For |
|-------|----------|-----------|
| `AstrologicalSubjectFactory` usage | `backend/astrology_calc.py` | Load natal chart profiles for transit comparison |
| JSON profile structure | `~/.natal-charts/{slug}/chart.json` | Store transit/progression data alongside natal data |
| Argument parsing pattern | `backend/astrology_calc.py` main() | Add `--transits`, `--progressions`, `--solar-arc` flags |
| Exit code strategy | Return 0/1/2 for success/validation/parsing errors | Maintain for skill compatibility |
| Element/modality distribution | Existing calculations | NOT needed for transits (transits don't have distributions) |

### Integration Points
1. **Load natal chart:** Use existing profile loading mechanism (`~/.natal-charts/{slug}/chart.json`)
2. **Create transits:** New `TransitsTimeRangeFactory` invocation with loaded natal `AstrologicalSubjectModel`
3. **Store transits:** Either fresh calculation each time OR optional JSON snapshot in profile subfolder
4. **Interpretation guide:** Extend existing guide prompt injection with transit/progression context

### Code Additions (Estimated)
- **Transits:** ~150 LOC (ephemeris generation + transit factory + JSON serialization)
- **Secondary progressions:** ~80 LOC (date calculation + chart generation + comparison)
- **Solar arc:** ~120 LOC (arc calculation + position adjustment + aspect detection)
- **Total:** ~350 LOC (monolithic file grows from 1,070 to ~1,420 LOC)

## Sources

**HIGH confidence sources:**
- [Kerykeion 5.7.2 PyPI](https://pypi.org/project/kerykeion/) — Version confirmation, dependencies
- [Kerykeion GitHub](https://github.com/g-battaglia/kerykeion) — Factory architecture, transit support confirmation
- [Kerykeion API Documentation](https://www.kerykeion.net/pydocs/kerykeion.html) — `TransitsTimeRangeFactory`, `EphemerisDataFactory`, `PlanetaryReturnFactory` classes
- Local installation verification — Confirmed Kerykeion 5.7.2 installed with `TransitsTimeRangeFactory`, `EphemerisDataFactory`, `PlanetaryReturnFactory` available

**MEDIUM confidence sources:**
- [Swiss Ephemeris Programming Interface](https://www.astro.com/swisseph/swephprg.htm) — `calc_ut()` function documentation
- [pyswisseph GitHub](https://github.com/astrorigin/pyswisseph) — Python bindings for Swiss Ephemeris

**LOW confidence sources (astrological technique validation only, NOT library-specific):**
- [Cafe Astrology - Secondary Progressions](https://cafeastrology.com/secondaryprogressions.html) — Day-for-a-year formula validation
- [Astro-Seek Solar Arc Calculator](https://horoscopes.astro-seek.com/solar-arc-directions-calculator) — Solar arc calculation method validation

**NOT found (confirmed absence):**
- Kerykeion native secondary progression factory (searched GitHub issues, documentation, API reference)
- Kerykeion native solar arc factory (searched GitHub issues, documentation, API reference)
- Built-in progression chart SVG generation (PlanetaryReturnFactory is for solar/lunar returns, NOT progressions)

---

**Stack Research Summary:**

**ZERO new dependencies required.** Kerykeion 5.7.2 provides:
- ✓ **Transits:** `TransitsTimeRangeFactory` + `EphemerisDataFactory` (built-in, production-ready)
- ✗ **Secondary progressions:** Manual implementation (trivial day-for-a-year + existing `AstrologicalSubjectFactory`)
- ✗ **Solar arc:** Manual implementation (requires `swisseph.calc_ut()` + arc arithmetic)

**Why no additional libraries:**
1. Kerykeion's transit support is comprehensive (configurable points, aspects, orbs, time ranges)
2. No Python library provides Kerykeion-compatible progression models
3. Secondary progression calculation is a simple date offset (`birth_date + timedelta(days=age)`)
4. Solar arc is arc calculation + position arithmetic (40 lines of code, not worth a dependency)
5. Adding `immanuel-python` or similar would create model incompatibility with existing Kerykeion-based profiles

**Recommendation:** Extend existing monolithic `backend/astrology_calc.py` with ~350 LOC for transits (using Kerykeion factories) + progressions (manual calculation) + solar arc (manual calculation). Maintains architectural consistency with v1.0.

---
*Stack research for: generate-natal-chart v1.1 (Transits & Progressions)*
*Researched: 2026-02-17*
*Confidence: HIGH (verified with local Kerykeion 5.7.2 installation + official documentation)*
