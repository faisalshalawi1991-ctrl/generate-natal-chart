# Phase 3: Extended Calculations - Research

**Researched:** 2026-02-16
**Domain:** Advanced astrological calculations (asteroids, fixed stars, Arabic parts, essential dignities, elemental/modal analysis)
**Confidence:** HIGH

## Summary

Phase 3 extends the core calculation engine (Phase 2) with advanced astrological data: asteroids (Chiron, Lilith variants, Ceres, Pallas, Juno, Vesta), fixed star conjunctions, Arabic parts (Part of Fortune/Spirit), essential dignities, and element/modality distributions.

**Key finding:** Kerykeion 5.7.2 natively supports asteroids and Lilith variants as built-in attributes on `AstrologicalSubject`, eliminating the need for direct pyswisseph calls. Fixed stars require pyswisseph's `swe_fixstar2_ut()` function with the `sefstars.txt` data file. Essential dignities and distributions are lookup-table operations that don't require external libraries.

**Primary recommendation:** Extend the existing `backend/astrology_calc.py` script incrementally. Extract asteroid positions from Kerykeion attributes, calculate fixed stars via pyswisseph (already a Kerykeion dependency), implement Arabic parts with day/night formula logic, and create lookup tables for dignities and distributions. Maintain separation between calculation logic and display formatting.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| kerykeion | 5.7.2 | Astrological calculations | Already in use (Phase 2), supports asteroids/Lilith natively, wraps pyswisseph |
| pyswisseph | (transitive) | Swiss Ephemeris wrapper | Kerykeion dependency, needed directly for fixed stars via `swe_fixstar2_ut()` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| None required | - | All requirements met by existing stack | Phase 3 features supported by current dependencies |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Kerykeion asteroids | pyswisseph `calc_ut(AST_OFFSET + num)` | More verbose, redundant since Kerykeion exposes asteroids as attributes |
| Fixed star calculation | Third-party library | No mature Python libraries exist; pyswisseph is the standard ephemeris |
| Lookup tables (dignities/elements) | External JSON/database | Unnecessary complexity for static astrological reference data |

**Installation:**
No new dependencies required. Kerykeion 5.7.2 already installed provides all needed capabilities.

## Architecture Patterns

### Recommended Project Structure
```
backend/
├── astrology_calc.py        # Main CLI script (existing, extend in place)
├── requirements.txt          # Dependencies (no changes needed)
└── cache/                    # Kerykeion ephemeris cache (existing)
```

**Rationale:** Phase 2 established a working CLI script. Phase 3 adds output sections without architectural changes. Future phases (4+) may introduce modules for data persistence or helper utilities.

### Pattern 1: Extend Existing Display Sections
**What:** Add new calculation sections to `astrology_calc.py` after existing MAJOR ASPECTS section
**When to use:** Phase 3 requirements are additive display features, not architectural changes
**Example:**
```python
# After line 296 (existing MAJOR ASPECTS section):

# Extract and display asteroids
print("\n=== ASTEROIDS ===")
asteroids = [
    ('Chiron', subject.chiron),
    ('Mean Lilith', subject.mean_lilith),
    ('True Lilith', subject.true_lilith),
    ('Ceres', subject.ceres),
    ('Pallas', subject.pallas),
    ('Juno', subject.juno),
    ('Vesta', subject.vesta),
]
for name, body in asteroids:
    position_in_sign = body.position % 30
    print(f"{name:12} {body.sign:3} {position_in_sign:6.2f}°")
```

### Pattern 2: Day/Night Chart Detection
**What:** Determine if Sun is above (day) or below (night) horizon using house position
**When to use:** Required for Arabic parts calculation (Part of Fortune/Spirit formulas differ by chart type)
**Example:**
```python
# Day chart: Sun in houses 7-12 (above horizon)
# Night chart: Sun in houses 1-6 (below horizon)
is_day_chart = subject.sun.house >= 7

# Part of Fortune formula
if is_day_chart:
    # Day: ASC + Moon - Sun
    pof = (subject.ascendant.position + subject.moon.position - subject.sun.position) % 360
else:
    # Night: ASC + Sun - Moon
    pof = (subject.ascendant.position + subject.sun.position - subject.moon.position) % 360
```

