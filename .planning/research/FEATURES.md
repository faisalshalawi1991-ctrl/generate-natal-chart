# Feature Research: Transits & Progressions

**Domain:** Transit, Progression & Solar Arc Analysis for Astrology Software
**Researched:** 2026-02-17
**Confidence:** HIGH

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Current transit snapshot | Every astrology tool shows "where planets are now" | LOW | Single datetime calculation, reuses natal chart aspect logic |
| Transit-to-natal aspects | Core purpose of transits — what's affecting your chart | MEDIUM | Aspect grid between two chart sets (transit planets → natal planets) |
| Major transit aspects only | Hard aspects (conjunction, square, opposition) are standard | LOW | Filter existing aspect detection to hard aspects |
| Configurable orbs for transits | Different aspects use different orbs (1-3°) | LOW | Add orb parameter to aspect calculation functions |
| Secondary progressions | Day-for-a-year is foundational predictive technique | MEDIUM | Birth date + N days = year N positions, same chart structure as natal |
| Solar arc directions | Standard modern predictive method alongside progressions | MEDIUM | Sun's daily motion applied to all planets, simpler than progressions |
| Progressed-to-natal aspects | Shows internal psychological evolution | MEDIUM | Same aspect grid logic as transits, different planet set |
| Solar arc-to-natal aspects | Timing major life events via solar arc contacts | MEDIUM | Same aspect grid logic, solar arc positions as source |
| Date range for progressions | Users specify age or target year for progression snapshot | LOW | Date arithmetic: birth_date + (years * 1 day) |
| Visual chart wheel output | Kerykeion provides SVG for bi-wheel/tri-wheel | MEDIUM | Already exists for natal, extend to transit/progression overlays |
| House positions for transits | Which house transiting planets occupy | LOW | Same house calculation logic as natal, using birth location |
| Retrograde status in transits | Flag which planets are retrograde in transit chart | LOW | Already captured in natal chart, same logic applies |

### Differentiators (Competitive Advantage)

Features that set the product apart. Not required, but valuable.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Auto-load transits with chart | Context-aware: show current transits when loading any profile | LOW | Skill layer: always append current transit calc when loading chart JSON |
| Transit timeline with presets | "Next 3 months", "Next year", "Custom range" | MEDIUM | Multiple transit calculations across date range, aggregate aspects by date |
| Retrograde station tracking | Detect when transiting planets station retrograde/direct | MEDIUM | Calculate planetary direction changes within date range |
| Interpretation guide for predictive work | Like natal guide, but focused on timing/aspects/progressions | LOW | Write comprehensive markdown guide for transit/progression interpretation |
| Fresh vs snapshot modes | Current calculation (fresh) vs saved snapshot (audit trail) | LOW | Save transit/progression JSON with timestamp, optionally reuse |
| Progressed Moon phase tracking | Moon moves 12-14° per year, changes sign every ~2.5 years | LOW | Already calculated in progressions, just highlight in output |
| Aspect exactness dates | "Transit exact on 2026-03-15" instead of just "in orb" | HIGH | Requires iterative date search to find exact aspect degree match |
| Element/modality shifts in progressions | Track when progressed planets change signs → temperament shifts | LOW | Reuse existing element/modality distribution logic |
| Multiple time zone support | Transits calculated for chart's birth location, not current location | LOW | Use natal chart's timezone for all calculations |
| Tri-wheel display | Natal (inner) + Progressions (middle) + Transits (outer) | MEDIUM | Kerykeion supports multi-wheel, requires data structure alignment |
| Applying vs separating aspects | Flag whether aspect is forming or fading | LOW | Compare planet speeds or check orb change over time |
| Aspect grid terminal display | Clean tabular output for aspects in CLI | LOW | Format JSON aspect data as readable table |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Transit alerts/notifications | "Tell me when Jupiter trines my Sun" | Introduces state management, notification infrastructure, scheduling overhead | Provide timeline view showing all upcoming aspects — user chooses what to track |
| Solar/Lunar returns | Annual/monthly charts are standard astrology tools | Different chart type with location dependency (where you are at return time) — adds complexity | Defer to v2.0, focus on transit/progression overlays on natal chart first |
| Synastry/composite charts | Compare two natal charts for compatibility | Requires two-chart loading, different aspect interpretation context | Explicitly out of scope for v1.1, deferred to v2 milestone |
| Real-time updating transits | Live clock showing planets moving | Calculation overhead, UI complexity, no benefit for CLI tool | Calculate current transits on-demand when chart is loaded |
| Minor aspects for transits | Quintiles, semi-sextiles, etc. | Low signal-to-noise, standard practice uses hard aspects only | Stick to major aspects (0°, 60°, 90°, 120°, 180°) |
| Multiple house systems for progressions | Offer Placidus, Koch, Whole Sign, etc. | Kerykeion v1.0 constraint, adds config complexity | Use Placidus (natal chart default) for consistency, defer customization |
| Progressed angles (ASC/MC) | Technically calculable but multiple calculation methods exist | No single standard method — Solar Arc vs True Secondary vs Mean Quotidian | Calculate using solar arc method, document limitation clearly |
| Transit aspects to progressed planets | Transits to progressions (not just natal) | Adds combinatorial explosion (transits to natal AND to progressed) | Focus on transits-to-natal and progressions-to-natal, defer transit-to-progression |

