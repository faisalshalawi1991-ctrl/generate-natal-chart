# Phase 10: Solar Arc Directions - Research

**Researched:** 2026-02-17
**Domain:** Solar arc directions (SA), true arc vs mean arc (Naibod), Swiss Ephemeris swe.calc_ut(), manual aspect calculation, Python CLI extension
**Confidence:** HIGH

## Summary

Phase 10 adds a `--solar-arcs SLUG` CLI mode that calculates solar arc directed positions against an existing natal chart profile. Solar arc directions apply a single constant arc — the distance the progressed Sun has traveled since birth — to every natal planet, angle, and point simultaneously. The result is a "directed chart" where each natal position is shifted by the same number of degrees, then compared against the fixed natal chart for aspects.

Solar arc directions are fundamentally different from secondary progressions (Phase 9), even though both use the day-for-year concept to derive the arc. In secondary progressions, each planet moves independently at its actual ephemeris speed. In solar arc directions, every planet moves by the same arc (the Sun's progressed motion). This means SA directed positions **cannot be created using `AstrologicalSubjectFactory.from_birth_data()`** — they are not real sky positions at any date. Instead, directed positions are computed as pure arithmetic: `directed_lon = (natal_lon + arc) % 360`. This makes Phase 10 significantly simpler than Phase 9: no `from_birth_data()` calls are needed for the directed positions, and no monthly Moon report is required.

Two arc calculation methods are supported (SARC-03): the **true arc** (the actual distance the progressed Sun traveled, computed via `swe.calc_ut()` at the progressed JD) and the **mean arc** (the Naibod constant of 0.98564733 degrees per year multiplied by elapsed years). The true arc is the default and more accurate method; the mean arc is a simplification that assumes constant solar speed. For young subjects, the two methods differ by less than 1 degree. For extreme ages (80+ years), the difference grows to 2-3 degrees due to accumulated seasonal variation in the Sun's speed. The implementation reuses `compute_progressed_jd()` from Phase 9 to compute the progressed JD for the true arc Sun lookup.

**Primary recommendation:** Add `--solar-arcs SLUG` accepting the existing `--target-date YYYY-MM-DD` (default: today UTC) and a new `--arc-method [true|mean]` flag (default: `true`). Compute the arc entirely from natal profile `abs_position` fields and one `swe.calc_ut()` call. Calculate SA-to-natal aspects manually (no `AspectsFactory`). Total implementation is approximately 150-200 lines added to `astrology_calc.py`.

## Standard Stack

### Core (No New Dependencies)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pyswisseph | installed | `swe.calc_ut()` to get progressed Sun longitude for true arc | Already installed; one call suffices for the entire solar arc computation |
| Python | 3.11 | Runtime | Required for pyswisseph prebuilt wheels |
| Kerykeion | 5.7.2 | `load_natal_profile()` to read chart.json | Already installed; no new API surface needed for SA directions |

### No Kerykeion Subject Creation Required
Unlike Phase 9, Phase 10 does **not** call `AstrologicalSubjectFactory.from_birth_data()` for directed positions. SA directed positions are pure arithmetic from natal `abs_position` fields stored in `chart.json`. The natal subject loaded by `load_natal_profile()` provides the natal `abs_position` values needed.

### Reused from Phase 9
| Function/Constant | Phase | Use in Phase 10 |
|------------------|-------|-----------------|
| `compute_progressed_jd(birth_jd, target_jd)` | Phase 9 | Compute progressed JD for the true arc Sun lookup |
| `load_natal_profile(slug)` | Phase 7+ | Load natal chart.json with `abs_position` fields |
| `valid_query_date(s)` | Phase 7 | Reuse for `--target-date` input validation |
| `MAJOR_PLANETS` | Phase 7 | List of 10 planets for directed and natal aspect points |

### New Constant Needed
```python
# Solar arc orb: 1 degree for all aspects (tight, professional standard)
# Source: Noel Tyl, multiple web sources — 1 degree = 1 year window in SA timing
SARC_DEFAULT_ORBS = {
    'conjunction': 1.0,
    'opposition': 1.0,
    'trine': 1.0,
    'square': 1.0,
    'sextile': 1.0,
}

# Naibod mean arc constant (Sun's mean diurnal motion in degrees per year)
NAIBOD_ARC = 0.98564733  # degrees per year; equals Sun's mean daily motion
```

Note: `SARC_DEFAULT_ORBS` is a plain dict (not a list of `ActiveAspect` objects) because Phase 10 does not use `AspectsFactory` — aspects are computed manually.

### No New pip Dependencies
```bash
# Verify swisseph is already available:
/c/NEW/backend/venv/Scripts/python -c "import swisseph as swe; print(swe.calc_ut(swe.julday(2026, 2, 17, 12.0), swe.SUN)[0][0])"
# Expected: approximately 328.xx (Sun in Pisces, February)
```

## Architecture Patterns

### Recommended File Structure (No New Files)
```
backend/
└── astrology_calc.py   # Add solar arc functions after Phase 9 progressions section
    ├── [existing natal + Phase 7-9 functions — UNTOUCHED]
    ├── SARC_DEFAULT_ORBS                    # New constant (dict, 1-degree for all 5 aspects)
    ├── NAIBOD_ARC                           # New constant (0.98564733 degrees/year)
    ├── compute_solar_arc()                  # New: computes true or mean arc for target date
    ├── build_sarc_aspects()                 # New: manual aspect calculation (no AspectsFactory)
    ├── build_solar_arc_json()               # New: assembles complete SA directions JSON dict
    ├── calculate_solar_arcs()               # New: orchestrates full Phase 10 pipeline
    └── [main() — add --solar-arcs routing before --progressions routing]
```

### Pattern 1: Compute Solar Arc (True and Mean Methods)
**What:** Derive the arc to add to all natal points.
**When to use:** The foundational calculation for all of Phase 10.

```python
# Source: verified against local Kerykeion 5.7.2 + swisseph installation (2026-02-17)
import swisseph as swe

NAIBOD_ARC = 0.98564733  # degrees per year (Sun's mean daily motion)

def compute_solar_arc(birth_jd, target_jd, natal_sun_lon, method='true'):
    """
    Compute the solar arc for a target date.

    Args:
        birth_jd: Julian Day number of the birth moment
        target_jd: Julian Day number of the target date
        natal_sun_lon: Natal Sun absolute longitude (from chart.json abs_position)
        method: 'true' for actual progressed Sun position, 'mean' for Naibod constant

    Returns:
        float: Solar arc in degrees (0-360)
    """
    elapsed_years = (target_jd - birth_jd) / 365.25

    if method == 'mean':
        # Naibod mean arc: fixed rate × elapsed years
        return (elapsed_years * NAIBOD_ARC) % 360
    else:
        # True arc: progressed Sun longitude - natal Sun longitude
        # progressed_jd = birth_jd + elapsed_years (day-for-year formula)
        progressed_jd = compute_progressed_jd(birth_jd, target_jd)  # reuse Phase 9
        prog_sun_data, _ = swe.calc_ut(progressed_jd, swe.SUN)
        prog_sun_lon = prog_sun_data[0]
        return (prog_sun_lon - natal_sun_lon) % 360


# Verification: Einstein (birth 1879-03-14), target 2026-02-17 (age ~146.9 years)
# birth_jd = 2407422.979  natal_sun_lon = 353.499 (Pis 23.5)
# True arc:  141.935 degrees   (progressed Sun at Leo 15.43)
# Mean arc:  144.821 degrees   (146.93 * 0.98564733)
# Difference: 2.886 degrees    (expected for extreme age)

# Verification: 1990-06-15 birth, target 2025-01-01 (age ~34.5 years)
# True arc:  32.958 degrees
# Mean arc:  34.053 degrees
# Difference: 1.095 degrees    (seasonal effect: summer birth, Sun slower in June)
```

**Key finding (verified empirically):**
- Summer births (June): true arc < mean arc (Sun moves slower near aphelion, ~0.955 deg/day vs 0.986 mean)
- Winter births (December): true arc > mean arc (Sun moves faster near perihelion, ~1.018 deg/day vs 0.986 mean)
- For ages 0-50: difference is typically 0.5-1.5 degrees (within the 1-degree orb range)
- For ages 80+: difference can reach 2-5 degrees (extreme cases)

### Pattern 2: Apply Arc to Natal Positions
**What:** Add the arc to every natal planet and angle longitude.
**When to use:** Core of SA directed chart computation.

```python
# Source: verified against local swisseph installation (2026-02-17)
# No from_birth_data() call — pure arithmetic

def apply_arc_to_natal(natal_positions, arc):
    """
    Apply solar arc to a dict of natal absolute longitudes.

    Args:
        natal_positions: dict of {name: abs_longitude} from chart.json
        arc: float solar arc in degrees

    Returns:
        dict of {name: directed_longitude} (all positions shifted by arc)
    """
    return {name: (lon + arc) % 360 for name, lon in natal_positions.items()}


# Reconstruct natal planet positions from chart.json:
natal_planets = {
    p['name']: p['abs_position']
    for p in natal_data['planets']
    if p['name'] in MAJOR_PLANETS
}

# Reconstruct natal angle positions from chart.json:
natal_angles = {
    a['name']: a['abs_position']
    for a in natal_data['angles']
    if a['name'] in ['ASC', 'MC']
}

# Reconstruct natal house cusps from chart.json (sign+degree to abs_lon):
SIGN_OFFSETS = {
    'Ari': 0, 'Tau': 30, 'Gem': 60, 'Can': 90,
    'Leo': 120, 'Vir': 150, 'Lib': 180, 'Sco': 210,
    'Sag': 240, 'Cap': 270, 'Aqu': 300, 'Pis': 330
}
natal_house_cusps = {
    h['number']: SIGN_OFFSETS[h['sign']] + h['degree']
    for h in natal_data['houses']
}
# Note: natal_data['houses'] does NOT store abs_position; reconstruct from sign+degree
```

**Critical:** `natal_data['houses']` entries have `sign` and `degree` but NO `abs_position` key (verified against Einstein profile). Planets and angles DO have `abs_position`. House cusp absolute longitudes must be reconstructed using `SIGN_OFFSETS`.

### Pattern 3: Manual SA-to-Natal Aspect Calculation
**What:** Find aspects between SA directed positions and natal positions with tight orb.
**When to use:** SARC-02. Cannot use `AspectsFactory.dual_chart_aspects()` because directed positions are not a Kerykeion subject.

```python
# Source: verified against local installation (2026-02-17)
# Must implement manually — no AspectsFactory equivalent for non-subject positions

SARC_ASPECT_ANGLES = {
    'conjunction': 0,
    'opposition': 180,
    'trine': 120,
    'square': 90,
    'sextile': 60,
}

def angular_distance(lon1, lon2):
    """Compute smallest angular distance between two ecliptic longitudes."""
    diff = abs(lon1 - lon2) % 360
    return 360 - diff if diff > 180 else diff


def build_sarc_aspects(directed_positions, natal_positions, max_orb=1.0):
    """
    Find aspects between SA directed and natal positions.

    Args:
        directed_positions: dict of {name: directed_lon} (all points + angles)
        natal_positions: dict of {name: natal_lon} (all points + angles)
        max_orb: maximum orb in degrees (default 1.0)

    Returns:
        List[dict]: aspect entries sorted by orb
    """
    aspects = []
    for d_name, d_lon in directed_positions.items():
        for n_name, n_lon in natal_positions.items():
            dist = angular_distance(d_lon, n_lon)
            for asp_name, asp_angle in SARC_ASPECT_ANGLES.items():
                orb = abs(dist - asp_angle)
                if orb <= max_orb:
                    aspects.append({
                        'directed_point': d_name,
                        'natal_point': n_name,
                        'aspect': asp_name,
                        'orb': round(orb, 3),
                    })
    return sorted(aspects, key=lambda x: x['orb'])


# Verification: Einstein 2026-02-17, true arc = 141.935 degrees, 1-degree orb
# 6 aspects found within 1.0 degree:
# SA Venus      sextile    natal ASC    orb=0.014
# SA Uranus     sextile    natal Sun    orb=0.275
# SA Pluto      opposition natal Venus  orb=0.314
# SA Mercury    square     natal Pluto  orb=0.336
# SA Venus      opposition natal MC     orb=0.425
# SA ASC        square     natal Uranus orb=0.431
```

### Pattern 4: Applying vs Separating Detection
**What:** Determine if a SA aspect is applying (approaching exactness) or separating (past exactness).
**When to use:** Output enrichment for SA aspects.

```python
# Source: verified against local installation (2026-02-17)
# Method: compare orb at target_jd vs orb at target_jd + 365.25 days (one year forward)
# If future orb < current orb: applying
# If future orb > current orb: separating

def is_aspect_applying(directed_lon_now, directed_lon_future, natal_lon, asp_angle):
    """
    Returns True if SA aspect is applying (orb decreasing toward exact).

    Args:
        directed_lon_now: directed point longitude at target date
        directed_lon_future: directed point longitude 1 year later
        natal_lon: fixed natal point longitude
        asp_angle: aspect angle (0, 60, 90, 120, 180)
    """
    orb_now = abs(angular_distance(directed_lon_now, natal_lon) - asp_angle)
    orb_future = abs(angular_distance(directed_lon_future, natal_lon) - asp_angle)
    return orb_future < orb_now

# Implementation: compute arc at target_jd + 365.25 (1 Julian year later)
# arc_future = compute_solar_arc(birth_jd, target_jd + 365.25, natal_sun_lon, method)
# directed_future = (natal_lon + arc_future) % 360
# Check if orb decreases -> applying
```

**Verified result for Einstein (2026-02-17):** All 6 aspects within 1-degree are Separating (arc has already passed the exact point in the past year). This is expected for a very old chart. For younger charts with active progressions, applying aspects will appear.

### Pattern 5: CLI Arguments and Routing
**What:** Add `--solar-arcs` flag alongside existing flags, reusing `--target-date`.
**When to use:** Routing in `main()`.

```python
# Add to parser in main():
parser.add_argument(
    '--solar-arcs',
    metavar='SLUG',
    dest='solar_arcs',
    help='Calculate solar arc directions for an existing chart profile (e.g., albert-einstein)'
)
parser.add_argument(
    '--arc-method',
    choices=['true', 'mean'],
    default='true',
    dest='arc_method',
    help='Solar arc calculation method: true (default, actual progressed Sun) or mean (Naibod constant)'
)
# --target-date is ALREADY DEFINED in Phase 9 (shared, no redefinition needed)

# Routing in main() — add BEFORE --progressions check:
if args.solar_arcs:
    return calculate_solar_arcs(args)
```

**Note on `--target-date` sharing:** The `--target-date` argument defined in Phase 9 for `--progressions` can be reused for `--solar-arcs` without redefinition. argparse stores it as `args.target_date` and both modes read it. No conflict occurs because only one mode runs per invocation (early-return pattern). If neither `--target-date` nor `--age` is provided, default to today UTC (same as Phase 9 behavior).

**Note on `--age` sharing:** The `--age` argument from Phase 9 can also be reused for solar arcs. If `--age N` is given, compute `target_jd = birth_jd + N * 365.25`. This provides age-based solar arc lookup without new flags.

### Pattern 6: Complete JSON Output Structure
**What:** The solar arc directions output printed to stdout.

```python
# Target output structure for solar arc directions
{
    "meta": {
        "natal_name": "Albert Einstein",
        "natal_slug": "albert-einstein",
        "target_date": "2026-02-17",
        "arc_degrees": 141.935,              # The solar arc applied (true or mean)
        "arc_method": "true",                # 'true' or 'mean'
        "elapsed_years": 146.93,
        "chart_type": "solar_arc_directions",
        "calculated_at": "2026-02-17T12:00:00+00:00",
        "orbs_used": {"conjunction": 1.0, "opposition": 1.0, "trine": 1.0,
                      "square": 1.0, "sextile": 1.0}
    },
    "directed_planets": [
        {
            "name": "Sun",
            "natal_sign": "Pis",
            "natal_degree": 23.50,
            "natal_abs_position": 353.499,
            "directed_abs_position": 135.434,
            "directed_sign": "Leo",
            "directed_degree": 15.43
        },
        # ... 10 planets total
    ],
    "directed_angles": [
        {
            "name": "ASC",
            "natal_abs_position": 98.923,
            "directed_abs_position": 240.858,
            "directed_sign": "Sco",
            "directed_degree": 0.86
        },
        # ASC and MC (DSC and IC derivable)
    ],
    "aspects": [
        {
            "directed_point": "Venus",
            "natal_point": "ASC",
            "aspect": "sextile",
            "orb": 0.014,
            "applying": false,
            "movement": "Separating"
        },
        # ... all aspects within 1.0 degree orb, sorted by orb
    ]
}
```

### Anti-Patterns to Avoid
- **Using `from_birth_data()` for directed positions:** SA directed positions are NOT actual sky positions at any date. Calling `from_birth_data()` with the progressed date gives secondary progressions (each planet at its own speed), not solar arcs (all planets shifted by the same arc). Do not reuse the Phase 9 progressed subject creation for Phase 10.
- **Using `AspectsFactory.dual_chart_aspects()` for SA aspects:** `AspectsFactory` requires two `AstrologicalSubjectModel` objects. SA directed positions are not a subject — they're plain floats. Use the manual aspect calculation function instead.
- **Not reconstructing house cusp abs_positions from sign+degree:** `natal_data['houses']` entries lack `abs_position`. Use `SIGN_OFFSETS[sign] + degree` to convert. Planets and angles DO have `abs_position` directly.
- **Using `ActiveAspect` objects for SARC_DEFAULT_ORBS:** Phase 9 used `ActiveAspect` objects because `AspectsFactory` requires them. Phase 10 uses a plain dict because aspects are computed manually.
- **Adding `--solar-arcs` routing AFTER `--progressions` in main():** The routing must follow the established order. New mode checks should be added BEFORE existing mode checks to prevent argument pollution. Convention: `--list` first, then `--solar-arcs`, then `--progressions`, then `--timeline`, then `--transits`.
- **Not including natal context in directed planet output:** Each directed planet entry should include both the natal position (for reference) and the directed position. This is essential for Claude's interpretation: knowing where a planet started and where it is directed conveys the complete picture.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Solar arc computation | Custom ephemeris lookup loop | `swe.calc_ut(progressed_jd, swe.SUN)` for true arc; `elapsed_years * NAIBOD_ARC` for mean | One call to `swe.calc_ut()` gives the progressed Sun longitude; mean arc is a trivial multiplication |
| Progressed JD | Date arithmetic with datetime | `compute_progressed_jd()` already defined in Phase 9 | Reuse: `birth_jd + (target_jd - birth_jd) / 365.25` |
| Angular distance (wrap-around) | Manual abs() with conditional | `angular_distance()` helper function (define once, reuse) | Zodiac wrap-around at 0/360 requires `diff > 180` correction |
| Sign conversion for directed planets | Manual sign offset lookup | `position_to_sign_degree()` already defined in astrology_calc.py (line 984) | Converts abs_position to (sign, degree) — already exists in codebase |
| Profile loading | Open chart.json manually | `load_natal_profile(slug)` from Phase 7 | Returns parsed JSON with all `abs_position` fields pre-populated |

**Key insight:** Phase 10 is simpler than Phase 9. No `from_birth_data()` calls, no monthly Moon loop, no `AspectsFactory`. The entire calculation is: one `swe.calc_ut()` call (for true arc method) + arithmetic on stored natal positions + a simple nested loop for aspects. Total wall time < 5ms.

## Common Pitfalls

### Pitfall 1: Confusing SA Directed Positions with Secondary Progressed Positions
**What goes wrong:** Developer uses `compute_progressed_jd()` + `from_birth_data()` to create the directed subject, treating Phase 10 like Phase 9. The output shows secondary progressed Mars at ~35° (actual ephemeris position) instead of SA directed Mars at ~44° (natal Mars + arc). These are different techniques with different outputs.
**Why it happens:** Both techniques use day-for-year to compute the arc, so it's easy to assume the same Kerykeion subject creation approach applies.
**How to avoid:** Remember: SA directions add ONE constant arc to ALL natal positions. Secondary progressions compute each planet's actual sky position on the progressed date (each planet moves at its own speed). For SA: `directed_lon = natal_lon + arc`. For SP: `progressed_lon = swe.calc_ut(progressed_jd, planet_id)`. These are always different for planets other than the Sun.
**Warning signs:** SA Mars position equals the secondary progressed Mars position — this is almost never true (Mars moves ~0.52°/day; Sun moves ~0.985°/day, so their arcs diverge quickly).

### Pitfall 2: True vs Mean Arc Divergence at Extreme Ages
**What goes wrong:** For a 147-year-old chart (Einstein), the true arc is 141.94° and the mean arc is 144.82° — a difference of 2.89 degrees. An aspect that appears within 1-degree orb in one method may not appear in the other.
**Why it happens:** The Sun's actual daily speed varies by ~7% between summer (0.953°/day near aphelion) and winter (1.019°/day near perihelion). Over many decades, these seasonal variations accumulate.
**How to avoid:** Always output the arc method used (`arc_method` in meta), the arc value (`arc_degrees` in meta), and the elapsed years. This allows the user to understand which method they're using. Document the seasonal effect in CLI `--help` text.
**Warning signs:** Significant discrepancy between `--arc-method true` and `--arc-method mean` output for the same chart — expected and correct.

### Pitfall 3: Missing `abs_position` for House Cusps
**What goes wrong:** Code attempts `h['abs_position']` on house entries from `natal_data['houses']`, raises `KeyError`.
**Why it happens:** The `build_chart_json()` function stores houses as `{'number': N, 'sign': '...', 'degree': X.XX}` without an `abs_position` key. Only planets and angles store `abs_position` directly.
**How to avoid:** Reconstruct house cusp longitudes using `SIGN_OFFSETS[sign] + degree`. The `SIGN_OFFSETS` mapping (30° per sign) is simple: `{'Ari': 0, 'Tau': 30, ..., 'Pis': 330}`.
**Warning signs:** `KeyError: 'abs_position'` when accessing house data; or incorrect house positions that don't match the natal angles (ASC should equal House 1 cusp, which equals `SIGN_OFFSETS[House1.sign] + House1.degree`).

### Pitfall 4: `--target-date` Argument Conflict with `--progressions`
**What goes wrong:** Developer adds a NEW `--target-date` argument definition for `--solar-arcs`, causing argparse to raise a conflict error: `argument --target-date: conflicting option string(s)`.
**Why it happens:** argparse does not allow redefining an argument that already exists in the parser.
**How to avoid:** Do NOT add another `add_argument('--target-date', ...)` call. The Phase 9 definition is shared. In `calculate_solar_arcs(args)`, read `args.target_date` (same attribute name) just as `calculate_progressions()` does.
**Warning signs:** `argparse.ArgumentError: argument --target-date: conflicting option string(s)` at startup.

### Pitfall 5: SA Aspects Include Self-Aspects (Directed Point = Natal Point Same Name)
**What goes wrong:** The nested loop in `build_sarc_aspects()` compares SA directed Sun against natal Sun. Since the arc equals the Sun's motion, `SA Sun - Natal Sun = arc`. If arc happens to be exactly 120°, we'd find SA Sun trine natal Sun. This is technically valid but confusing in output.
**Why it happens:** The double loop does not exclude same-name pairs.
**How to avoid:** Decide on policy during planning: include or exclude `directed_point == natal_point`. For Phase 10, exclude self-aspects (a planet directing to its own natal position is redundant information, not an aspect in the traditional sense).
**Warning signs:** Output showing `SA Sun conjunction natal Sun` — the conjunction is always 0° because directed Sun moves at the same rate as the arc, but other aspects are meaningful.

## Code Examples

Verified patterns from direct testing against local swisseph + Kerykeion 5.7.2 installation (2026-02-17).

### Complete Solar Arc Computation
```python
# Source: verified against local swisseph installation (2026-02-17)
import swisseph as swe

NAIBOD_ARC = 0.98564733  # degrees per year

def compute_solar_arc(birth_jd, target_jd, natal_sun_lon, method='true'):
    """
    Returns solar arc in degrees for the given birth/target date and method.

    True arc: arc = (progressed_Sun_longitude - natal_Sun_longitude) % 360
    Mean arc: arc = (elapsed_years * NAIBOD_ARC) % 360

    Progressed JD uses the standard day-for-year formula (365.25 Julian year).
    """
    elapsed_years = (target_jd - birth_jd) / 365.25
    if method == 'mean':
        return (elapsed_years * NAIBOD_ARC) % 360
    # True arc
    progressed_jd = birth_jd + elapsed_years  # reuse compute_progressed_jd formula
    prog_sun_data, _ = swe.calc_ut(progressed_jd, swe.SUN)
    return (prog_sun_data[0] - natal_sun_lon) % 360


# Verified values (Einstein, 2026-02-17, age 146.93 years):
birth_jd = swe.julday(1879, 3, 14, 11.5)
target_jd = swe.julday(2026, 2, 17, 12.0)
natal_sun_lon = 353.499  # from chart.json
true_arc = compute_solar_arc(birth_jd, target_jd, natal_sun_lon, 'true')
# true_arc == 141.935 degrees
mean_arc = compute_solar_arc(birth_jd, target_jd, natal_sun_lon, 'mean')
# mean_arc == 144.821 degrees
```

### Convert abs_position to Sign/Degree (reuse existing function)
```python
# position_to_sign_degree() is already defined in astrology_calc.py at line 984
# Returns (sign_abbreviation, degree_within_sign)
# Example:
sign, degree = position_to_sign_degree(135.434)
# sign='Leo', degree=15.43
```

### Complete calculate_solar_arcs() Orchestration
```python
# Source: verified pattern (2026-02-17) — follows Phase 7-9 routing conventions
def calculate_solar_arcs(args):
    """
    Orchestrate solar arc directions calculation for an existing natal profile.
    """
    try:
        natal_subject, natal_data = load_natal_profile(args.solar_arcs)

        natal_meta = natal_data.get('meta', {})
        natal_name = natal_meta.get('name', args.solar_arcs)
        location = natal_meta.get('location', {})

        birth_date_str = natal_meta['birth_date']
        birth_time_str = natal_meta['birth_time']
        birth_dt = datetime.strptime(birth_date_str + ' ' + birth_time_str, "%Y-%m-%d %H:%M")
        birth_jd = swe.julday(birth_dt.year, birth_dt.month, birth_dt.day,
                              birth_dt.hour + birth_dt.minute / 60.0)

        # Determine target date (reuse Phase 9 pattern)
        if args.age is not None:
            target_jd = birth_jd + args.age * 365.25
        elif args.target_date is not None:
            target_jd = swe.julday(args.target_date.year, args.target_date.month,
                                   args.target_date.day, 12.0)
        else:
            today = datetime.now(timezone.utc)
            target_jd = swe.julday(today.year, today.month, today.day, 12.0)

        # Get arc method (default: 'true')
        arc_method = getattr(args, 'arc_method', 'true')

        # Get natal Sun from profile
        natal_sun_lon = next(
            p['abs_position'] for p in natal_data['planets'] if p['name'] == 'Sun'
        )

        # Compute arc
        arc = compute_solar_arc(birth_jd, target_jd, natal_sun_lon, method=arc_method)

        # Build and emit JSON
        sarc_dict = build_solar_arc_json(
            natal_data, args.solar_arcs, birth_jd, target_jd, arc, arc_method
        )
        print(json.dumps(sarc_dict, indent=2))
        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error calculating solar arc directions: {e}", file=sys.stderr)
        return 1
```

### Verified Performance (2026-02-17, local machine)
```
Profile load:              1ms  (reading chart.json from disk)
swe.calc_ut() (true arc):  0ms  (single ephemeris lookup)
Arithmetic + aspects:      0ms  (pure Python dict operations)
TOTAL:                    ~1ms  (trivially fast — no from_birth_data() calls)
```
Phase 10 is the fastest of all the predictive techniques (Phases 7-10) because it requires zero `from_birth_data()` invocations.

## State of the Art

| Old Approach | Current Approach | Impact for Phase 10 |
|---|---|---|
| Manual solar arc: add age in degrees to all natal positions | Compute arc from actual progressed Sun position via Swiss Ephemeris | Use `swe.calc_ut(progressed_jd, swe.SUN)` for true arc; do not use age as a direct substitute |
| Naibod mean arc only (fixed rate) | True arc (default) + mean arc option | Support both methods via `--arc-method` flag; true arc is more accurate for non-mean solar motion |
| SA aspects only for planets | SA aspects include ASC and MC | Include natal and directed ASC/MC in the aspect check — angles are primary SA targets |
| Separate directed chart tool | CLI mode integrated with natal profile | Reuse `load_natal_profile()` and `compute_progressed_jd()` from existing codebase |

**Deprecated/outdated:**
- Using whole-year approximation (arc ≈ age in whole degrees): too imprecise for aspects with 1-degree orb; use elapsed years with decimal precision via JD arithmetic.

## Open Questions

1. **Should `--solar-arcs` routing be BEFORE or AFTER `--progressions` in main()?**
   - What we know: The early-return pattern means order matters only if both flags are provided simultaneously (which is an error case). Conventionally, newer modes are added before older ones to prevent stale patterns from being reached by mistake.
   - What's unclear: Whether there's any reason to prefer a specific order between `--solar-arcs` and `--progressions`.
   - Recommendation: Add `--solar-arcs` routing immediately BEFORE the existing `--progressions` check. The planner should decide on final ordering.

2. **Should SA aspects include directed angles (ASC, MC) vs natal angles, or only planets?**
   - What we know: Professional astrology strongly emphasizes SA directed angles to natal planets and SA directed planets to natal angles (e.g., "SA Pluto conjunct natal ASC" is a major life event indicator). Angles are essential to include.
   - What's unclear: Whether to also include SA directed planets to natal House cusps (a less common practice).
   - Recommendation: Include ASC and MC in both the directed and natal aspect sets. Exclude house cusps from aspect calculation (cusp conjunctions are a more specialized technique).

3. **Should SA output include directed house cusp positions?**
   - What we know: House cusps can be solar arc directed just like planets (add arc to each cusp longitude). This shows which natal houses are "activated" by the directed cusps.
   - What's unclear: Whether this is useful for the interpretation guide in Phase 10 vs adding output complexity.
   - Recommendation: Omit directed house cusps for Phase 10 (SARC-01 through SARC-03 don't mention it). Include directed planets and directed angles (ASC + MC) only. The planner can add cusps as a SARC-04 enhancement.

4. **What orb should be the default for SARC-02: 0.5 or 1.0 degrees?**
   - What we know: SARC-02 says "0.5-1 degree orb." Professional standard (Noel Tyl, multiple sources) uses 1.0 degree. Some practitioners use 0.5 degree for stricter timing.
   - What's unclear: Whether the requirement means "use a range of 0.5-1.0" or "the orb should be somewhere between 0.5 and 1.0."
   - Recommendation: Default to 1.0 degree (professional standard). The 0.5-1.0 range in the requirement describes the professional practice range, not a dual-orb system. The planner may add a `--sarc-orb` flag if configurable orb is desired.

## Sources

### Primary (HIGH confidence)
- Local swisseph + Kerykeion 5.7.2 installation — direct Python REPL testing (2026-02-17)
  - `swe.calc_ut(progressed_jd, swe.SUN)` confirmed: returns progressed Sun longitude for true arc
  - True arc formula `(prog_sun_lon - natal_sun_lon) % 360` verified: Einstein gets 141.935°, 1990-06-15 birth at 34.5 years gets 32.958°
  - Mean arc formula `elapsed_years * 0.98564733` verified: Einstein gets 144.821°, 34.5-year case gets 34.053°
  - Aspect finding (manual loop) confirmed: 6 aspects for Einstein within 1-degree orb
  - Performance: < 1ms total (no `from_birth_data()` calls)
  - `natal_data['houses']` confirmed: no `abs_position` key; planets and angles DO have `abs_position`
  - House cusp reconstruction `SIGN_OFFSETS[sign] + degree` verified: House 1 cusp matches ASC abs_position exactly
  - `position_to_sign_degree()` exists at line 984 in current `astrology_calc.py` — reusable
- `C:/NEW/backend/astrology_calc.py` (lines 640-983) — Phase 9 `compute_progressed_jd()`, `load_natal_profile()`, routing pattern confirmed
- `~/.natal-charts/albert-einstein/chart.json` — data structure verified for planets, angles, houses

### Secondary (MEDIUM confidence)
- Web search results (multiple consistent sources, 2024-2026): Solar arc definition confirmed as "progressed Sun - natal Sun, applied to all chart points"
- Web search results: Naibod arc = 0.98564733 degrees/year (Sun's mean daily motion); true arc = actual solar arc on progressed date; both methods confirmed from multiple sources
- Web search results: 1-degree orb is professional standard for SA directions (Noel Tyl cited; confirmed by multiple sources); 0.5-degree used by some practitioners for tighter timing
- Astrodienst Astrowiki Solar Arc entry: true arc vs mean arc distinction confirmed (JavaScript-rendered page — could not fetch full content, but summary confirmed by Wayback/secondary sources)

### Tertiary (LOW confidence)
- "Summer births have SA arc less than age; winter births have SA arc more than age" — derived from Sun's perihelion/aphelion mechanics; empirically verified in code but not cited from a single authoritative astrological text

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — entire implementation verified end-to-end against local swisseph + chart.json; no new dependencies
- Architecture: HIGH — formulas verified; aspect calculation confirmed; output structure defined; performance benchmarked
- Pitfalls: HIGH — all pitfalls identified from direct code testing (KeyError on house abs_position, from_birth_data confusion, argparse conflict)

**Research date:** 2026-02-17
**Valid until:** 2026-03-17 (30 days — swisseph API is stable, SA formulas are timeless, Kerykeion pinned at 5.7.2)
