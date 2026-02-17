# Pitfalls Research: Adding Transits & Progressions

**Domain:** Extending natal chart tool with transits, secondary progressions, and solar arc directions
**Researched:** 2026-02-17
**Confidence:** MEDIUM

**Context:** Adding time-based predictive techniques to existing working natal chart system. Must preserve natal chart functionality while extending calculation engine to handle date ranges, progressed positions, and transit events.

---

## Critical Pitfalls

### Pitfall 1: Breaking Existing Natal Chart Functionality

**What goes wrong:**
Adding transit/progression modes introduces shared code paths (timezone conversion, Kerykeion initialization, JSON assembly) that can inadvertently break natal chart calculations. A seemingly harmless refactor to support "calculation date vs birth date" can introduce bugs in the natal chart path.

**Why it happens:**
The existing `astrology_calc.py` is ~1,070 LOC monolithic file. Adding new modes means touching shared functions (`valid_date`, `valid_time`, Julian day conversions, Kerykeion subject creation). Developers assume "I'm just adding new code" but shared utilities get modified, introducing regressions.

**How to avoid:**
- **NEVER modify existing natal chart code paths** — isolate transit/progression logic in separate functions
- Create separate argument parsing sections for each mode (`--transit`, `--progression`, `--solar-arc`) with exclusive validation
- Use separate JSON assembly functions (`build_natal_json`, `build_transit_json`, `build_progression_json`) even if they share some utilities
- **Critical:** Test natal chart mode after EVERY commit during integration phase
- Consider extracting shared utilities (timezone, date validation) into a separate `utils.py` only after transit mode is working

**Warning signs:**
- Natal chart tests start failing during transit development
- Natal chart output includes unexpected new fields
- Birth time/location validation rejects previously valid inputs
- Natal chart folder structure changes unintentionally

**Phase to address:**
Phase 1 (Current transits) — Establish integration pattern from the start. Create `test_natal_regression.py` that verifies existing functionality remains untouched.

---

### Pitfall 2: Timezone Confusion Across Multiple Dates

**What goes wrong:**
Natal charts use birth timezone (e.g., "1990-06-15 14:30 in New York EST"). Transits need "now" in the user's current timezone OR a specified query date. Secondary progressions need birth timezone for both birth date AND progressed date calculation. Mixing these timezones produces incorrect positions by hours.