## Feature Dependencies

```
[Natal Chart Data]  ← Required foundation for all predictive features
    ↓
    ├──> [Current Transit Snapshot]
    │        ├──> [Transit-to-Natal Aspects]
    │        ├──> [Transit House Positions] (uses natal birth location)
    │        └──> [Transit Timeline] (multiple snapshots across date range)
    │                 └──> [Retrograde Station Tracking]
    │
    ├──> [Secondary Progressions]
    │        ├──requires──> [Date Range Parsing] (target age/year)
    │        ├──> [Progressed-to-Natal Aspects]
    │        └──enhances──> [Progressed Moon Sign Tracking]
    │
    ├──> [Solar Arc Directions]
    │        ├──requires──> [Date Range Parsing] (target age/year)
    │        └──> [Solar Arc-to-Natal Aspects]
    │
    └──> [Interpretation Guide] ──enhances──> [All Features]

[Tri-Wheel Display]
    ├──requires──> [Natal Chart] (inner wheel)
    ├──requires──> [Secondary Progressions] (middle wheel)
    └──requires──> [Current Transits] (outer wheel)
```

### Dependency Notes

- **Current Transit Snapshot requires Natal Chart Data:** Transit house positions only meaningful relative to natal chart's birth location. Transits calculated for the natal chart's location timezone, not current location.
- **Transit Timeline requires Current Transit Snapshot:** Timeline is multiple snapshot calculations across date range, same core logic repeated.
- **Secondary Progressions requires Natal Chart Data:** Day-for-a-year formula anchored to exact birth date and time. Progressed positions calculated from ephemeris starting at birth date + N days.
- **Solar Arc Directions requires Natal Chart Data:** Solar arc = progressed Sun position - natal Sun position. This arc applied uniformly to all natal planets.
- **All aspect calculations require both source and target charts:** Aspect detection is always planet-to-planet comparison between two sets (e.g., transiting Jupiter to natal Sun).
- **Interpretation Guide enhances all features:** Transforms raw aspect data into actionable astrological context for Claude to synthesize.
- **Tri-Wheel Display requires all three chart types:** Kerykeion can generate tri-wheel SVG, but complexity increases with three simultaneous chart datasets.

## MVP Definition

### Launch With (v1.1)

Minimum viable transit/progression system — what's needed to validate the predictive capability.

- [x] **Current transit snapshot** — Auto-calculated when loading chart profiles, shows "what's happening now"
- [x] **Transit-to-natal aspects** — Core predictive value, which transits are active
- [x] **Secondary progressions for target date** — Day-for-a-year calculation for specified age/year
- [x] **Progressed-to-natal aspects** — Internal psychological timing
- [x] **Solar arc directions for target date** — Add Sun's arc to all planets
- [x] **Solar arc-to-natal aspects** — Event timing via solar arc contacts
- [x] **Interpretation guide** — Dedicated markdown guide for reading transits/progressions/solar arcs
- [x] **Configurable orbs** — Different orbs for transit (1-3°), progression (1°), solar arc (0.5-1°)
- [x] **House positions** — Transits/progressions show which natal houses they occupy
- [x] **Retrograde status** — Flag retrograde planets in all chart types
- [x] **Aspect grid display** — Terminal-friendly table showing active aspects

### Add After Validation (v1.x)

Features to add once core is working and usage patterns emerge.

