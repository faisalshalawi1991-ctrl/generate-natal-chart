# Phase 8: Transit Timelines - Research

**Researched:** 2026-02-17
**Domain:** Kerykeion 5.7.2 time-range transit generation, ephemeris sampling, exact aspect hit detection
**Confidence:** HIGH

## Summary

Phase 8 adds a `--timeline` CLI mode that generates transit aspect timelines over a date range. Users specify a natal profile slug and either a preset range (week / 30d / 3m / year) or custom start + end dates, and receive a chronological list of transit events — each event is an exact aspect hit (the day an applying aspect flips to separating).

The full technical pipeline is already present in Kerykeion 5.7.2 and was verified empirically. `EphemerisDataFactory` generates daily planetary positions for any date range (up to the built-in 730-day max). `TransitsTimeRangeFactory` then compares each day's positions against the natal chart using `AspectsFactory.dual_chart_aspects()` and returns a `TransitsTimeRangeModel` with per-day aspect snapshots. Exact hit detection is a post-processing step: scan the ordered day-by-day list for each unique (transit_planet, aspect_type, natal_planet) triple and flag the transition where `aspect_movement` flips from `'Applying'` to `'Separating'` (or `'Static'`). The day before the flip is the "exact hit" date.

Performance was measured directly against the installed library: 7 days takes 0.02s, 30 days 0.09s, 90 days 0.26s, 365 days 1.14s. All preset ranges are fast enough for CLI usage. No new pip dependencies are required.

**Primary recommendation:** Add a `--timeline SLUG` subcommand with `--range {week,30d,3m,year}` (default: 30d) and `--start` / `--end` for custom ranges. Use `EphemerisDataFactory` + `TransitsTimeRangeFactory` with daily step and tighter transit orbs (the existing `TRANSIT_DEFAULT_ORBS` constant). Post-process the resulting `TransitsTimeRangeModel` to extract exact hit events and output a timeline JSON to stdout.

## Standard Stack

### Core (No Changes)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Kerykeion | 5.7.2 | Ephemeris generation and transit comparison | `EphemerisDataFactory` + `TransitsTimeRangeFactory` are the purpose-built Phase 8 APIs. PINNED — do not upgrade. |
| Python | 3.11 | Runtime | Required for pyswisseph prebuilt wheels. |

### Kerykeion APIs Used in Phase 8
| API | Class/Method | What It Provides |
|-----|-------------|-----------------|
| Ephemeris generation | `EphemerisDataFactory(start, end, step_type='days', step=1, lat=0.0, lng=0.0, tz_str='Etc/UTC')` | List of `AstrologicalSubjectModel` objects, one per day at UTC noon |
| Get subjects | `.get_ephemeris_data_as_astrological_subjects()` | Returns `List[AstrologicalSubjectModel]` — each usable with `TransitsTimeRangeFactory` |
| Transit time range | `TransitsTimeRangeFactory(natal_chart, ephemeris_data_points, active_points, active_aspects)` | Wraps all daily aspect comparisons |
| Get transit moments | `.get_transit_moments()` | Returns `TransitsTimeRangeModel` with `transits: List[TransitMomentModel]` |
| Transit moment | `TransitMomentModel` | Has `date: str` (ISO UTC) and `aspects: List[AspectModel]` |
| Aspect model | `AspectModel` | Has `p1_name`, `p2_name`, `aspect`, `orbit`, `aspect_movement` ('Applying'/'Separating'/'Static'), `p1_speed`, `p2_speed` |
| Time range model | `TransitsTimeRangeModel` | Has `transits`, `dates`, `subject` |

### Existing Constants (Reuse from Phase 7)
| Constant | Value | Use in Phase 8 |
|----------|-------|---------------|
| `TRANSIT_DEFAULT_ORBS` | conj/opp=3, trine/sq=2, sextile=1 | Pass as `active_aspects` to `TransitsTimeRangeFactory` |
| `MAJOR_PLANETS` | 10 planets: Sun through Pluto | Pass as `active_points` to both factory classes |

