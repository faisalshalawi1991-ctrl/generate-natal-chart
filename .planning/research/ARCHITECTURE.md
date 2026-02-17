# Architecture Research: Transit & Progression Integration

**Domain:** Astrological predictive techniques (transits, secondary progressions, solar arc directions)
**Researched:** 2026-02-17
**Confidence:** HIGH

## Integration with Existing Architecture

### Current System (v1.0)

```
┌─────────────────────────────────────────────────────────────────┐
│                    Skill Layer (SKILL.md)                        │
│  Routes: create natal | list profiles | load profile             │
└───────────────┬─────────────────────────────────────────────────┘
                │ bash invoke
┌───────────────▼─────────────────────────────────────────────────┐
│              Python Backend (astrology_calc.py)                  │
│  main() → build_chart_json() → Kerykeion Subject                 │
│  Functions: get_planet_dignities(), position_to_sign_degree()    │
└───────────────┬─────────────────────────────────────────────────┘
                │ write files
┌───────────────▼─────────────────────────────────────────────────┐
│              Storage (~/.natal-charts/{slug}/)                   │
│  chart.json (natal data) + chart.svg (natal wheel)               │
└─────────────────────────────────────────────────────────────────┘
```

### Target System (v1.1) — Transit/Progression Layer Added

```
┌─────────────────────────────────────────────────────────────────┐
│                    Skill Layer (SKILL.md)                        │
│  Routes: create natal | load with transits | query transits      │
│         | timeline | progressions | solar arc                    │
└───────────────┬─────────────────────────────────────────────────┘
                │ bash invoke
┌───────────────▼─────────────────────────────────────────────────┐
│              Python Backend (astrology_calc.py)                  │
│  ┌──────────────────┐  ┌──────────────────────────────────────┐ │
│  │  Natal Functions │  │ New: Transit/Progression Functions   │ │
│  │  build_chart_json│  │ build_transit_json()                 │ │
│  │  main() create   │  │ build_progression_json()             │ │
│  │                  │  │ build_solar_arc_json()               │ │
│  │                  │  │ calculate_aspects_between_charts()   │ │
│  │                  │  │ find_transit_events()                │ │
│  └──────────────────┘  └──────────────────────────────────────┘ │
└───────────────┬─────────────────────────────────────────────────┘
                │ write files
┌───────────────▼─────────────────────────────────────────────────┐
│              Storage (~/.natal-charts/{slug}/)                   │
│  Natal:          chart.json + chart.svg (persistent)             │
│  Transits:       transits-YYYY-MM-DD.json (snapshots, optional)  │
│  Progressions:   progressions-YYYY.json (snapshots, optional)    │
│  Solar Arc:      solar-arc-YYYY.json (snapshots, optional)       │
└─────────────────────────────────────────────────────────────────┘
```

## New CLI Modes & Arguments

### Mode 1: Auto-Include Current Transits (Chart Load Enhancement)

**Trigger:** Loading existing profile with `--now` flag
**Purpose:** Automatically calculate and inject current transits when loading a natal chart

```bash
# User intent: "Load John's chart with current transits"
python astrology_calc.py --load john-doe --now
```

**Data Flow:**
1. Load natal chart JSON from `~/.natal-charts/john-doe/chart.json`
2. Calculate transiting positions for current datetime
3. Calculate aspects between natal positions and transits
4. Return combined JSON: `{natal: {...}, transits: {...}, transit_aspects: [...]}`
5. Skill injects both natal guide + transit guide into context

**No save** — fresh calculation each time (transits change constantly)

### Mode 2: Targeted Transit Query

**Trigger:** Explicit transit calculation for specific date/range
**Purpose:** Answer "What transits affect person X on date Y?"

```bash
# Single date transit snapshot
python astrology_calc.py --transits john-doe --date 2026-03-15

# Transit timeline (find major events in range)
python astrology_calc.py --transits john-doe --from 2026-03-01 --to 2026-06-01 --events
```