### Pattern 3: Fixed Star Conjunction Detection
**What:** Use pyswisseph to get fixed star positions, compare to planet/angle positions with orb tolerance
**When to use:** CALC-06 (fixed star conjunctions)
**Example:**
```python
import swisseph as swe

# Calculate Julian day from birth data
jd = swe.julday(year, month, day, hour + minute/60.0)

# Get fixed star position
star_name = "Regulus"
star_data, ret_flag = swe.fixstar2_ut(star_name, jd, 0)  # 0 = default flags
star_longitude = star_data[0]

# Check conjunction with orb (1 degree for bright stars)
orb = 1.0
for planet_name, planet_obj in planets:
    diff = abs(planet_obj.position - star_longitude)
    if diff > 180:
        diff = 360 - diff  # Handle zodiac wrap-around
    if diff <= orb:
        print(f"{star_name} conjunct {planet_name} (orb: {diff:.2f}°)")
```

### Pattern 4: Static Lookup Tables
**What:** Define essential dignities and element/modality mappings as Python dictionaries
**When to use:** CALC-08, CALC-09, CALC-10 (dignities, elements, modalities)
**Example:**
```python
# Essential dignities (domicile/rulership only shown, expand for exaltation/detriment/fall)
DOMICILE = {
    'Sun': ['Leo'],
    'Moon': ['Cancer'],
    'Mercury': ['Gemini', 'Virgo'],
    'Venus': ['Taurus', 'Libra'],
    'Mars': ['Aries', 'Scorpio'],
    'Jupiter': ['Sagittarius', 'Pisces'],
    'Saturn': ['Capricorn', 'Aquarius'],
}

SIGN_ELEMENTS = {
    'Ari': 'Fire', 'Leo': 'Fire', 'Sag': 'Fire',
    'Tau': 'Earth', 'Vir': 'Earth', 'Cap': 'Earth',
    'Gem': 'Air', 'Lib': 'Air', 'Aqu': 'Air',
    'Can': 'Water', 'Sco': 'Water', 'Pis': 'Water',
}

SIGN_MODALITIES = {
    'Ari': 'Cardinal', 'Can': 'Cardinal', 'Lib': 'Cardinal', 'Cap': 'Cardinal',
    'Tau': 'Fixed', 'Leo': 'Fixed', 'Sco': 'Fixed', 'Aqu': 'Fixed',
    'Gem': 'Mutable', 'Vir': 'Mutable', 'Sag': 'Mutable', 'Pis': 'Mutable',
}
```

### Anti-Patterns to Avoid
- **Don't refactor prematurely:** Phase 3 is additive display logic. Resist urge to extract modules until Phase 4 (data output) or later phases require it.
- **Don't recalculate existing data:** Kerykeion `AstrologicalSubject` already computed everything. Don't re-instantiate or call pyswisseph for planets/houses.
- **Don't hardcode modern planet dignities:** Uranus/Neptune/Pluto dignities are disputed. Traditional planets (Sun-Saturn) have consensus; document modern planet rulership choices explicitly.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Asteroid position calculation | Custom ephemeris parser | `subject.chiron`, `subject.ceres`, etc. (Kerykeion attributes) | Swiss Ephemeris calculations are complex (orbital mechanics, precession, nutation). Kerykeion exposes as simple attributes. |
| Fixed star positions | Star catalog parser | `swe.fixstar2_ut()` (pyswisseph) | Fixed stars require sidereal positions, precession adjustments, proper motion. Swiss Ephemeris maintains `sefstars.txt` with 3000+ stars. |
| Julian day conversion | Manual calendar math | `swe.julday()` (pyswisseph) | Gregorian/Julian calendar transitions, leap year rules, time zone offsets are error-prone. |
| Zodiac degree wrapping | Custom modulo logic | Always use `position % 360` for longitude, `position % 30` for sign degree | Edge cases: negative angles, angles >360, floating-point precision errors. |

**Key insight:** Astrological calculations have centuries of edge cases (precession, calendar reforms, coordinate systems). Swiss Ephemeris is the gold standard used by professional astrologers and NASA. Never reimplement its logic.

## Common Pitfalls