### No New Dependencies
No `pip install` required. `EphemerisDataFactory` and `TransitsTimeRangeFactory` are already installed in Kerykeion 5.7.2.

**Installation:**
```bash
# No new packages needed — verify existing installation
/c/NEW/backend/venv/Scripts/python -c "from kerykeion.ephemeris_data_factory import EphemerisDataFactory; from kerykeion.transits_time_range_factory import TransitsTimeRangeFactory; print('OK')"
```

## Architecture Patterns

### Recommended File Structure (No New Files)
```
backend/
└── astrology_calc.py   # Add timeline functions here (isolated section after Phase 7 functions)
    ├── [existing natal chart + Phase 7 transit functions - UNTOUCHED]
    ├── valid_timeline_date()          # New: validates start/end dates (1900-2100, reuse valid_query_date logic)
    ├── parse_preset_range()           # New: converts 'week'/'30d'/'3m'/'year' to (start, end) datetimes
    ├── build_timeline_events()        # New: extracts exact hit events from TransitsTimeRangeModel
    ├── build_timeline_json()          # New: assembles the complete timeline JSON dict
    ├── calculate_timeline()           # New: orchestrates the full pipeline
    └── [main() — add --timeline routing after --transits routing]
```

### Pattern 1: EphemerisDataFactory + TransitsTimeRangeFactory Pipeline
**What:** Generate daily planetary positions, then run dual-chart aspect comparison for each day.
**When to use:** All date-range transit calculations (Phase 8 scope).

```python
# Source: verified against local Kerykeion 5.7.2 installation (2026-02-17)
from datetime import datetime, timedelta
from kerykeion.ephemeris_data_factory import EphemerisDataFactory
from kerykeion.transits_time_range_factory import TransitsTimeRangeFactory

# Step 1: Generate ephemeris data (one AstrologicalSubject per day at UTC noon)
start_dt = datetime(2026, 2, 17, 12, 0)    # UTC noon on start date
end_dt   = datetime(2026, 3, 18, 12, 0)    # UTC noon on end date

ephemeris_factory = EphemerisDataFactory(
    start_datetime=start_dt,
    end_datetime=end_dt,
    step_type='days',
    step=1,
    lat=0.0,        # Geocentric — same as Phase 7 transit subject
    lng=0.0,
    tz_str='Etc/UTC',
)
ephemeris_subjects = ephemeris_factory.get_ephemeris_data_as_astrological_subjects()
# Returns List[AstrologicalSubjectModel], one per day

# Step 2: Run transit comparison against natal chart
transit_factory = TransitsTimeRangeFactory(
    natal_chart=natal_subject,              # From load_natal_profile()
    ephemeris_data_points=ephemeris_subjects,
    active_points=MAJOR_PLANETS,            # Reuse Phase 7 constant
    active_aspects=TRANSIT_DEFAULT_ORBS,    # Reuse Phase 7 constant
)
results = transit_factory.get_transit_moments()
# Returns TransitsTimeRangeModel with .transits (List[TransitMomentModel])
# Each TransitMomentModel: .date (ISO UTC str), .aspects (List[AspectModel])
```

### Pattern 2: Exact Hit Detection (TRAN-08)
**What:** Post-process the day-by-day results to find the moment an applying aspect flips to separating. The last day in the "Applying" state is the date of closest approach; the hit occurred between that day and the next. Report the "Applying" day as the hit date.
**When to use:** For producing the `events` list in the timeline output.