**Data Flow:**
1. Load natal chart JSON
2. For single date: Calculate transiting positions, aspects to natal
3. For timeline: Iterate date range, find exact aspect hits (orb threshold)
4. Return JSON with transit positions + aspects OR timeline of events
5. Optional `--save` flag writes snapshot to `transits-YYYY-MM-DD.json`

**Timeline mode** returns list of events:
```json
{
  "timeline": [
    {
      "date": "2026-03-15",
      "event": "Transiting Jupiter conjunct Natal Sun",
      "orb": 0.2,
      "exact_time": "14:32 UTC"
    }
  ]
}
```

### Mode 3: Secondary Progressions

**Trigger:** `--progressions` flag with target year/age
**Purpose:** Calculate progressed chart for specific year

```bash
# Progressions for current age
python astrology_calc.py --progressions john-doe --now

# Progressions for specific age/year
python astrology_calc.py --progressions john-doe --age 35
python astrology_calc.py --progressions john-doe --year 2026
```

**Calculation Method (Day-for-a-Year):**
1. Load natal birth datetime: `birth_date`
2. Calculate target age: `age = target_year - birth_year`
3. Calculate progressed date: `progressed_date = birth_date + age days`
4. Create Kerykeion Subject for `progressed_date` at birth location
5. Extract positions (progressed planets, progressed houses, progressed angles)
6. Calculate aspects: progressed-to-natal

**Data Flow:**
- Fresh calculation each time (can be slow, ~1-2 seconds)
- Optional `--save` writes to `progressions-YYYY.json`
- Return JSON: `{progressed: {...}, progressed_natal_aspects: [...]}`

### Mode 4: Solar Arc Directions

**Trigger:** `--solar-arc` flag with target year/age
**Purpose:** Calculate solar arc directed chart

```bash
# Solar arc for current age
python astrology_calc.py --solar-arc john-doe --now

# Solar arc for specific year
python astrology_calc.py --solar-arc john-doe --year 2026
```

**Calculation Method (1 degree per year):**
1. Load natal positions
2. Calculate age: `age = target_year - birth_year`
3. Calculate arc offset: `arc = progressed_sun_position - natal_sun_position`
4. Apply arc to ALL natal positions: `directed_position = natal_position + arc`
5. Calculate directed houses using directed Ascendant
6. Calculate aspects: directed-to-natal

**Data Flow:**
- Faster than progressions (no ephemeris lookup, just arithmetic)
- Optional `--save` writes to `solar-arc-YYYY.json`
- Return JSON: `{solar_arc: {...}, solar_arc_natal_aspects: [...]}`

## Data Model Design

### Natal Data (Existing — No Changes)

```json
{
  "meta": {
    "name": "John Doe",
    "birth_date": "1990-06-15",
    "birth_time": "14:30",
    "location": {...},
    "chart_type": "Natal"
  },
  "planets": [...],
  "houses": [...],
  "angles": [...],
  "aspects": [...],
  "asteroids": [...],
  "fixed_stars": [...],
  "arabic_parts": {...},
  "dignities": [...],
  "distributions": {...}
}
```

### Transit Data (New Structure)

```json
{
  "meta": {
    "chart_type": "Transit",
    "natal_subject": "john-doe",
    "transit_datetime": "2026-02-17T15:30:00Z",
    "generated_at": "2026-02-17T15:30:05Z"
  },
  "transiting_planets": [
    {
      "name": "Jupiter",
      "sign": "Gem",
      "degree": 15.23,
      "abs_position": 75.23,
      "house": "3",
      "retrograde": false
    }
  ],
  "transit_aspects": [
    {
      "transiting_planet": "Jupiter",
      "natal_planet": "Sun",
      "type": "trine",
      "orb": 0.5,
      "applying": true
    }
  ]
}
```

### Progression Data (New Structure)

```json
{
  "meta": {
    "chart_type": "Secondary Progression",
    "natal_subject": "john-doe",
    "progressed_for_date": "2026-02-17",
    "progressed_age": 35,
    "calculation_date": "1990-07-20",
    "generated_at": "2026-02-17T15:30:05Z"
  },
  "progressed_planets": [...],
  "progressed_houses": [...],
  "progressed_angles": [...],
  "progressed_natal_aspects": [
    {
      "progressed_planet": "Moon",
      "natal_planet": "Venus",
      "type": "conjunction",
      "orb": 0.3
    }
  ]
}
```