- [ ] **Transit timeline** — Trigger: User requests "show upcoming aspects" beyond current snapshot
- [ ] **Retrograde station tracking in timelines** — Trigger: User asks about Mercury retrograde periods
- [ ] **Progressed Moon sign tracking** — Trigger: User focuses on emotional evolution timing
- [ ] **Aspect exactness dates** — Trigger: User wants precise timing ("when exactly is this aspect exact?")
- [ ] **Tri-wheel SVG output** — Trigger: User wants visual comparison of natal/progressed/transit
- [ ] **Element/modality progression tracking** — Trigger: User asks about temperament shifts over time
- [ ] **Applying vs separating indicators** — Trigger: User wants to know if aspect is forming or fading
- [ ] **Custom date ranges for timelines** — Trigger: User needs specific date range instead of presets

### Future Consideration (v2+)

Features to defer until transit/progression foundation is solid.

- [ ] **Solar returns** — Why defer: Different chart type, location-dependent, adds complexity
- [ ] **Lunar returns** — Why defer: Monthly calculations, high frequency, marginal value in CLI context
- [ ] **Transit aspects to progressed planets** — Why defer: Combinatorial complexity, advanced technique
- [ ] **Multiple house systems** — Why defer: Kerykeion limitation, config complexity, low priority
- [ ] **Transit alerts/notifications** — Why defer: Requires infrastructure outside CLI scope
- [ ] **Minor aspects for transits** — Why defer: Low signal-to-noise, not standard practice

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Current transit snapshot | HIGH | LOW | P1 |
| Transit-to-natal aspects | HIGH | MEDIUM | P1 |
| Secondary progressions | HIGH | MEDIUM | P1 |
| Progressed-to-natal aspects | HIGH | MEDIUM | P1 |
| Solar arc directions | HIGH | MEDIUM | P1 |
| Solar arc-to-natal aspects | HIGH | MEDIUM | P1 |
| Interpretation guide | HIGH | LOW | P1 |
| Configurable orbs | MEDIUM | LOW | P1 |
| House positions | HIGH | LOW | P1 |
| Retrograde status | MEDIUM | LOW | P1 |
| Aspect grid display | MEDIUM | LOW | P1 |
| Transit timeline (preset ranges) | MEDIUM | MEDIUM | P2 |
| Transit timeline (custom ranges) | MEDIUM | LOW | P2 |
| Retrograde station tracking | MEDIUM | MEDIUM | P2 |
| Progressed Moon tracking | MEDIUM | LOW | P2 |
| Applying/separating indicators | MEDIUM | LOW | P2 |
| Aspect exactness dates | HIGH | HIGH | P3 |
| Tri-wheel SVG | MEDIUM | MEDIUM | P3 |
| Element/modality shifts | LOW | LOW | P3 |
| Solar returns | MEDIUM | HIGH | Future |
| Lunar returns | LOW | MEDIUM | Future |
| Transit-to-progressed aspects | LOW | HIGH | Future |

**Priority key:**
- P1: Must have for v1.1 launch — core predictive functionality
- P2: Should have, add when possible — enhances usability
- P3: Nice to have, future consideration — polish features

## Transit Timeline Details

### Expected Date Range Options

Based on research into astrology software usage patterns:

| Range Preset | Duration | Use Case | Planetary Coverage |
|--------------|----------|----------|-------------------|
| **Week** | 7 days from current date | Fast-moving transits (Sun, Moon, Mercury, Venus, Mars) | Moon completes ~7°, Sun ~7°, quick aspects |
| **Month** | 30 days from current date | Standard short-term forecast | Moon through full cycle, inner planets make multiple aspects |
| **3 Months** | 90 days from current date | Quarter-year planning | Mercury retrograde cycles, Venus/Mars sign changes |
| **Year** | 365 days from current date | Annual forecast | Jupiter aspects, Saturn slow movement, outer planet long transits |
| **Custom** | User-specified start/end dates | Specific event planning, historical review | Any range, calculate all transiting aspects |

### Transit Speed Considerations

| Planet | Avg Daily Motion | Aspect Duration (3° orb) | Timeline Inclusion |
|--------|------------------|--------------------------|-------------------|
| Moon | 12-14° | ~6 hours | Optionally exclude (too fast) |
| Mercury | 1-2° | ~3 days | Include in week+ timelines |
| Venus | 0.8-1.2° | ~3-4 days | Include in week+ timelines |
| Sun | ~1° | ~3 days | Always include (backbone) |
| Mars | 0.5-0.8° | ~5-7 days | Include in week+ timelines |
| Jupiter | 0.08-0.2° | ~15-40 days | Month+ timelines |
| Saturn | 0.03-0.08° | ~40-100 days | 3-month+ timelines |
| Uranus | 0.01-0.02° | ~150-300 days | Year timelines |
| Neptune | 0.005-0.01° | ~300-600 days | Year+ timelines |
| Pluto | 0.003-0.008° | ~400-1000 days | Multi-year timelines |