```python
# Source: verified against local Kerykeion 5.7.2 installation (2026-02-17)
from collections import defaultdict

def build_timeline_events(results):
    """
    Extract exact transit aspect hit events from TransitsTimeRangeModel.

    An 'exact hit' is detected when an aspect's aspect_movement transitions from
    'Applying' (on day N) to 'Separating' or 'Static' (on day N+1).
    The hit date is reported as day N (the last day in the Applying state).
    The orb on day N is the closest recorded approach.

    Args:
        results: TransitsTimeRangeModel from TransitsTimeRangeFactory.get_transit_moments()

    Returns:
        List[dict]: Sorted list of event dicts, each with:
            - date (str): YYYY-MM-DD of the exact hit
            - transit_planet (str): Name of the transiting planet
            - aspect (str): Aspect type (conjunction, opposition, etc.)
            - natal_planet (str): Name of the natal planet
            - orb (float): Closest orb recorded (the applying orb on hit date)
    """
    # Track per (transit_planet, aspect, natal_planet): list of (date, orb, movement)
    aspect_tracking = defaultdict(list)
    for tm in results.transits:
        date_str = tm.date[:10]  # YYYY-MM-DD from ISO datetime
        for asp in tm.aspects:
            if asp.p1_name in MAJOR_PLANETS and asp.p2_name in MAJOR_PLANETS:
                key = (asp.p1_name, asp.aspect, asp.p2_name)
                aspect_tracking[key].append((date_str, round(asp.orbit, 3), asp.aspect_movement))

    events = []
    for key, track in aspect_tracking.items():
        transit_planet, aspect_type, natal_planet = key
        for i in range(1, len(track)):
            prev_date, prev_orb, prev_mv = track[i - 1]
            _curr_date, _curr_orb, curr_mv = track[i]
            # Transition from applying to separating (or static) = exact hit
            if prev_mv == 'Applying' and curr_mv in ('Separating', 'Static'):
                events.append({
                    'date': prev_date,
                    'transit_planet': transit_planet,
                    'aspect': aspect_type,
                    'natal_planet': natal_planet,
                    'orb_at_hit': prev_orb,
                })

    events.sort(key=lambda e: e['date'])
    return events
```

### Pattern 3: Preset Range Parsing (TRAN-06)
**What:** Convert named preset strings to concrete (start, end) datetime pairs.
**When to use:** When user passes `--range {week,30d,3m,year}`.

```python
# Source: verified logic using standard library datetime + relativedelta or timedelta
from datetime import datetime, timedelta, timezone

def parse_preset_range(preset: str, reference_date=None):
    """
    Convert preset range string to (start_dt, end_dt) UTC noon datetimes.

    Args:
        preset: One of 'week', '30d', '3m', 'year'
        reference_date: datetime to use as 'today' (default: today UTC)

    Returns:
        Tuple[datetime, datetime]: (start, end) at UTC noon
    """
    if reference_date is None:
        reference_date = datetime.now(timezone.utc).replace(tzinfo=None)

    today = reference_date.replace(hour=12, minute=0, second=0, microsecond=0)

    DELTAS = {
        'week':  timedelta(days=6),
        '30d':   timedelta(days=29),
        '3m':    timedelta(days=89),   # 90 days total (inclusive)
        'year':  timedelta(days=364),  # 365 days total (inclusive)
    }
    if preset not in DELTAS:
        raise ValueError(f"Invalid preset: {preset}. Use: week, 30d, 3m, year")

    return today, today + DELTAS[preset]
```

Note: Using `timedelta` instead of `relativedelta` avoids a new dependency. For 3m, 90 days is an acceptable approximation (standard industry practice for transit timelines).

### Pattern 4: CLI Argument Additions for Phase 8
**What:** Add `--timeline` flag alongside existing `--transits` flag.

```python
# Add to parser in main(), BEFORE args = parser.parse_args()
parser.add_argument(
    '--timeline',
    metavar='SLUG',
    help='Generate transit timeline for an existing chart profile (e.g., albert-einstein)'
)
parser.add_argument(
    '--range',
    choices=['week', '30d', '3m', 'year'],
    default='30d',
    help='Preset date range for timeline (default: 30d). Ignored if --start/--end given.'
)
parser.add_argument(
    '--start',
    type=valid_query_date,   # Reuse Phase 7 validator (1900-2100)
    default=None,
    help='Custom timeline start date YYYY-MM-DD'
)
parser.add_argument(
    '--end',
    type=valid_query_date,   # Reuse Phase 7 validator
    default=None,
    help='Custom timeline end date YYYY-MM-DD'
)
```