### Solar Arc Data (New Structure)

```json
{
  "meta": {
    "chart_type": "Solar Arc Direction",
    "natal_subject": "john-doe",
    "directed_for_year": 2026,
    "age": 35,
    "arc_degrees": 35.12,
    "generated_at": "2026-02-17T15:30:05Z"
  },
  "directed_planets": [...],
  "directed_houses": [...],
  "directed_angles": [...],
  "solar_arc_natal_aspects": [...]
}
```

### Timeline Data (New Structure for Event Finding)

```json
{
  "meta": {
    "chart_type": "Transit Timeline",
    "natal_subject": "john-doe",
    "from_date": "2026-03-01",
    "to_date": "2026-06-01",
    "event_types": ["conjunction", "opposition", "trine", "square"],
    "orb_threshold": 1.0,
    "generated_at": "2026-02-17T15:30:05Z"
  },
  "events": [
    {
      "date": "2026-03-15",
      "exact_time": "14:32",
      "transiting_planet": "Jupiter",
      "natal_point": "Sun",
      "aspect": "trine",
      "orb_at_exact": 0.0,
      "duration_days": 3
    }
  ]
}
```

## Function Design

### New Functions to Add to `astrology_calc.py`

#### 1. `build_transit_json(natal_subject_data, transit_datetime)`

**Purpose:** Calculate transiting positions and aspects to natal chart

**Inputs:**
- `natal_subject_data`: Loaded natal chart JSON (dict)
- `transit_datetime`: datetime object for transit calculation

**Process:**
1. Create Kerykeion Subject for `transit_datetime` at birth location
2. Extract transiting planet positions
3. Call `calculate_aspects_between_charts()` with natal + transit positions
4. Calculate house positions for transiting planets (using natal houses)
5. Assemble transit JSON structure

**Returns:** Dict with transiting planets + transit aspects

#### 2. `build_progression_json(natal_subject_data, target_date_or_age)`

**Purpose:** Calculate secondary progressed chart

**Inputs:**
- `natal_subject_data`: Loaded natal chart JSON (dict)
- `target_date_or_age`: Either date or age integer

**Process:**
1. Parse natal birth date
2. Calculate progressed date using day-for-a-year formula
3. Create Kerykeion Subject for progressed date at birth location
4. Extract progressed positions
5. Call `calculate_aspects_between_charts()` for progressed-to-natal
6. Assemble progression JSON structure

**Returns:** Dict with progressed positions + progressed-natal aspects

#### 3. `build_solar_arc_json(natal_subject_data, target_year)`

**Purpose:** Calculate solar arc directed chart

**Inputs:**
- `natal_subject_data`: Loaded natal chart JSON (dict)
- `target_year`: Target year for direction

**Process:**
1. Calculate age from natal birth year
2. Calculate progressed Sun position (day-for-a-year)
3. Calculate arc: `arc = progressed_sun_abs_pos - natal_sun_abs_pos`
4. Apply arc to all natal positions
5. Convert directed Ascendant to houses (may need Kerykeion house calculation)
6. Call `calculate_aspects_between_charts()` for directed-to-natal
7. Assemble solar arc JSON structure

**Returns:** Dict with directed positions + directed-natal aspects

#### 4. `calculate_aspects_between_charts(chart1_positions, chart2_positions, aspect_types, orb)`

**Purpose:** Generic aspect calculation between two sets of positions

**Inputs:**
- `chart1_positions`: List of `{name, abs_position}` dicts
- `chart2_positions`: List of `{name, abs_position}` dicts
- `aspect_types`: List of aspect names (default: major 5)
- `orb`: Orb tolerance in degrees (default: 8° for transits, 1° for progressions)

**Process:**
1. Define aspect angles: conjunction=0°, opposition=180°, trine=120°, square=90°, sextile=60°
2. For each planet in chart1:
   - For each planet in chart2:
     - Calculate angular separation
     - Check if within orb of any aspect type
     - Determine if applying or separating (requires speed data)