**Why it happens:**
According to [Time Nomad's natal chart accuracy guide](https://timenomad.app/documentation/accurate-natal-birth-chart-calculator-software.html), discrepancies in transits are usually due to birth time/location issues, especially UTC time being manually edited incorrectly. When adding transit calculations to existing code, developers often:
1. Convert birth time to UTC once (correct for natal)
2. Convert transit query date to UTC separately (often using system timezone, NOT birth location timezone)
3. Mix UTC timestamps from different timezone contexts

The [Swiss Ephemeris documentation](https://www.astro.com/swisseph/swephprg.htm) warns about timezone conversion pitfalls explicitly.

**How to avoid:**
- **Store timezone context explicitly**: Track three separate timezone strings:
  - `birth_tz_str` — Birth location timezone (e.g., "America/New_York")
  - `query_tz_str` — Transit query timezone (defaults to `birth_tz_str` for consistency)
  - `user_current_tz` — Only for "now" transits (system timezone)
- **Always convert to UTC before Kerykeion**: Use `pytz` to localize datetime to specific timezone, then convert to UTC before passing to `swe.utc_to_jd()`
- For progressions: Birth date uses `birth_tz_str`, progressed date calculation uses `birth_tz_str` (not current location)
- Add `--query-tz` flag for transit mode (optional, defaults to birth location timezone)
- **Never mix timezone-aware and naive datetime objects** — always localize first

**Warning signs:**
- Transit positions differ by whole hours from expected values
- Progressed Moon position off by days/months
- DST transitions cause 1-hour calculation shifts
- Different results for same query on different user machines

**Phase to address:**
Phase 1 (Current transits) — Establish timezone handling pattern. Create explicit timezone context tracking before date range features add complexity.

---

### Pitfall 3: Date Range Performance Explosion

**What goes wrong:**
"Generate daily transits for the next year" means calculating planetary positions for 365+ dates. Naively looping `create_subject()` for each date can take 10+ seconds or timeout entirely. Users expect <2 second response for timeline queries.

**Why it happens:**
[Kerykeion's TransitsTimeRangeFactory](https://www.kerykeion.net/pydocs/kerykeion.html) provides date range transit calculations, but developers unfamiliar with it create loops like:

```python
for date in date_range:
    subject = AstrologicalSubjectFactory.from_birth_data(...)  # Full chart every iteration
    transits = NatalAspects(natal, subject)  # Aspect search every iteration
```

Each iteration:
- Initializes Swiss Ephemeris
- Calculates 10 planetary positions + houses + angles
- Searches all aspect combinations (10 natal × 10 transit = 100 checks)

For 365 days × 100+ calculations = 36,500+ ephemeris calls.

**How to avoid:**
- **Use Kerykeion's `TransitsTimeRangeFactory`** — designed for date range efficiency
- For daily snapshots (not aspect events): Pre-calculate only required points using `active_points` parameter
- **Limit date ranges**: 1 year max for daily transits, 30 days for hourly
- For progressed charts: Single snapshot calculation (not ranges) — progressed positions change slowly
- Consider optional snapshot caching: Store JSON for common queries ("today's transits") with 1-day TTL
- **Don't calculate houses for every transit snapshot** — transiting planets' ecliptic positions don't need house system calculations unless specifically requested

**Warning signs:**
- CLI takes >5 seconds for 30-day transit range
- Memory usage grows linearly with date range
- Users request "next 5 years" and script hangs
- CPU spikes during date range calculations

**Phase to address:**
Phase 2 (Transit timelines) — Implement date range mode AFTER current transits work correctly. Benchmark single-date performance first, then optimize range calculations.

---

### Pitfall 4: Ephemeris Accuracy Limits for Historical/Future Dates

**What goes wrong:**
Users request progressed chart for someone born in 1850, or transits for 2100. Swiss Ephemeris accuracy degrades outside tested ranges. Calculations may fail silently, return inaccurate positions, or throw exceptions.

**Why it happens:**
According to the [ephemeris accuracy discussion on The Astrology Podcast](https://theastrologypodcast.com/transcripts/ep-304-transcript-how-to-read-an-ephemeris/), ephemeris makers warn if you're going "a certain distance out that it could start to become unreliable." While JPL DE431 covers 13,000 BC to 17,000 AD, pyswisseph's practical reliable range is narrower.

From [Wikipedia's ephemeris article](https://en.wikipedia.org/wiki/Ephemeris), gravitational perturbations from asteroids with poorly known masses cause prediction drift over very long periods. For astrology software, reliability is "pretty solid for relatively close distances within a century or a few centuries."

**How to avoid:**
- **Define supported date ranges explicitly**:
  - Birth dates: 1800–present (current `valid_date()` already enforces this)
  - Transit query dates: 1900–2100 (reasonable human lifespan coverage)
  - Progression calculations: Birth date + 120 years max (accounts for centenarians)
- Add `valid_query_date()` separate from `valid_date()` with different range
- Return clear error messages: "Ephemeris data unreliable for dates before 1900" NOT "Calculation failed"
- For edge case dates (1800-1900), add warning flag in JSON: `"ephemeris_reliability": "reduced"`
- Document supported ranges in CLI `--help` text

**Warning signs:**
- Swiss Ephemeris returns error codes for distant dates
- Calculated positions seem implausible (planet at 400° longitude)
- Different astrology software gives wildly different results for same distant date
- Silent failures for historical dates

**Phase to address:**
Phase 1 (Current transits) — Extend date validation to cover query dates, not just birth dates. Better to fail fast with clear error than produce unreliable calculations.

---

### Pitfall 5: Secondary Progressions Retrograde Station Math Errors

**What goes wrong:**
When a planet stations retrograde or direct within the first 80 days of life, the progressed position calculation becomes complex. Mercury retrogrades 3 times/year — many people have progressed Mercury changing direction. Incorrect station handling produces positions off by several degrees.

**Why it happens:**
Day-for-a-year progression is straightforward when planets move steadily: Birth + 30 days = Age 30 chart. But stations introduce directional changes:

From [The Astrology Podcast on planetary stations](https://theastrologypodcast.com/2022/03/11/planetary-stations-in-secondary-progressions/):
- Mercury stations last ~24 progressed years (retrograde period)
- Venus retrograde lasts 42 progressed years
- Mars retrograde lasts 80 progressed years

According to [My Sky Pie's retrograde direction article](https://my-sky-pie.com/when-a-secondary-progressed-planet-changes-direction/), "for secondary progression, retrograde motion means that progressing a planet forward one day in time leads to the planet's moving 'backwards' in the chart."

Developers often implement simple addition:
```python
progressed_long = natal_long + (age_years * daily_motion)  # WRONG for retrograde
```

This fails when the planet stations between birth and progressed date.

**How to avoid:**
- **Use Kerykeion's progression calculations directly** — don't implement day-for-a-year math manually
- Kerykeion creates a progressed subject with date offset — handles retrograde internally
- If manual calculation needed: Check ephemeris data for EACH day between birth and progressed date to detect stations
- Include retrograde status in progressed planet output: `"progressed_mercury": {"position": "15°20' Gemini", "retrograde": true}`
- For progressed Moon (moves 12-14°/day = 11-14°/year progressed): Calculate monthly positions for precision

**Warning signs:**
- Progressed Mercury position doesn't match astrology software
- Progressed planet suddenly jumps backward in timeline view
- Retrograde status missing from progressed planet data
- Progressed positions off by 5-10 degrees for known charts

**Phase to address:**
Phase 3 (Secondary progressions) — Test with known birth dates that include planetary stations in first 80 days. Verify against established astrology software.

---

### Pitfall 6: Solar Arc True vs Mean Arc Confusion

**What goes wrong:**
Solar arc directions move every chart point by the distance the progressed Sun has traveled. The Sun moves ~0.9856°/day (mean), but actual daily motion varies slightly. Using mean arc for everyone produces positions off by ~1° after 90 years. Users comparing with other software notice discrepancies.

**Why it happens:**
From [Astrodienst's Solar Arc article](https://www.astro.com/astrowiki/en/Solar_Arc), "it is possible to use either the actual distance travelled by the Sun on any particular day (the true solar arc) or to use an average value using the Naibod key."

According to [Astrotheme's solar arc calculator](https://www.astrotheme.com/astrological_solar_arcs_directions.php), "the sun makes only 0.9856 degrees per day on average, so the true solar arc for 90 years progression should be 88.706 degrees rather than exactly 90 degrees."

Developers assume "1 degree per year" for simplicity, or use mean solar motion without understanding the difference. Professional astrology software offers both methods, leading to version conflicts.

**How to avoid:**
- **Use TRUE solar arc by default** (actual Sun progression, more accurate)
- Calculate: `solar_arc = progressed_sun_longitude - natal_sun_longitude`
- Apply same arc to ALL chart points (planets, angles, house cusps)
- Add CLI flag `--solar-arc-method {true|mean}` for compatibility with other software
- Document which method is used in JSON output: `"solar_arc_method": "true"`
- Include Naibod key calculation as alternative (0.9856°/year exactly)

**Warning signs:**
- Solar arc positions differ by 1-2° from other software after 40+ years
- Users report "incorrect" solar arc calculations for elderly clients
- Different software versions give different results
- Confusion about which method is "standard"

**Phase to address:**
Phase 4 (Solar arc directions) — Implement true solar arc first, add mean arc as option only if users request it for compatibility.

---

### Pitfall 7: Progressed Moon Sub-Monthly Precision

**What goes wrong:**
Progressed Moon moves 12-14°/day in ephemeris = 12-14°/year in progressions. At 1°/month progressed, the Moon changes sign every 2.5 months. Reporting only yearly snapshots misses critical progressed Moon phase changes that astrologers use for monthly timing.

**Why it happens:**
From [Cafe Astrology's secondary progressions guide](https://cafeastrology.com/secondaryprogressions.html): "The moon moves between 11 and 14 degrees a day, which translates to between 55 and 70 minutes motion per progressed month."

Developers implement progressions for slow planets (Sun, Mercury, Venus) where yearly snapshots suffice, then apply the same structure to the Moon. But astrologers specifically use progressed Moon for **monthly** timing:

"Since the moon moves so quickly, it is worth calculating its monthly progressed position to look for the aspects the moon makes and time events to within around a month."

Missing monthly Moon positions makes progressions less useful for practical prediction work.

**How to avoid:**
- For progressed Moon specifically: Offer monthly precision option
- CLI flag: `--progressed-moon-monthly` calculates 12 monthly snapshots per year for progressed Moon only
- Include progressed Moon phase in output (relationship to progressed Sun)
- Calculate progressed lunar return dates (when progressed Moon returns to natal Moon position ~27-28 years)
- For other progressed planets: Yearly snapshots sufficient (they move slowly in progressions)

**Warning signs:**
- Astrologers complain progressed Moon data is "too coarse"
- Users manually calculate monthly progressions outside the tool
- Progressed Moon aspects missed between yearly snapshots
- Feedback: "Other software shows monthly progressed Moon"

**Phase to address:**
Phase 3 (Secondary progressions) — Implement monthly progressed Moon precision from the start, even if other planets use yearly snapshots. This is a domain-specific requirement.

---

### Pitfall 8: Monolithic File Becomes Unmaintainable

**What goes wrong:**
Current `astrology_calc.py` is ~1,070 LOC. Adding transits (~300 LOC), progressions (~400 LOC), and solar arc (~200 LOC) pushes it to ~2,000+ LOC. Single file becomes difficult to navigate, test, and debug. New features take longer to add, bugs harder to isolate.

**Why it happens:**
According to [Real Python's refactoring guide](https://realpython.com/python-refactoring/), "distinct blocks of code that seem separated by some kind of logic can indicate a routine that can be extracted into a function or its own class."

For existing monolithic files, developers resist refactoring because "it works now, why risk breaking it?" But each new feature added without restructuring increases technical debt. Eventually a single bug fix requires understanding 2000 lines of context.

**How to avoid:**
- **Don't refactor until transit mode works** — premature extraction introduces bugs
- After Phase 2 (transit timelines work correctly):
  1. Extract shared utilities: `utils/date_validation.py`, `utils/timezone.py`, `utils/dignities.py`
  2. Create calculation modules: `calculations/natal.py`, `calculations/transits.py`, `calculations/progressions.py`
  3. Keep `astrology_calc.py` as thin CLI orchestrator (argument parsing + mode routing)
- Use modern IDE refactoring tools (PyCharm "Extract Method") to automate safely
- **Critical:** Run full test suite after each extraction to catch regressions
- Group by domain coupling (all dignity code together) not by technical type

**Warning signs:**
- Scrolling >500 lines to find relevant function
- Copy-paste code between modes (DRY violation)
- Bug fixes require changes in 3+ places
- New features take disproportionately long to implement
- Difficulty writing focused unit tests

**Phase to address:**
Between Phase 2 and Phase 3 — Refactor after transit features work, before adding progressions. This creates clean structure for remaining features.

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Reuse natal chart JSON structure for transits by adding fields | Faster implementation, no new schema design | JSON becomes bloated, unclear which fields apply to which mode, harder to document | Never — separate schemas |
| Calculate transits in local time instead of UTC | Avoids timezone conversion complexity | Incorrect calculations across DST boundaries, impossible to debug timezone issues | Never — always use UTC internally |
| Store progressed chart without birth date reference | Smaller JSON file | Can't verify progression calculation, can't recalculate if method changes | Never — always link to source natal chart |
| Use mean solar arc (1°/year) instead of true arc | Simpler calculation, "close enough" for most ages | Accumulates error, professional astrologers notice discrepancies | Only if user explicitly requests mean method |
| Skip monthly progressed Moon calculation | Simpler implementation, faster calculation | Misses primary use case for progressions (monthly timing) | Never — monthly Moon is core feature |
| Hard-code date range limits (no validation) | Faster coding, assumes reasonable users | Silent failures for edge cases, user confusion | Never — always validate with clear errors |
| Combine all calculation modes in single function | Less code duplication initially | Impossible to test modes independently, shared bugs affect all modes | Never — isolate mode logic |

---

## Integration Gotchas

Common mistakes when connecting to Kerykeion for new calculation types.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Kerykeion subject creation for transits | Creating both natal and transit subjects with `online=True`, hitting GeoNames twice | Natal subject with `online=True` (lookup birth location), transit subject with `online=False` + reuse natal coordinates |
| TransitsTimeRangeFactory usage | Passing date range as string dates | Convert to datetime objects first, use timezone-aware datetimes, convert to UTC before passing |
| Progressed chart calculation | Creating subject with progressed date only | Must create natal subject first, then progressed subject referencing natal date + progression offset |
| Solar arc chart | Manually adding 1°/year to each position | Use Kerykeion's progression API with solar arc mode, let it handle retrograde/station edge cases |
| Aspect calculation for transits | Recalculating natal aspects every time | Calculate natal aspects once, reuse natal chart, only calculate transit-to-natal aspects |
| House system for progressed chart | Using Placidus for all calculations | Progressions traditionally use progressed Ascendant with natal houses OR equal house from progressed ASC — document choice |

---

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Calculating full chart for every date in range | Linear slowdown with range size, >5 sec for 1 year | Use `active_points` to limit calculations to required planets only | 100+ dates (3+ months daily) |
| Re-initializing Swiss Ephemeris per calculation | Noticeable startup delay per call | Initialize once, reuse connection across date range | 50+ sequential calculations |
| Storing daily transit snapshots as separate JSON files | Disk I/O bottleneck, slow listing | Single JSON with array of snapshots, or SQLite for range queries | 1000+ snapshots (2+ years daily) |
| Calculating house cusps for transit positions | Unnecessary computation (transits are ecliptic positions) | Skip house calculations unless user requests transit house positions | Every transit calculation (wasteful but not breaking) |
| Loading entire progressed timeline on chart load | Context window overflow, slow response | Load current progressed chart only, offer timeline as separate query | Multi-year progressed ranges |

---

## UX Pitfalls

Common user experience mistakes in this domain.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Not showing which timezone transit calculations use | User confusion: "Are these transits for my location or birth location?" | Output includes: `"timezone": "America/New_York (birth location)"` clearly labeled |
| Reporting progressed positions without natal reference | Can't interpret meaning without comparison | Always show: `"natal_sun": "15° Leo"`, `"progressed_sun": "22° Leo"` side by side |
| Using technical terminology without context | "Solar arc using Naibod key" means nothing to learners | Include brief explanation: `"method": "true_solar_arc"`, `"description": "Based on actual Sun movement"` |
| No indication of calculation freshness | Stale transit data misleads users | Include `"calculated_at": "2026-02-17T14:30:00Z"` timestamp in JSON |
| Identical output format for different calculation types | User can't distinguish transit from progression | Use clear mode indicator: `"chart_type": "secondary_progression"`, `"chart_type": "current_transits"` |
| Missing ephemeris accuracy warnings for edge dates | Users assume all dates equally reliable | Flag when query date is near supported range limits: `"reliability": "reduced (near ephemeris limit)"` |

---

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **Transit calculations:** Often missing retrograde status for transiting planets — verify each planet includes `"retrograde": true/false`
- [ ] **Date range output:** Often missing timezone context for each snapshot — verify every timestamp includes explicit timezone
- [ ] **Progressed Moon:** Often missing monthly precision — verify option for sub-yearly calculation exists
- [ ] **Solar arc:** Often missing method documentation — verify JSON includes `"solar_arc_method"` field
- [ ] **Timezone handling:** Often assumes user is in birth location — verify `--query-tz` flag works independently
- [ ] **Aspect calculations:** Often missing applying/separating distinction for transits — verify aspect metadata includes `"applying": true/false`
- [ ] **Progressed planets:** Often missing station events — verify retrograde/direct station dates calculated for Mercury/Venus/Mars
- [ ] **Error messages:** Often generic "failed" instead of specific — verify timezone errors, date range errors, ephemeris errors all have distinct messages

---

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Broke natal chart functionality during integration | HIGH | Revert to last working commit, create regression tests, re-implement transit mode in isolation |
| Mixed timezones produced incorrect transit positions | MEDIUM | Add explicit timezone logging, trace each datetime conversion, add timezone validation tests |
| Date range performance is too slow | MEDIUM | Profile to find bottleneck, implement `active_points` optimization, add date range limits |
| Progressed positions don't match other software | MEDIUM | Verify Kerykeion progression API version, test with known birth dates, check station handling |
| Monolithic file too large to maintain | HIGH | Extract incrementally starting with utilities, test after each extraction, don't rush |
| Ephemeris failures for historical dates | LOW | Add date range validation earlier in pipeline, return clear error before calculation attempt |
| Missing monthly progressed Moon | LOW | Add monthly calculation as separate function, integrate into existing progression mode |
| Solar arc method confusion | LOW | Add method flag and documentation, default to true arc, allow mean arc as option |

---

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Breaking natal chart functionality | Phase 1 (Current transits) | Regression test suite passes after every commit |
| Timezone confusion across multiple dates | Phase 1 (Current transits) | Test with birth in EST, query in PST, verify positions match UTC calculation |
| Date range performance explosion | Phase 2 (Transit timelines) | 1-year daily range completes in <3 seconds |
| Ephemeris accuracy limits | Phase 1 (Current transits) | Date validation rejects <1900 and >2100 with clear error |
| Secondary progressions retrograde station math | Phase 3 (Secondary progressions) | Compare with known progressed Mercury retrograde examples from astrology references |
| Solar arc true vs mean confusion | Phase 4 (Solar arc directions) | Test 40-year arc, verify true arc differs from mean arc by expected amount |
| Progressed Moon sub-monthly precision | Phase 3 (Secondary progressions) | Verify monthly Moon option produces 12 snapshots/year |
| Monolithic file becomes unmaintainable | Between Phase 2 and 3 | File structure has separate modules for natal/transits/progressions |

---

## Sources

**Kerykeion & Swiss Ephemeris:**
- [Kerykeion Transit Chart Examples](https://www.kerykeion.net/content/examples/transit-chart) — Transit calculation API
- [Kerykeion API Documentation](https://www.kerykeion.net/pydocs/kerykeion.html) — TransitsTimeRangeFactory reference
- [PySwisseph GitHub Repository](https://github.com/astrorigin/pyswisseph) — Python Swiss Ephemeris wrapper
- [Swiss Ephemeris Programming Interface](https://www.astro.com/swisseph/swephprg.htm) — Official documentation, timezone warnings

**Timezone & Date Handling:**
- [Time Nomad: Accurate Natal Chart Calculator](https://timenomad.app/documentation/accurate-natal-birth-chart-calculator-software.html) — Timezone conversion pitfalls
- [Cafe Astrology: Historical Time Zones](https://cafeastrology.com/historical-time-zones.html) — DST and timezone law changes
- [Section 7: Date and Time Conversion Functions in swephR](https://rdrr.io/cran/swephR/man/Section7.html) — Swiss Ephemeris timezone functions

**Secondary Progressions:**
- [Cafe Astrology: Secondary Progressions](https://cafeastrology.com/secondaryprogressions.html) — Day-for-a-year method, progressed Moon precision
- [The Astrology Podcast: Planetary Stations in Secondary Progressions](https://theastrologypodcast.com/2022/03/11/planetary-stations-in-secondary-progressions/) — Retrograde duration, station handling
- [My Sky Pie: When a Secondary Progressed Planet Changes Direction](https://my-sky-pie.com/when-a-secondary-progressed-planet-changes-direction/) — Retrograde motion in progressions
- [Charlie Obert: Secondary Progressions Guide (PDF)](https://studentofastrology.com/wp-content/uploads/2014/04/Secondary_Progressions_Guide.pdf) — Comprehensive guide to progression calculations

**Solar Arc Directions:**
- [Astrodienst: Solar Arc](https://www.astro.com/astrowiki/en/Solar_Arc) — True vs mean solar arc
- [Astrotheme: Solar Arcs Directions](https://www.astrotheme.com/astrological_solar_arcs_directions.php) — Calculation accuracy (88.706° for 90 years)
- [Astrology School: Solar Arc Directions](https://astrologyschool.net/solar-arc-directions/) — Birth time accuracy requirements

**Ephemeris Accuracy:**
- [The Astrology Podcast: How to Read an Ephemeris (Transcript)](https://theastrologypodcast.com/transcripts/ep-304-transcript-how-to-read-an-ephemeris/) — Ephemeris reliability over time
- [Wikipedia: Ephemeris](https://en.wikipedia.org/wiki/Ephemeris) — Gravitational perturbations, long-term accuracy limits

**Code Architecture:**
- [Real Python: Refactoring Python Applications](https://realpython.com/python-refactoring/) — When to extract functions from monolithic files
- [Medium: Refactoring Monolithic Code Structures](https://sdremthix.medium.com/a-high-level-overview-to-refactoring-monolithic-code-structures-2d5b70a79570) — Identifying extraction candidates

---

*Pitfalls research for: Adding transits, progressions, and solar arc directions to generate-natal-chart*
*Researched: 2026-02-17*
*Focus: Integration risks, timezone handling, calculation accuracy, performance optimization for date ranges*