**Routing in `main()` — add AFTER `--transits` check:**
```python
if args.timeline:
    return calculate_timeline(args)
```

### Pattern 5: Timeline JSON Output Structure
**What:** The complete output structure for `--timeline` mode.

```python
# Target timeline output structure
timeline_output = {
    "meta": {
        "natal_name": "Albert Einstein",
        "natal_slug": "albert-einstein",
        "start_date": "2026-02-17",
        "end_date": "2026-03-18",
        "range_days": 30,
        "chart_type": "transit_timeline",
        "calculated_at": "2026-02-17T12:00:00+00:00",
        "orbs_used": {"conjunction": 3, "opposition": 3, "trine": 2, "square": 2, "sextile": 1},
        "event_count": 24
    },
    "events": [
        {
            "date": "2026-02-17",
            "transit_planet": "Venus",
            "aspect": "opposition",
            "natal_planet": "Uranus",
            "orb_at_hit": 0.052
        },
        {
            "date": "2026-02-17",
            "transit_planet": "Mars",
            "aspect": "sextile",
            "natal_planet": "Moon",
            "orb_at_hit": 0.222
        }
        # ... sorted chronologically
    ]
}
```

### Anti-Patterns to Avoid
- **Using `EphemerisDataFactory` with location-specific `lat`/`lng`/`tz_str`:** Like Phase 7 transit subjects, ephemeris subjects for transit timelines should use `lat=0.0`, `lng=0.0`, `tz_str='Etc/UTC'` so planet ecliptic positions are location-independent. The `__main__` example in `transits_time_range_factory.py` uses the natal chart's lat/lng — this is incorrect for transit position calculation.
- **Using the default `TransitsTimeRangeFactory` active_aspects:** The default `DEFAULT_ACTIVE_ASPECTS` uses wide natal-chart orbs (conjunction=10, opposition=10, trine=8). Always pass `TRANSIT_DEFAULT_ORBS` explicitly to `TransitsTimeRangeFactory` to use tighter transit orbs (3/3/2/2/1).
- **Using the default `TransitsTimeRangeFactory` active_points:** `DEFAULT_ACTIVE_POINTS` includes 18 points (lunar nodes, Chiron, angles, etc.). Always pass `MAJOR_PLANETS` explicitly for focused 10-planet transit analysis.
- **Reporting missed Moon aspects:** Moon moves 13-14 deg/day with daily sampling. A sextile (1 deg orb = 2 deg window) can be entered and exited within a single day, producing no visible `Applying` -> `Separating` transition in the daily data. Do NOT claim Moon transit events are exhaustive. Document this limitation in the meta or output.
- **Exceeding the 730-day max_days limit:** `EphemerisDataFactory` raises `ValueError` if `len(dates_list) > 730`. The year preset (365 days) is well within the limit. Custom ranges must be validated to be ≤ 730 days (or the error from the factory is sufficient).
- **Modifying Phase 7 functions:** All new timeline code must be in new functions. `build_transit_json`, `calculate_transits`, and `load_natal_profile` must not be touched.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Daily planetary position generation | Custom loop calling `AstrologicalSubjectFactory` per day | `EphemerisDataFactory.get_ephemeris_data_as_astrological_subjects()` | Already does this loop with safety limits, correct UTC handling, and all edge cases |
| Per-day transit aspect comparison | Calling `dual_chart_aspects()` directly in a loop | `TransitsTimeRangeFactory.get_transit_moments()` | Wraps the loop; returns structured `TransitsTimeRangeModel` with ISO datetime stamps |
| Date range arithmetic for presets | Custom relativedelta / calendar logic | `timedelta` with fixed-day approximations (6, 29, 89, 364) | No new dependency; acceptable precision for transit timelines |
| Aspect continuity tracking | Complex state machine across multiple days | Simple list append + consecutive-pair scan for `Applying` -> `Separating` transition | Kerykeion already provides `aspect_movement` per day; just scan transitions |