3. Return list of aspect dicts

**Returns:** List of `{planet1, planet2, aspect, orb, applying}` dicts

**Note:** Can reuse Kerykeion's `NatalAspects` logic but needs adaptation for cross-chart aspects. May use Kerykeion 5.x `AspectsFactory` if available.

#### 5. `find_transit_events(natal_subject_data, from_date, to_date, event_types, orb_threshold)`

**Purpose:** Timeline scan for exact transit aspect hits

**Inputs:**
- `natal_subject_data`: Loaded natal chart JSON
- `from_date`, `to_date`: datetime range
- `event_types`: List of aspect types to find
- `orb_threshold`: Maximum orb to consider (default 1°)

**Process:**
1. Iterate daily from `from_date` to `to_date`
2. For each day, calculate transiting positions
3. Check aspects between transits and natal
4. When aspect orb < threshold, record event with exact date/time
5. Use binary search or ephemeris interpolation for exact timing

**Returns:** List of event dicts with date, aspect, orb, duration

**Performance:** ~90 days = ~90 ephemeris calls. Acceptable for CLI (few seconds).

### Modified Functions

#### `main()` — Argument Routing

**Add new argument groups:**

```python
# Transit mode
parser.add_argument('--transits', type=str, help='Profile slug for transit calculation')
parser.add_argument('--now', action='store_true', help='Use current datetime')
parser.add_argument('--from', type=valid_date, help='Timeline start date')
parser.add_argument('--to', type=valid_date, help='Timeline end date')
parser.add_argument('--events', action='store_true', help='Timeline mode')

# Progression mode
parser.add_argument('--progressions', type=str, help='Profile slug for progressions')
parser.add_argument('--age', type=int, help='Age for progression')
parser.add_argument('--year', type=int, help='Year for progression/solar arc')

# Solar arc mode
parser.add_argument('--solar-arc', type=str, help='Profile slug for solar arc')

# Optional save
parser.add_argument('--save', action='store_true', help='Save snapshot to profile directory')

# Load mode enhancement
parser.add_argument('--load', type=str, help='Profile slug to load')
```

**Routing logic:**

```python
if args.load and args.now:
    # Load natal + calculate current transits, return combined
    natal_data = load_natal_profile(args.load)
    transit_data = build_transit_json(natal_data, datetime.now())
    print(json.dumps({"natal": natal_data, "transits": transit_data}))

elif args.transits:
    if args.events:
        # Timeline mode
        events = find_transit_events(...)
        print(json.dumps(events))
    else:
        # Single date mode
        transit_data = build_transit_json(...)
        print(json.dumps(transit_data))

elif args.progressions:
    prog_data = build_progression_json(...)
    print(json.dumps(prog_data))

elif args.solar_arc:
    arc_data = build_solar_arc_json(...)
    print(json.dumps(arc_data))

# ... existing natal creation logic
```

#### `build_chart_json()` — No Changes

Natal chart building unchanged. New functions handle transit/progression separately.

## Kerykeion Integration Strategy

### Transit Calculations

**Use Kerykeion's existing capabilities:**

Based on research, Kerykeion 5.x supports transit charts via:
- `AstrologicalSubjectFactory.from_birth_data()` for transit datetime
- `ChartDataFactory.create_transit_chart_data(natal_subject, transit_subject)` (v5.x API)
- Returns pre-computed aspects between charts

**Fallback for v5.7.2 (current version):**
- Create two `AstrologicalSubject` instances (natal + transit)
- Use `NatalAspects` class or manually calculate aspects using positions
- Extract transiting positions from second subject

**Code approach:**

```python
# Create transit subject at target datetime
transit_subject = AstrologicalSubjectFactory.from_birth_data(
    name="Transit",
    year=transit_dt.year,
    month=transit_dt.month,
    day=transit_dt.day,
    hour=transit_dt.hour,
    minute=transit_dt.minute,
    lat=natal_subject.lat,
    lng=natal_subject.lng,
    tz_str=natal_subject.tz_str,
    online=False,
    houses_system_identifier='P'
)

# Extract positions and calculate aspects
```