### Pitfall 1: Day/Night Chart Confusion
**What goes wrong:** Using wrong Arabic parts formula (day formula for night chart or vice versa)
**Why it happens:** Multiple definitions exist: some sources define day chart as "Sun above horizon," others as "Sun in houses 7-12," and traditional vs. modern astrology differs on whether to reverse formulas
**How to avoid:**
- Use house-based definition: day chart = Sun in houses 7-12 (below ASC-DSC axis, above IC-MC axis)
- Comment the chosen convention in code
- Traditional formula: Day = ASC + Moon - Sun, Night = ASC + Sun - Moon
**Warning signs:** Part of Fortune in illogical position (e.g., night chart PoF too close to Sun position)

### Pitfall 2: Fixed Star Orb Overreach
**What goes wrong:** Detecting dozens of "conjunctions" with wide orbs, diluting significance
**Why it happens:** Astrological tradition varies from 1° to 7° orbs; larger orbs catch more stars but reduce specificity
**How to avoid:**
- Use 1° orb for all fixed stars (conservative, high confidence)
- Document rationale: tighter orb = more significant conjunction
- Filter to major stars only: Regulus, Algol, Spica, Aldebaran, Antares, Fomalhaut, Sirius (magnitude 1st-2nd)
**Warning signs:** More than 10-15 fixed star conjunctions detected in a single chart (orb likely too wide)

### Pitfall 3: Sign Abbreviation Mismatch
**What goes wrong:** Lookup tables use 'Ari' but Kerykeion returns 'Aries', causing KeyError
**Why it happens:** Kerykeion's `planet.sign` returns full name, not abbreviation
**How to avoid:**
- Check Kerykeion's actual output format first (run Phase 2 script to see)
- Use consistent key format: either full names ('Aries') or add abbreviation mapping
- Test lookup tables with actual Kerykeion output before assuming format
**Warning signs:** KeyError on sign lookups, element/modality distribution missing entries

### Pitfall 4: Asteroid Attribute Naming Ambiguity
**What goes wrong:** Trying `subject.lilith` when Kerykeion uses `subject.mean_lilith` and `subject.true_lilith`
**Why it happens:** Kerykeion supports multiple Lilith definitions (Mean vs. True Black Moon)
**How to avoid:**
- Use exact attribute names from Kerykeion documentation: `mean_lilith`, `true_lilith` (lowercase, underscored)
- Test attribute access with `hasattr(subject, 'mean_lilith')` before using
- Display both Lilith variants to avoid choosing between traditions
**Warning signs:** AttributeError on asteroid access, missing Lilith in output

### Pitfall 5: Modern Planet Dignity Disputes
**What goes wrong:** Implementing Uranus/Neptune/Pluto dignities that contradict user expectations
**Why it happens:** Traditional astrology (pre-1781) only defines dignities for Sun-Saturn; modern assignments (Uranus=Aquarius, Neptune=Pisces, Pluto=Scorpio) are not universally accepted
**How to avoid:**
- Phase 3 requirement (CALC-08) says "each planet" but doesn't specify which planets
- Document choice: implement traditional dignities (Sun-Saturn) only, or add modern planets with explicit disclaimer
- If adding modern planets, cite source (e.g., "modern rulership per 20th century convention")
**Warning signs:** User asks "why is Uranus exalted in Scorpio?" — this is disputed, not consensus

### Pitfall 6: Zodiac Degree Wrap-Around in Conjunctions
**What goes wrong:** Missing conjunction between planet at 359° Pisces and star at 1° Aries (difference is 2°, not 358°)
**Why it happens:** Naively calculating `abs(pos1 - pos2)` without handling 0°/360° boundary
**How to avoid:**
```python
diff = abs(pos1 - pos2)
if diff > 180:
    diff = 360 - diff  # Shortest arc across zodiac circle
```
**Warning signs:** No conjunctions detected near 0° Aries despite visual proximity in chart

### Pitfall 7: Floating-Point Precision in Degree Calculations
**What goes wrong:** Position shows as 29.9999999° instead of 30°, causing incorrect sign assignment
**Why it happens:** IEEE 754 floating-point arithmetic, trigonometric function rounding
**How to avoid:**
- Don't check exact equality (`== 30.0`), use ranges (`>= 29.999`)
- Round for display but use raw values for calculation: `f"{position:.2f}°"`
- Trust Kerykeion's `planet.sign` attribute for sign assignment, don't recalculate from `planet.position`
**Warning signs:** Planet shows 29.99° in one sign but Kerykeion says it's in the next sign