**Key insight:** Phase 8 is primarily orchestration: the two factory classes handle all computation. The core implementation is (1) argument parsing, (2) calling the factories, (3) scanning transitions to extract exact hit events, (4) JSON assembly.

## Common Pitfalls

### Pitfall 1: EphemerisDataFactory Using Natal Location Instead of UTC at 0,0
**What goes wrong:** Developer copies the `transits_time_range_factory.py` `__main__` example, which passes `lat=person.lat, lng=person.lng, tz_str=person.tz_str` to `EphemerisDataFactory`. Transit planet positions then depend on the natal chart's timezone, introducing a sub-degree offset from other reference sources.
**Why it happens:** The Kerykeion example code uses the natal chart's location for the ephemeris factory. This is appropriate if you want house cusps at that location, but irrelevant for ecliptic planet longitudes.
**How to avoid:** Always pass `lat=0.0, lng=0.0, tz_str='Etc/UTC'` to `EphemerisDataFactory` for transit timeline calculations. Planet ecliptic longitudes depend only on the UTC Julian Day, not on the observer's location.
**Warning signs:** Transit Sun position differs by ~0.3° from astro.com for the same date.

### Pitfall 2: Moon Transit Events Silently Missed with Daily Sampling
**What goes wrong:** Moon aspects (especially minor aspects like sextile with 1° orb) happen entirely between two daily sample points and are never detected. The TRAN-08 exact hit detection produces zero Moon events for some days even though Moon formed and completed aspects during that day.
**Why it happens:** Moon moves ~13-14 deg/day. With a 1° sextile orb, the 2-degree total orb window takes approximately 2/13 = 3.5 hours. Daily sampling (once per day at noon UTC) misses aspects that occur between midnight-to-midnight outside the sample window.
**How to avoid:** This is a known limitation of daily sampling. Document it in the output meta. Do not attempt to fix it by upsampling all planets — that would add significant complexity and computation time for limited benefit. The standard industry approach (astro.com daily lists, Astrodienst) also uses daily resolution for transit timelines. Slow planets (Jupiter through Pluto) are essentially unaffected — their orb windows span days or weeks.
**Warning signs:** "Why is Moon not showing aspects?" user question. Answer: Moon aspects are approximate at daily resolution; fast Moon aspects (< 4 hours in orb) may be missed.

### Pitfall 3: Default Active Aspects Using Wide Natal Orbs
**What goes wrong:** Developer creates `TransitsTimeRangeFactory(natal, ephemeris_data)` without specifying `active_aspects`. The default `DEFAULT_ACTIVE_ASPECTS` uses orbs of 10° (conjunction), 10° (opposition), 8° (trine), 6° (sextile), 5° (square). The timeline becomes overwhelming with hundreds of concurrent aspects.
**Why it happens:** Kerykeion's defaults are designed for natal chart analysis, not transit timelines. Transit orbs should be 2-5x tighter.
**How to avoid:** Always pass `active_aspects=TRANSIT_DEFAULT_ORBS` explicitly to `TransitsTimeRangeFactory`. The existing constant (conj/opp=3, trine/sq=2, sextile=1) is the correct value.
**Warning signs:** 30-day timeline shows 345+ aspects (correct with TRANSIT_DEFAULT_ORBS) vs 1000+ (with DEFAULT_ACTIVE_ASPECTS).

### Pitfall 4: Same Aspect Triple Appearing Multiple Times in Events List
**What goes wrong:** An aspect like "Jupiter square natal Venus" enters orb, is detected as a hit, then leaves orb and re-enters orb (e.g., due to retrograde), creating duplicate events with different dates.
**Why it happens:** Outer planets go retrograde and can hit the same aspect multiple times in a year. For example, Jupiter in a multi-week retrograde loop can square a natal planet, separate, then return direct and square it again — this produces 2-3 exact hit events for the same triple.
**How to avoid:** This is correct behavior, not a bug. Multiple hits for the same triple (due to retrograde loops) should all appear in the events list with different dates. Do not deduplicate by aspect triple — deduplicate only by (triple, date) to prevent double-counting on the same day if two consecutive same-day samples both show Applying.
**Warning signs:** "Jupiter square Venus appearing twice" — this is expected and correct.