### Progression Calculations

**Kerykeion may not have built-in progression support** (not found in documentation).

**Manual implementation required:**

```python
def build_progression_json(natal_data, target_year):
    birth_date = datetime.strptime(natal_data['meta']['birth_date'], '%Y-%m-%d')
    birth_time = datetime.strptime(natal_data['meta']['birth_time'], '%H:%M')

    age = target_year - birth_date.year
    progressed_date = birth_date + timedelta(days=age)

    # Create subject for progressed date
    progressed_subject = AstrologicalSubjectFactory.from_birth_data(
        name="Progressed",
        year=progressed_date.year,
        month=progressed_date.month,
        day=progressed_date.day,
        hour=birth_time.hour,
        minute=birth_time.minute,
        lat=natal_data['meta']['location']['latitude'],
        lng=natal_data['meta']['location']['longitude'],
        tz_str=natal_data['meta']['location']['timezone'],
        online=False,
        houses_system_identifier='P'
    )

    # Extract positions from progressed_subject
    # Calculate aspects between progressed and natal positions
```

### Solar Arc Calculations

**Manual implementation (arithmetic only, no ephemeris lookup):**

```python
def build_solar_arc_json(natal_data, target_year):
    birth_date = datetime.strptime(natal_data['meta']['birth_date'], '%Y-%m-%d')
    birth_time = datetime.strptime(natal_data['meta']['birth_time'], '%H:%M')

    age = target_year - birth_date.year

    # Calculate progressed Sun position to get arc
    progressed_date = birth_date + timedelta(days=age)
    progressed_sun_subject = AstrologicalSubjectFactory.from_birth_data(...)

    natal_sun_pos = natal_data['planets'][0]['abs_position']  # Sun is first
    progressed_sun_pos = progressed_sun_subject.sun.abs_pos
    arc = progressed_sun_pos - natal_sun_pos

    # Apply arc to all natal positions
    directed_planets = []
    for planet in natal_data['planets']:
        directed_pos = (planet['abs_position'] + arc) % 360
        directed_sign, directed_degree = position_to_sign_degree(directed_pos)
        directed_planets.append({
            "name": planet['name'],
            "sign": directed_sign,
            "degree": directed_degree,
            "abs_position": directed_pos
        })

    # Similar for angles and houses (houses need recalculation with directed ASC)
```

## Skill Layer Changes

### Routing Enhancements

**Current skill behavior:**
- No args → list profiles
- Birth data args → create natal chart

**New behavior:**
- `--load {slug}` → load natal chart only
- `--load {slug} --now` → load natal + current transits
- `--transits {slug} --date YYYY-MM-DD` → transit snapshot
- `--transits {slug} --from ... --to ... --events` → transit timeline
- `--progressions {slug} --year YYYY` → secondary progressions
- `--solar-arc {slug} --year YYYY` → solar arc directions

### Context Injection Strategy

**Two interpretation guides:**

1. **Natal guide** (existing) — How to interpret natal positions
2. **Transit guide** (new) — How to interpret transits, progressions, solar arc

**Injection logic:**

```
If transit data present:
  Inject natal guide + transit guide + combined JSON

If only natal:
  Inject natal guide + natal JSON
```

**Transit guide content:**
- Transit meanings (outer planets = long-term, inner = triggers)
- Aspect orbs for transits (wider than natal)
- Applying vs separating aspects
- Progression interpretation (inner development vs external events)
- Solar arc timing (1° = 1 year, exact hits are significant)

## Storage Strategy

### Principle: Natal Persistent, Predictive Ephemeral

**Rationale:**
- Natal chart never changes → store permanently
- Transits change constantly → calculate fresh, optionally snapshot
- Progressions change slowly → calculate on demand, optionally snapshot
- Solar arc changes slowly → calculate on demand, optionally snapshot

### Storage Layout