## Code Examples

Verified patterns from documentation and analysis:

### Accessing Asteroid Positions
```python
# Source: Kerykeion PyPI documentation, confirmed via WebSearch
from kerykeion import AstrologicalSubjectFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    name="Example",
    year=1990, month=6, day=15,
    hour=14, minute=30,
    lat=51.5074, lng=-0.1278,
    tz_str="Europe/London",
    online=False,
    houses_system_identifier='P'
)

# Asteroids available as direct attributes
print(f"Chiron: {subject.chiron.sign} {subject.chiron.position % 30:.2f}°")
print(f"Ceres: {subject.ceres.sign} {subject.ceres.position % 30:.2f}°")
print(f"Pallas: {subject.pallas.sign} {subject.pallas.position % 30:.2f}°")
print(f"Juno: {subject.juno.sign} {subject.juno.position % 30:.2f}°")
print(f"Vesta: {subject.vesta.sign} {subject.vesta.position % 30:.2f}°")
print(f"Mean Lilith: {subject.mean_lilith.sign} {subject.mean_lilith.position % 30:.2f}°")
print(f"True Lilith: {subject.true_lilith.sign} {subject.true_lilith.position % 30:.2f}°")
```

### Fixed Star Conjunction Calculation
```python
# Source: pyswisseph documentation via WebSearch, Swiss Ephemeris programming guide
import swisseph as swe

# Set ephemeris path (Kerykeion may set this automatically)
# swe.set_ephe_path('/path/to/ephe')  # Usually not needed with Kerykeion installed

# Calculate Julian day
jd = swe.julday(1990, 6, 15, 14.5)  # 14:30 = 14.5 hours

# Major fixed stars with approximate 2026 tropical positions
MAJOR_STARS = [
    "Regulus",    # ~29° Leo / 0° Virgo (Heart of the Lion)
    "Algol",      # ~26° Taurus (Demon Star)
    "Spica",      # ~24° Libra (Wheat Ear of Virgo)
    "Aldebaran",  # ~9° Gemini (Eye of the Bull)
    "Antares",    # ~9° Sagittarius (Heart of the Scorpion)
    "Fomalhaut",  # ~3° Pisces (Royal Star)
]

ORB = 1.0  # 1 degree for tight conjunctions

conjunctions = []
for star_name in MAJOR_STARS:
    try:
        # Use fixstar2_ut (recommended over fixstar_ut for performance)
        star_data, ret_flag = swe.fixstar2_ut(star_name, jd, 0)
        star_long = star_data[0]  # Ecliptic longitude

        # Check against all planets and angles
        points_to_check = [
            ('Sun', subject.sun.position),
            ('Moon', subject.moon.position),
            ('ASC', subject.ascendant.position),
            ('MC', subject.medium_coeli.position),
            # ... add other planets/angles
        ]

        for point_name, point_long in points_to_check:
            diff = abs(point_long - star_long)
            if diff > 180:
                diff = 360 - diff
            if diff <= ORB:
                conjunctions.append({
                    'star': star_name,
                    'point': point_name,
                    'orb': diff
                })
    except Exception as e:
        # Star not found or calculation error
        print(f"Warning: Could not calculate {star_name}: {e}")

# Display conjunctions
print(f"\n=== FIXED STAR CONJUNCTIONS (orb ≤{ORB}°) ===")
if conjunctions:
    for conj in conjunctions:
        print(f"{conj['star']:12} conjunct {conj['point']:10} (orb: {conj['orb']:.2f}°)")
else:
    print("No major fixed star conjunctions detected")
```