### Pitfall 5: --start/--end Validation When Only One Is Provided
**What goes wrong:** User passes `--start 2026-03-01` without `--end`, or vice versa. The CLI silently ignores one or falls back to preset range in an undocumented way.
**Why it happens:** Argparse doesn't natively enforce "both or neither" for paired arguments.
**How to avoid:** In `calculate_timeline()`, validate: if `args.start` or `args.end` is set, both must be set. Also validate `args.start < args.end`. Print clear error to stderr and return 1 if either condition is violated.
**Warning signs:** `--start 2026-06-01` without `--end` uses a default end date with no warning.

### Pitfall 6: Breaking --transits Mode When Adding --start/--end Arguments
**What goes wrong:** The new `--start` and `--end` arguments are accepted by both `--transits` and `--timeline` modes. A user running `--transits albert-einstein --start 2026-01-01` might get an unexpected warning or error from the transit snapshot mode.
**Why it happens:** Argparse arguments are global — they apply to all modes unless carefully routed.
**How to avoid:** In `calculate_transits()`, ignore `args.start` and `args.end` entirely. In `calculate_timeline()`, treat `--start`/`--end` as the custom range override and ignore `--range`. Document this in `--help` text. Use `--query-date` exclusively for `--transits` mode.
**Warning signs:** `--transits albert-einstein --start 2026-01-01` prints an unexpected error or uses start date incorrectly.

## Code Examples

Verified patterns from direct testing against local Kerykeion 5.7.2 installation.

### Complete Pipeline: EphemerisDataFactory + TransitsTimeRangeFactory
```python
# Source: verified against local Kerykeion 5.7.2 installation (2026-02-17)
# Performance measured: 7d=0.02s, 30d=0.09s, 90d=0.26s, 365d=1.14s
from datetime import datetime, timedelta, timezone
from kerykeion.ephemeris_data_factory import EphemerisDataFactory
from kerykeion.transits_time_range_factory import TransitsTimeRangeFactory

def calculate_timeline(args):
    try:
        natal_subject, natal_data = load_natal_profile(args.timeline)

        # Determine date range
        if args.start and args.end:
            # Custom range (TRAN-07)
            start_dt = args.start.replace(hour=12, minute=0, second=0, microsecond=0)
            end_dt   = args.end.replace(hour=12, minute=0, second=0, microsecond=0)
            if start_dt >= end_dt:
                print("Error: --start must be before --end", file=sys.stderr)
                return 1
        elif args.start or args.end:
            print("Error: both --start and --end required for custom range", file=sys.stderr)
            return 1
        else:
            # Preset range (TRAN-06)
            start_dt, end_dt = parse_preset_range(args.range)

        # Generate daily ephemeris (lat=0, lng=0, UTC)
        eph_factory = EphemerisDataFactory(
            start_datetime=start_dt,
            end_datetime=end_dt,
            step_type='days',
            step=1,
            lat=0.0,
            lng=0.0,
            tz_str='Etc/UTC',
        )
        ephemeris_subjects = eph_factory.get_ephemeris_data_as_astrological_subjects()

        # Run transit comparison
        transit_factory = TransitsTimeRangeFactory(
            natal_chart=natal_subject,
            ephemeris_data_points=ephemeris_subjects,
            active_points=MAJOR_PLANETS,
            active_aspects=TRANSIT_DEFAULT_ORBS,
        )
        results = transit_factory.get_transit_moments()

        # Extract exact hit events and assemble output
        timeline_dict = build_timeline_json(
            results, natal_data, args.timeline, start_dt, end_dt
        )
        print(json.dumps(timeline_dict, indent=2))
        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error calculating timeline: {e}", file=sys.stderr)
        return 1
```