```
~/.natal-charts/john-doe/
├── chart.json              # Natal data (permanent)
├── chart.svg               # Natal wheel (permanent)
├── transits-2026-02-17.json   # Optional snapshot (user-saved)
├── progressions-2026.json     # Optional snapshot (user-saved)
└── solar-arc-2026.json        # Optional snapshot (user-saved)
```

**File naming convention:**
- Transits: `transits-YYYY-MM-DD.json` (date-specific)
- Progressions: `progressions-YYYY.json` (year-specific, slow-moving)
- Solar arc: `solar-arc-YYYY.json` (year-specific)

**Save behavior:**
- Default: NO save (fresh calculation, print to stdout)
- With `--save` flag: Write snapshot to profile directory
- Skill can later implement "load saved transit snapshot" if useful

## Build Order & Dependencies

### Phase Dependency Graph

```
1. Core Transit Calculation
   ├─► build_transit_json()
   ├─► calculate_aspects_between_charts()
   └─► Depends on: natal chart loading (existing)

2. CLI Arguments & Routing
   ├─► Add --transits, --now, --date arguments to main()
   ├─► Route to build_transit_json()
   └─► Depends on: Phase 1

3. Progression Calculation
   ├─► build_progression_json()
   ├─► Day-for-a-year date arithmetic
   └─► Depends on: Phase 1 (reuses calculate_aspects_between_charts)

4. Solar Arc Calculation
   ├─► build_solar_arc_json()
   ├─► Arc arithmetic + position offset
   └─► Depends on: Phase 1

5. Timeline / Event Finding
   ├─► find_transit_events()
   ├─► Date iteration + aspect detection
   └─► Depends on: Phase 1

6. Optional Save to Storage
   ├─► Write snapshot JSON files
   └─► Depends on: Phases 1-5

7. Skill Layer Integration
   ├─► Update SKILL.md routing
   ├─► Add transit guide prompt
   └─► Depends on: Phases 1-6 complete

8. Context Injection
   ├─► Combined JSON output
   ├─► Dual guide injection (natal + transit)
   └─► Depends on: Phase 7
```

### Recommended Build Order

**Priority 1 (Core Functionality):**
1. `build_transit_json()` — Single date transit snapshot
2. `calculate_aspects_between_charts()` — Generic aspect calculation
3. CLI routing for `--transits {slug} --date YYYY-MM-DD`
4. Manual testing: "python astrology_calc.py --transits john-doe --date 2026-02-17"

**Priority 2 (Progressions):**
5. `build_progression_json()` — Secondary progression calculation
6. CLI routing for `--progressions {slug} --year YYYY`
7. Manual testing

**Priority 3 (Solar Arc):**
8. `build_solar_arc_json()` — Solar arc calculation
9. CLI routing for `--solar-arc {slug} --year YYYY`
10. Manual testing

**Priority 4 (Timeline):**
11. `find_transit_events()` — Event timeline
12. CLI routing for `--transits {slug} --from ... --to ... --events`
13. Manual testing

**Priority 5 (Auto-Include):**
14. `--load {slug} --now` mode (load natal + current transits)
15. Combined JSON output

**Priority 6 (Skill Integration):**
16. Update SKILL.md with new routing
17. Create transit interpretation guide
18. Context injection logic

**Priority 7 (Optional Features):**
19. `--save` flag for snapshot storage
20. List saved snapshots

## Architectural Patterns

### Pattern 1: Fresh Calculation with Optional Persistence

**What:** Calculate predictive data on-demand, optionally save snapshot

**When to use:** For data that changes (transits) or is expensive to recalculate (progressions)

**Trade-offs:**
- Pro: Always current data, no stale snapshots
- Pro: Simple storage model (no cache invalidation)
- Con: Slower than cached (acceptable for CLI, 1-2 sec max)

**Example:**
```python
# Default: calculate, print, done
transit_data = build_transit_json(natal_data, datetime.now())
print(json.dumps(transit_data))

# With --save: calculate, print, AND save
if args.save:
    filepath = profile_dir / f"transits-{date.today().isoformat()}.json"
    with open(filepath, 'w') as f:
        json.dump(transit_data, f, indent=2)
```

### Pattern 2: Cross-Chart Aspect Calculation