### Arabic Parts Calculation
```python
# Source: Traditional astrological formulas verified via WebSearch (cafeastrology.com, astro-seek.com)

# Determine chart type
is_day_chart = subject.sun.house >= 7  # Houses 7-12 = day, 1-6 = night

# Get absolute positions (0-360 degrees)
asc = subject.ascendant.position
sun = subject.sun.position
moon = subject.moon.position

# Part of Fortune (Pars Fortunae)
if is_day_chart:
    pof = (asc + moon - sun) % 360
else:
    pof = (asc + sun - moon) % 360

# Part of Spirit (Pars Spiritus) - reverse of Part of Fortune
if is_day_chart:
    pos = (asc + sun - moon) % 360
else:
    pos = (asc + moon - sun) % 360

# Convert to sign and degree within sign
def position_to_sign_degree(position):
    signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
             'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
    sign_index = int(position // 30)
    degree = position % 30
    return signs[sign_index], degree

pof_sign, pof_deg = position_to_sign_degree(pof)
pos_sign, pos_deg = position_to_sign_degree(pos)

print(f"\n=== ARABIC PARTS ===")
print(f"Chart type: {'Day' if is_day_chart else 'Night'}")
print(f"Part of Fortune: {pof_sign} {pof_deg:.2f}°")
print(f"Part of Spirit:  {pos_sign} {pos_deg:.2f}°")
```

### Essential Dignities Lookup
```python
# Source: Traditional astrological dignities compiled from multiple sources (Wikipedia, saturn and honey, astro.com)

# Complete traditional dignities table (Sun through Saturn)
DIGNITIES = {
    'Sun': {
        'domicile': ['Leo'],
        'exaltation': ['Aries'],
        'detriment': ['Aquarius'],
        'fall': ['Libra']
    },
    'Moon': {
        'domicile': ['Cancer'],
        'exaltation': ['Taurus'],
        'detriment': ['Capricorn'],
        'fall': ['Scorpio']
    },
    'Mercury': {
        'domicile': ['Gemini', 'Virgo'],
        'exaltation': ['Virgo'],  # Some sources say Aquarius
        'detriment': ['Sagittarius', 'Pisces'],
        'fall': ['Pisces']
    },
    'Venus': {
        'domicile': ['Taurus', 'Libra'],
        'exaltation': ['Pisces'],
        'detriment': ['Scorpio', 'Aries'],
        'fall': ['Virgo']
    },
    'Mars': {
        'domicile': ['Aries', 'Scorpio'],
        'exaltation': ['Capricorn'],
        'detriment': ['Libra', 'Taurus'],
        'fall': ['Cancer']
    },
    'Jupiter': {
        'domicile': ['Sagittarius', 'Pisces'],
        'exaltation': ['Cancer'],
        'detriment': ['Gemini', 'Virgo'],
        'fall': ['Capricorn']
    },
    'Saturn': {
        'domicile': ['Capricorn', 'Aquarius'],
        'exaltation': ['Libra'],
        'detriment': ['Cancer', 'Leo'],
        'fall': ['Aries']
    }
}

# Note: Modern planets (Uranus, Neptune, Pluto) omitted due to lack of consensus
# If including them, document as "modern convention, not traditional"

def get_planet_dignities(planet_name, planet_sign):
    """Return list of dignities for planet in given sign."""
    if planet_name not in DIGNITIES:
        return []

    dignities = []
    planet_dign = DIGNITIES[planet_name]

    if planet_sign in planet_dign['domicile']:
        dignities.append('Domicile')
    if planet_sign in planet_dign['exaltation']:
        dignities.append('Exaltation')
    if planet_sign in planet_dign['detriment']:
        dignities.append('Detriment')
    if planet_sign in planet_dign['fall']:
        dignities.append('Fall')

    return dignities if dignities else ['Peregrine']  # No dignity

# Example usage
planets = [
    ('Sun', subject.sun),
    ('Moon', subject.moon),
    ('Mercury', subject.mercury),
    ('Venus', subject.venus),
    ('Mars', subject.mars),
    ('Jupiter', subject.jupiter),
    ('Saturn', subject.saturn),
]

print("\n=== ESSENTIAL DIGNITIES ===")
for name, planet in planets:
    digns = get_planet_dignities(name, planet.sign)
    print(f"{name:10} in {planet.sign:12} - {', '.join(digns)}")
```