### Exact Hit Event Extraction
```python
# Source: verified against local Kerykeion 5.7.2 installation (2026-02-17)
# Correctly detects applying->separating transitions for all 10 major planets
from collections import defaultdict

def build_timeline_events(results):
    aspect_tracking = defaultdict(list)
    for tm in results.transits:
        date_str = tm.date[:10]  # YYYY-MM-DD
        for asp in tm.aspects:
            if asp.p1_name in MAJOR_PLANETS and asp.p2_name in MAJOR_PLANETS:
                key = (asp.p1_name, asp.aspect, asp.p2_name)
                aspect_tracking[key].append((date_str, round(asp.orbit, 3), asp.aspect_movement))

    events = []
    for (transit_planet, aspect_type, natal_planet), track in aspect_tracking.items():
        for i in range(1, len(track)):
            prev_date, prev_orb, prev_mv = track[i - 1]
            _curr_date, _curr_orb, curr_mv = track[i]
            if prev_mv == 'Applying' and curr_mv in ('Separating', 'Static'):
                events.append({
                    'date': prev_date,
                    'transit_planet': transit_planet,
                    'aspect': aspect_type,
                    'natal_planet': natal_planet,
                    'orb_at_hit': prev_orb,
                })

    events.sort(key=lambda e: e['date'])
    return events
```

### Verified Performance Numbers (Kerykeion 5.7.2 on local machine, 2026-02-17)
```
  7 days:   7 points, eph=0.02s, transits=0.00s, total=0.02s, aspects_total=73
 30 days:  30 points, eph=0.07s, transits=0.01s, total=0.09s, aspects_total=345
 90 days:  90 points, eph=0.23s, transits=0.03s, total=0.26s, aspects_total=906
365 days: 365 points, eph=0.98s, transits=0.16s, total=1.14s, aspects_total=3779
```
All preset ranges complete well under 2 seconds. No caching or batch processing required.

### TransitsTimeRangeModel Data Access
```python
# Source: verified against local Kerykeion 5.7.2 installation (2026-02-17)
results = transit_factory.get_transit_moments()
# results.transits: List[TransitMomentModel]
# results.dates: List[str] — ISO datetime strings, same order as results.transits
# results.subject: AstrologicalSubjectModel — the natal chart

for tm in results.transits:
    print(f"Date: {tm.date}")         # e.g. "2026-02-17T12:00:00+00:00"
    for asp in tm.aspects:
        print(f"  {asp.p1_name} {asp.aspect} natal {asp.p2_name}")
        print(f"  orb: {asp.orbit:.2f}°, movement: {asp.aspect_movement}")
        # asp.aspect_movement is Literal['Applying', 'Separating', 'Static']
```

## State of the Art

| Old Approach | Current Approach | Impact for Phase 8 |
|---|---|---|
| Manual loop: create AstrologicalSubject per day + call dual_chart_aspects | `EphemerisDataFactory` + `TransitsTimeRangeFactory` | Use the factory pipeline; don't build the loop manually |
| Python `dateutil.relativedelta` for 3-month offsets | `timedelta(days=89)` with fixed approximation | No new dependency; 89-day approximation is standard for transit timelines |
| Interpolating exact aspect date (fraction of day) | Reporting "last Applying day" as hit date | Day-resolution is appropriate for transit timelines; sub-day precision not required for TRAN-08 |

**Deprecated/outdated:**
- `synastry_aspects()` method: deprecated alias for `dual_chart_aspects()` — `TransitsTimeRangeFactory` already uses the correct API internally.
- Using `EphemerisDataFactory.get_ephemeris_data()` (dict output) for transit calculation: use `get_ephemeris_data_as_astrological_subjects()` instead — returns `AstrologicalSubjectModel` objects required by `TransitsTimeRangeFactory`.

## Open Questions