**What:** Generic function for aspects between two sets of positions

**When to use:** Transits, progressions, solar arc, synastry (future)

**Trade-offs:**
- Pro: Single implementation, consistent aspect logic
- Pro: Reusable for all predictive techniques
- Con: More complex than hardcoded approaches

**Example:**
```python
def calculate_aspects_between_charts(chart1_positions, chart2_positions, orb=8):
    aspects = []
    aspect_angles = {
        'conjunction': 0, 'opposition': 180,
        'trine': 120, 'square': 90, 'sextile': 60
    }

    for p1 in chart1_positions:
        for p2 in chart2_positions:
            angle_diff = abs(p1['abs_position'] - p2['abs_position'])
            if angle_diff > 180:
                angle_diff = 360 - angle_diff

            for aspect_name, aspect_angle in aspect_angles.items():
                if abs(angle_diff - aspect_angle) <= orb:
                    aspects.append({
                        'planet1': p1['name'],
                        'planet2': p2['name'],
                        'aspect': aspect_name,
                        'orb': abs(angle_diff - aspect_angle)
                    })

    return aspects
```

### Pattern 3: Monolithic Extension (Keep Single File)

**What:** Add new functions to existing `astrology_calc.py` instead of splitting into modules

**When to use:** When total LOC stays under ~2,000 and functions share utilities

**Trade-offs:**
- Pro: Simple deployment (one file to manage)
- Pro: Easier to understand data flow
- Con: File gets large (current 1,070 → estimated 1,500-1,800 LOC)
- Con: Harder to unit test individual components

**Recommendation:** Stay monolithic for v1.1. Consider splitting if v2 adds synastry/composite (likely 3,000+ LOC).

## Integration Points with Existing Code

### Functions to Reuse (No Modification)

| Function | Use in Transit/Progression |
|----------|---------------------------|
| `position_to_sign_degree()` | Convert directed/progressed positions to signs |
| `valid_date()`, `valid_time()` | Parse transit dates/times |
| `ELEMENT_MAP`, `MODALITY_MAP` | Analyze transit/progression distributions |
| `get_planet_dignities()` | Dignity status of progressed planets |

### Functions to Modify

| Function | Modification Needed | Reason |
|----------|---------------------|--------|
| `main()` | Add argument groups for transits/progressions | New CLI modes |
| `check_existing_profile()` | Adapt for snapshot checking (optional) | If implementing snapshot overwrite protection |

### Functions to Add (New)

| Function | Purpose | LOC Estimate |
|----------|---------|--------------|
| `load_natal_profile(slug)` | Load natal JSON from storage | 20 |
| `build_transit_json()` | Transit calculation | 150 |
| `build_progression_json()` | Secondary progression calculation | 180 |
| `build_solar_arc_json()` | Solar arc calculation | 120 |
| `calculate_aspects_between_charts()` | Generic aspect calculation | 80 |
| `find_transit_events()` | Timeline event scanning | 150 |
| **Total new code** | | **~700 LOC** |

**Projected total:** 1,070 (current) + 700 (new) = **~1,770 LOC**

Still manageable as single file. If synastry added in v2, consider splitting.

## Anti-Patterns to Avoid

### Anti-Pattern 1: Saving Transits by Default

**What people do:** Auto-save every transit calculation to avoid recalculating

**Why it's wrong:**
- Transits change daily → accumulates stale files
- User doesn't know which snapshot is current
- Storage bloat (365 files/year per profile)
- Adds complexity for marginal performance gain (transits calculate in <1 sec)

**Do this instead:** Fresh calculation by default, `--save` only when user explicitly wants snapshot

### Anti-Pattern 2: Hardcoding Aspect Logic Per Chart Type

**What people do:** Separate aspect calculation for natal, transit, progression

**Why it's wrong:**
- Duplicates logic (maintenance burden)
- Inconsistent orbs/rules across chart types
- Harder to add new predictive techniques

**Do this instead:** Single `calculate_aspects_between_charts()` function with configurable orbs

### Anti-Pattern 3: Mixing Natal and Transit Data in Same JSON Structure