**Recommendation:** For week/month timelines, focus on Sun through Mars. For 3-month+ timelines, include Jupiter and slower planets.

## Progression Calculation Details

### Secondary Progressions Formula

```
Progressed Date = Birth Date + (Current Age in Years * 1 Day)

Example:
  Birth Date: 1991-01-13
  Current Age: 35 years
  Progressed Date: 1991-01-13 + 35 days = 1991-02-17

Planetary positions on 1991-02-17 = Progressed chart for age 35
```

### Solar Arc Directions Formula

```
Solar Arc = Progressed Sun Position - Natal Sun Position

Apply Solar Arc to all planets/points:
  Solar Arc Sun = Natal Sun + Arc
  Solar Arc Moon = Natal Moon + Arc
  Solar Arc Ascendant = Natal Ascendant + Arc
  ... (all planets and angles)

Example:
  Natal Sun: 292.45° (22° Capricorn)
  Progressed Sun (35 days later): 327.28° (27° Aquarius)
  Solar Arc: 327.28° - 292.45° = 34.83°

  Solar Arc Moon = Natal Moon (261.61°) + 34.83° = 296.44° (26° Capricorn)
```

### Progressed vs Solar Arc Key Differences

| Aspect | Secondary Progressions | Solar Arc Directions |
|--------|------------------------|---------------------|
| Calculation | Each planet's actual position N days after birth | Natal position + Sun's arc applied uniformly |
| Planetary speeds | Different for each planet (Moon fast, outer planets slow) | All move at same rate (Sun's daily motion ~1°/year) |
| Aspect timing | Progressed Moon makes many aspects, outer planets barely move | All planets make aspect contacts at similar frequency |
| Orbs | 1° orb standard | 0.5-1° orb (tighter, more precise) |
| Interpretation focus | Internal psychological development, especially Moon | Major life events, external manifestations |
| House positions | Angles change slowly, progressed Moon changes houses every ~2 years | Angles move predictably, uniform progression |

## Data Output Format

### Expected JSON Structure Extensions

Building on existing `chart.json` structure from natal charts:

```json
{
  "meta": {
    "name": "Person Name",
    "birth_date": "1991-01-13",
    "birth_time": "07:00",
    "calculation_date": "2026-02-17T12:00:00+00:00",
    "calculation_type": "current_transits|secondary_progressions|solar_arc_directions",
    "target_age": 35,
    "house_system": "Placidus",
    "generated_at": "2026-02-17T18:30:00+00:00"
  },
  "planets": [
    {
      "name": "Sun",
      "sign": "Aqu",
      "degree": 28.12,
      "abs_position": 328.12,
      "house": "First_House",
      "retrograde": false,
      "speed": 1.01
    }
  ],
  "aspects_to_natal": [
    {
      "transiting_planet": "Jupiter",
      "natal_planet": "Sun",
      "aspect": "Trine",
      "orb": 1.2,
      "exact_date": "2026-02-20",
      "applying": true
    }
  ],
  "houses": [],
  "angles": [],
  "retrograde_stations": [
    {
      "planet": "Mercury",
      "station_type": "retrograde",
      "date": "2026-03-15",
      "degree": "15.2 Pisces"
    }
  ]
}
```

### Aspect Grid Display (Terminal Output)

```
TRANSITS TO NATAL ASPECTS (2026-02-17)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Transit Planet    Aspect    Natal Planet    Orb      Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
tr.Jupiter        Trine     ☉ Sun          1.2°     Applying
tr.Saturn         Square    ☽ Moon         0.8°     Exact!
tr.Uranus         Conjunct  ♀ Venus        2.5°     Separating
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Competitor Feature Analysis

| Feature | TimePassages (Desktop) | Astro-Seek (Web) | Our Approach |
|---------|------------------------|------------------|--------------|
| Current transits | Bi-wheel with natal, auto-updates | Transit chart calculator, manual date entry | Auto-load with chart profile, JSON + SVG output |
| Transit timeline | Graphical curves for 3/6/12 months | Calendar view, aspect list by date | Preset ranges (week/month/3mo/year) + custom, aspect list format |
| Secondary progressions | Tri-wheel (natal/prog/transit), full chart | Progressed chart calculator, separate from natal | Calculate for target date, aspect grid to natal, JSON output |
| Solar arc directions | Separate calculation, aspects to natal | Solar arc calculator, manual date | Calculate alongside progressions, same aspect detection logic |
| Aspect orbs | Configurable per aspect type | Fixed orbs (3° transits, 1° progressions) | Configurable via CLI args, sensible defaults (transit: 1-3°, prog: 1°, solar arc: 0.5-1°) |
| Retrograde tracking | Visual indicators on chart wheel | Separate retrograde calendar | Include in timeline, flag station dates |
| Interpretation | Point-and-click text for each aspect | Generic interpretations for aspects | Comprehensive markdown guide loaded into Claude's context — expert-level synthesis |
| House positions | All three chart types show houses | Transit/progression house positions | Calculate houses for transits/progressions using natal location |
| Chart export | PDF reports, print | PNG image download | JSON (structured data) + SVG (visual), optimized for Claude Code context loading |
| Progressed angles | Multiple calculation methods (Solar Arc, True Secondary) | Solar Arc only | Calculate ASC/MC via solar arc method, document limitation |

## Sources

**Transit Functionality:**
- [ASTROGRAPH - TimePassages](https://www.astrograph.com/astrology-software/)
- [Astro-Seek Transit Chart Calculator](https://horoscopes.astro-seek.com/transit-chart-planetary-transits)
- [Astrolada Personal Transit Calendar](https://www.astrolada.com/personal-transit-calendar/)
- [Planetary Transits & Aspects 2026](https://horoscopes.astro-seek.com/astrology-aspects-transits-online-calendar)

**Secondary Progressions:**
- [Cafe Astrology - Secondary Progressions](https://cafeastrology.com/secondaryprogressions.html)
- [Astro-Seek Secondary Progressions Calculator](https://horoscopes.astro-seek.com/astrology-secondary-progressions-directions-chart)
- [Kepler College - Introduction to Secondary Progressions](https://library.keplercollege.org/into-secondary-prog/)
- [Astrology University - How to Use Progressions](https://www.astrologyuniversity.com/how-to-use-progressions/)

**Solar Arc Directions:**
- [Astro-Seek Solar Arc Calculator](https://horoscopes.astro-seek.com/solar-arc-directions-calculator)
- [Alabe - What is Solar Arc](https://www.alabe.com/solararc.html)
- [Astro.com Wiki - Solar Arc](https://www.astro.com/astrowiki/en/Solar_Arc)
- [Two Wander - How To Use Solar Arcs](https://www.twowander.com/blog/how-to-use-solar-arcs-in-astrology)

**Orbs & Aspect Timing:**
- [Cafe Astrology - Progressed Moon Aspects](https://cafeastrology.com/progressedmoonaspects.html)
- [Astrology with Heather - 2026 Predictions](https://www.astrologywithheather.com/blog/2026-astrology-forecast-reality-shifting-transits-karmic-turning-points-a-new-era-unfolding)

**Retrograde & Stations:**
- [Astro-Seek Retrograde-Stationary Planets](https://horoscopes.astro-seek.com/retrograde-stationary-planets-transits-in-natal-chart-astrology)
- [Pandora Astrology - Planetary Retrogrades](https://pandoraastrology.com/transits-this-year/planetary-retrogrades-stations/)
- [Cafe Astrology - Retrograde Cycles 2024-2026](https://cafeastrology.com/retrogrades.html)

**Software Comparison:**
- [iPhemeris Features](https://iphemeris.com/)
- [TimePassages Advanced Edition](https://www.astrograph.com/astrology-software/advanced.php)
- [Astro Gold](https://www.astrogold.io/AG-MacOS-Help/grid.html)
- [LUNA Astrology Software](https://www.lunaastrology.com/)

**Predictive Techniques:**
- [Elsa Elsa - Transits vs Progressions vs Solar Returns](https://elsaelsa.com/astrology/what-is-the-difference-between-transits-progressions-the-solar-return/)
- [Cafe Astrology - Interpreting Solar Returns](https://cafeastrology.com/interpretingsolarreturns.html)

---
*Feature research for: Transit, Progression & Solar Arc Analysis*
*Researched: 2026-02-17*
*Confidence: HIGH — verified with authoritative astrology software sources, current documentation, and standard astrological practice*