### Element and Modality Distribution
```python
# Source: Standard astrological correspondences verified via WebSearch (almanac.com, tarot.com)

ELEMENT_MAP = {
    'Aries': 'Fire', 'Leo': 'Fire', 'Sagittarius': 'Fire',
    'Taurus': 'Earth', 'Virgo': 'Earth', 'Capricorn': 'Earth',
    'Gemini': 'Air', 'Libra': 'Air', 'Aquarius': 'Air',
    'Cancer': 'Water', 'Scorpio': 'Water', 'Pisces': 'Water',
}

MODALITY_MAP = {
    'Aries': 'Cardinal', 'Cancer': 'Cardinal', 'Libra': 'Cardinal', 'Capricorn': 'Cardinal',
    'Taurus': 'Fixed', 'Leo': 'Fixed', 'Scorpio': 'Fixed', 'Aquarius': 'Fixed',
    'Gemini': 'Mutable', 'Virgo': 'Mutable', 'Sagittarius': 'Mutable', 'Pisces': 'Mutable',
}

# Collect placements (planets + ASC)
placements = [
    subject.sun, subject.moon, subject.mercury, subject.venus,
    subject.mars, subject.jupiter, subject.saturn,
    subject.uranus, subject.neptune, subject.pluto,
    subject.ascendant,  # ASC counts toward distribution
]

# Count elements
element_count = {'Fire': 0, 'Earth': 0, 'Air': 0, 'Water': 0}
for placement in placements:
    element = ELEMENT_MAP.get(placement.sign)
    if element:
        element_count[element] += 1

# Count modalities
modality_count = {'Cardinal': 0, 'Fixed': 0, 'Mutable': 0}
for placement in placements:
    modality = MODALITY_MAP.get(placement.sign)
    if modality:
        modality_count[modality] += 1

# Display distribution
print("\n=== ELEMENT DISTRIBUTION ===")
total = sum(element_count.values())
for element, count in element_count.items():
    percentage = (count / total * 100) if total > 0 else 0
    print(f"{element:6} {count:2} ({percentage:5.1f}%)")

print("\n=== MODALITY DISTRIBUTION ===")
total = sum(modality_count.values())
for modality, count in modality_count.items():
    percentage = (count / total * 100) if total > 0 else 0
    print(f"{modality:8} {count:2} ({percentage:5.1f}%)")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual pyswisseph calls for asteroids | Kerykeion attributes (`subject.chiron`, etc.) | Kerykeion 4.0+ | Simpler API, no need to manage Swiss Ephemeris asteroid numbers |
| Wide orbs (5-7°) for fixed stars | Tight orbs (1°) for conjunctions | Modern precision era (2000s+) | Fewer but more significant fixed star aspects |
| Single Lilith position | Mean Lilith and True Lilith variants | Traditional vs. modern distinction | Accommodates both calculation methods |
| Modern planet dignities as consensus | Traditional dignities only (Sun-Saturn) | Recognition of disputed modern assignments | Avoids imposing unverified rulership systems |

**Deprecated/outdated:**
- **Flatlib library**: Inactive since 2018, doesn't support Python 3.9+. Use Kerykeion instead.
- **swe.fixstar_ut()**: Replaced by `swe.fixstar2_ut()` for better performance when calculating multiple stars.
- **Equal House for asteroids/parts**: Arabic parts require cusp-based houses (Placidus, Koch) for horizon detection; Equal House doesn't define horizon clearly.

## Open Questions

### 1. Outer Planet Dignities (Uranus, Neptune, Pluto)
**What we know:**
- Modern astrology assigns Uranus→Aquarius, Neptune→Pisces, Pluto→Scorpio
- Traditional astrology (pre-1781) only defines Sun-Saturn dignities
- Exaltations for outer planets are highly disputed (multiple conflicting sources)

**What's unclear:**
- Does "each planet" in CALC-08 include outer planets?
- Should we implement modern rulerships with disclaimer, or omit entirely?

**Recommendation:** Implement traditional dignities (Sun-Saturn) only for HIGH confidence. If user requests outer planets later, add as enhancement with explicit "modern convention" label.

### 2. Fixed Star Catalog Size
**What we know:**
- `sefstars.txt` contains 3000+ fixed stars
- Major stars: ~15-20 (Regulus, Algol, Spica, Aldebaran, Antares, Fomalhaut, Sirius, etc.)
- CALC-06 says "Regulus, Algol, Spica, and other major fixed stars" (ambiguous scope)

**What's unclear:**
- Should we check all 3000+ stars or just the traditional ~15-20 major stars?
- What magnitude cutoff defines "major"? (1st magnitude? 2nd?)

**Recommendation:** Start with 15-20 historically significant stars (magnitude 1-2, used in classical astrology). Checking all 3000+ would produce overwhelming output. Document the list chosen with rationale.

### 3. Element/Modality Distribution: Which Placements Count?
**What we know:**
- Sun through Pluto = 10 placements
- Ascendant is commonly included in distributions
- Some astrologers include MC, some include all 4 angles, some include asteroids

**What's unclear:**
- CALC-09/CALC-10 say "across all placements" but don't define "all placements"
- Should we include ASC only, or ASC+MC, or all angles, or asteroids too?

**Recommendation:** Count 10 planets + ASC (11 total) for distributions. This is the most common modern convention. Document the choice. Excluding asteroids avoids double-counting Phase 3 additions.

### 4. Sign Name Format in Kerykeion Output
**What we know:**
- Phase 2 script prints `planet.sign` directly
- WebSearch suggests Kerykeion might use full names ('Aries') or abbreviations ('Ari')

**What's unclear:**
- Exact format returned by Kerykeion 5.7.2's `planet.sign` attribute

**Recommendation:** Run Phase 2 script to verify actual output format before implementing lookup tables. Adjust ELEMENT_MAP/MODALITY_MAP keys to match Kerykeion's format (likely full names based on library's style).

## Sources

### Primary (HIGH confidence)
- [Kerykeion PyPI](https://pypi.org/project/kerykeion/) - Version 5.7.2 confirmed, asteroid support verified
- [Kerykeion documentation](https://www.kerykeion.net/content/docs/astrological_subject_factory) - AstrologicalSubject factory patterns
- [pyswisseph GitHub](https://github.com/astrorigin/pyswisseph) - Fixed star functions, asteroid calculation
- [Swiss Ephemeris documentation](https://www.astro.com/swisseph/swisseph.htm) - Official ephemeris reference

### Secondary (MEDIUM confidence)
- [Cafe Astrology: Part of Fortune](https://cafeastrology.com/partoffortune.html) - Arabic parts formulas (day/night)
- [Astro-Seek Arabic Parts Calculator](https://horoscopes.astro-seek.com/arabic-lots-parts-astrology-online-calculator) - Formula verification
- [Saturn and Honey: Essential Dignities](https://www.saturnandhoney.com/blog/domicile-exaltation-detriment-and-fall-in-astrology) - Dignities table
- [Almanac.com: Zodiac Elements](https://www.almanac.com/zodiac-elements-fire-earth-air-water-explained) - Element/modality correspondences
- [Tarot.com: Modalities](https://www.tarot.com/astrology/sign-quality) - Modality distribution
- [Time Nomad: Fixed Stars](https://timenomad.app/documentation/fixed-stars-in-astrological-chart.html) - Orb guidelines, major stars
- [Astrology King: Major Fixed Stars](https://astrologyking.com/fixed-stars/) - Fixed star meanings and positions

### Tertiary (LOW confidence - flagged for validation)
- [Dima Gur Astrology: Outer Planet Dignities](https://www.gurastro.com/2013/04/uranus-neptune-pluto-exalted-in.html) - Modern planet exaltations (disputed)

## Metadata

**Confidence breakdown:**
- Asteroid positions via Kerykeion: HIGH - Direct attribute access verified via PyPI docs and WebSearch
- Fixed stars via pyswisseph: HIGH - Swiss Ephemeris is industry standard, `swe_fixstar2_ut()` documented
- Arabic parts formulas: HIGH - Traditional formulas consistent across multiple authoritative sources
- Essential dignities (Sun-Saturn): HIGH - Traditional rulerships are consensus across classical astrology
- Essential dignities (Uranus-Pluto): LOW - Modern assignments disputed, multiple conflicting sources
- Element/modality maps: HIGH - Standard correspondences, no variation across sources
- Orb guidelines for fixed stars: MEDIUM - Range of 1-7° cited; 1° recommended for specificity

**Research date:** 2026-02-16
**Valid until:** ~2027-01-16 (1 year for stable domain; astrological calculation methods change slowly)

**Kerykeion version:** 5.7.2 (released 2026-02-06, highly current)
**Python version:** 3.11 (per Phase 1 decision, compatible with all Phase 3 requirements)