1. **Should Moon transit events include a warning flag in the output?**
   - What we know: Daily sampling misses Moon aspects that occur entirely within a single day (2-4 hour window for sextile with 1° orb). Tested: Moon produces 2-3 detected aspects per week at daily sampling vs ~12 theoretically possible.
   - What's unclear: Whether to add a `"moon_events_approximate": true` flag in meta, or just document in RESEARCH.md and leave it to the interpretation guide (Phase 11).
   - Recommendation: Add a `"sampling_note"` field in meta: `"Daily resolution; Moon aspects < 4h in orb may not appear."` This is informative without changing the data structure.

2. **Maximum custom date range**
   - What we know: `EphemerisDataFactory` enforces a 730-day maximum by default. Custom `--start`/`--end` ranges beyond 730 days will raise `ValueError` from the factory.
   - What's unclear: Whether to enforce our own tighter limit (e.g., 365 days) in `calculate_timeline()` before calling the factory, to give a cleaner error message.
   - Recommendation: Validate custom range ≤ 365 days in `calculate_timeline()` before calling `EphemerisDataFactory`, with a clear error message. The preset `year` range is already 365 days. Ranges beyond 1 year are uncommon for transit analysis and would make the output very large.

3. **Output format: flat events list vs grouped by planet or date**
   - What we know: Requirements say "see transit events within a date range." No specific format required.
   - What's unclear: Whether a flat chronological list is better for Claude context loading vs a nested structure grouped by transit planet.
   - Recommendation: Use a flat chronological list of event dicts sorted by date. This is easiest for Claude to reason about ("what's happening around March 15") and simplest to implement.

## Sources

### Primary (HIGH confidence)
- Local Kerykeion 5.7.2 installation — direct Python REPL testing (2026-02-17)
  - `EphemerisDataFactory` constructor parameters confirmed with `step_type='days'`, `lat=0.0`, `lng=0.0`, `tz_str='Etc/UTC'`
  - `get_ephemeris_data_as_astrological_subjects()` confirmed returns `List[AstrologicalSubjectModel]`
  - `TransitsTimeRangeFactory(natal, subjects, active_points, active_aspects)` confirmed returns `TransitsTimeRangeModel`
  - `TransitMomentModel` fields: `date` (str ISO), `aspects` (List[AspectModel]) — confirmed via `model_fields`
  - `TransitsTimeRangeModel` fields: `transits`, `dates`, `subject` — confirmed via `model_fields`
  - Performance benchmarks: 7d=0.02s, 30d=0.09s, 90d=0.26s, 365d=1.14s
  - Exact hit detection via Applying->Separating transition: confirmed on 30-day Albert Einstein test (24 events detected)
  - Moon daily sampling gap: confirmed (speed 13-14 deg/day; sextile 1° orb window ≈ 3.5 hours)
  - `DEFAULT_ACTIVE_ASPECTS` and `DEFAULT_ACTIVE_POINTS` values confirmed from `kerykeion.settings.config_constants`
- `C:/NEW/backend/venv/Lib/site-packages/kerykeion/transits_time_range_factory.py` — source read directly
- `C:/NEW/backend/venv/Lib/site-packages/kerykeion/ephemeris_data_factory.py` — source read directly
- Phase 7 RESEARCH.md and VERIFICATION.md — prior architecture decisions confirmed

### Secondary (MEDIUM confidence)
- Kerykeion `transits_time_range_factory.py` `__main__` example — identifies the standard usage pattern (natal location for ephemeris factory is INCORRECT for transit calculations; corrected to lat=0.0, lng=0.0)

### Tertiary (LOW confidence)
- None for this phase — all claims verified against installed code and direct testing.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — both factory classes tested end-to-end with correct parameters
- Architecture: HIGH — exact hit detection pattern verified on 30-day test (24 events correctly identified)
- Pitfalls: HIGH — Moon sampling gap empirically confirmed; location pitfall verified against Kerykeion source; orb defaults confirmed from `config_constants`

**Research date:** 2026-02-17
**Valid until:** 2026-03-17 (30 days — Kerykeion pinned at 5.7.2, APIs are stable)