**What people do:** Add transiting positions as extra keys in `chart.json`

**Why it's wrong:**
- Natal chart is permanent, transits are ephemeral → different lifecycle
- Confuses "when was this calculated?"
- Can't have multiple transit snapshots

**Do this instead:** Separate JSON structures, combined at output layer when needed

### Anti-Pattern 4: Using String Parsing Instead of Kerykeion Objects

**What people do:** Extract positions from Kerykeion's string output instead of using object attributes

**Why it's wrong:**
- Fragile (breaks if Kerykeion changes string format)
- Loses precision (string may round values)
- More code (parsing logic vs direct attribute access)

**Do this instead:** Use `subject.sun.abs_pos`, `subject.sun.sign`, etc. (existing pattern in codebase)

### Anti-Pattern 5: Blocking Timeline Calculation for Long Ranges

**What people do:** Allow `--from 2020-01-01 --to 2030-12-31` (3,650+ days)

**Why it's wrong:**
- CLI blocks for minutes (poor UX)
- User has no progress indicator
- Likely doesn't need that granularity

**Do this instead:**
- Limit timeline to 180 days max (raise error if exceeded)
- Suggest narrowing range or using yearly progressions/solar arc for long-term trends
- Document performance expectation: ~1 sec per 10 days

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 1-10 profiles | Current architecture perfect (fresh calculation on demand) |
| 10-100 profiles | Still fine (each profile independent, no shared state) |
| 100+ profiles with frequent queries | Consider: pre-calculation daemon for "today's transits" (out of scope v1.1) |

**v1.1 target:** 1-10 profiles (personal use). No optimization needed.

## Sources

**Kerykeion Library & API:**
- [Kerykeion PyPI](https://pypi.org/project/kerykeion/) — Python astrology library for transits, natal, synastry charts
- [Kerykeion GitHub Repository](https://github.com/g-battaglia/kerykeion) — Data-driven astrology with factory-based API
- [Kerykeion Official Documentation](https://www.kerykeion.net/) — API reference and examples
- [Kerykeion Transit Chart Example](https://www.kerykeion.net/content/examples/transit-chart) — Code example for transit calculations

**Swiss Ephemeris & Pyswisseph:**
- [Swiss Ephemeris Official Documentation](https://www.astro.com/swisseph/swisseph.htm) — High-precision ephemeris library
- [Pyswisseph PyPI](https://pypi.org/project/pyswisseph/) — Python extension to Swiss Ephemeris
- [Pyswisseph GitHub](https://github.com/astrorigin/pyswisseph) — Python bindings for astrological calculations
- [Swiss Ephemeris Programming Interface](https://www.astro.com/swisseph/swephprg.htm) — API reference

**Astrological Calculation Methods:**
- [Secondary Progressions Calculator](https://horoscopes.astro-seek.com/astrology-secondary-progressions-directions-chart) — Day-for-a-year formula explanation
- [Cafe Astrology: Secondary Progressions](https://cafeastrology.com/secondaryprogressions.html) — How progressions work
- [Solar Arc Directions Calculator](https://horoscopes.astro-seek.com/solar-arc-directions-calculator) — 1 degree per year method
- [Solar Arc Directions Explanation](https://astrologyschool.net/solar-arc-directions/) — Calculation and interpretation
- [Predictive Techniques Comparison](https://hniizato.com/solar-arc-vs-secondary-progression/) — Solar arc vs secondary progression differences

**Astrology Software Architecture:**
- [ASTROGRAPH TimePassages](https://www.astrograph.com/astrology-software/) — Transit timeline and progression features
- [Astrology API Documentation](https://www.astrologyapi.com/western-api-docs/api-ref/200/natal_transits/daily) — JSON data format for transits
- [AstroJSON GitHub](https://github.com/neilg63/astrojson) — CLI tool for astrology data in JSON format
- [Solar Fire Software Features](https://www.soulhealing.com/timemaps.htm) — Transit graph architecture patterns

---
*Architecture research for: Transit & Progression Integration (v1.1 Milestone)*
*Researched: 2026-02-17*
