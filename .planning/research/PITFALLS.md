# Pitfalls Research: generate-natal-chart

## Critical Pitfalls

### 1. Timezone Handling for Birth Times

**Description:** Birth time must be interpreted in the timezone of the birth location, not the user's current timezone. A birth at "14:30 in New York" means EST/EDT, not UTC. Getting this wrong shifts every house cusp and angle.

**Warning Signs:** Ascendant/MC don't match expected values for known charts. House cusps off by whole signs.

**Prevention:** Kerykeion handles timezone resolution internally via GeoNames timezone data. Ensure the location is passed correctly — don't pre-convert times to UTC. Pass local birth time + location and let Kerykeion resolve.

**Phase:** Core Python backend (Phase 1)

---

### 2. Kerykeion API Version Differences

**Description:** Kerykeion's API has changed significantly between v3 and v4. Property names, class structures, and method signatures differ. Code written for one version may break on another.

**Warning Signs:** AttributeError on Kerykeion objects. Missing properties. Unexpected data types.

**Prevention:** Pin Kerykeion version in requirements. Test with pinned version. Document which API surface the script uses. Check Kerykeion changelog before upgrading.

**Phase:** Core Python backend (Phase 1)

---

### 3. GeoNames Lookup Failures

**Description:** Kerykeion uses GeoNames for geocoding. Ambiguous city names (e.g., "Springfield" — 30+ cities), non-English names, or GeoNames service issues can cause lookup failures or wrong coordinates.

**Warning Signs:** Script hangs on location lookup. Wrong city selected silently. Network errors.

**Prevention:** The Python script should handle GeoNames errors gracefully — clear error messages. For ambiguous locations, show the resolved city/country so the user can verify. Consider accepting "City, State/Country" format for disambiguation.

**Phase:** Core Python backend (Phase 1)

---

### 4. Context Window Overflow with Maximum Data

**Description:** "Everything possible" JSON could be very large. Planets (10) + asteroids (6+) + houses (12) + aspects (50+) + fixed stars (20+) + Arabic parts + dignities + element distributions could produce a JSON file that consumes significant context window space.

**Warning Signs:** Chart loading leaves little room for conversation. Claude's responses truncated or degraded.

**Prevention:** Structure JSON efficiently — no redundant data. Estimate token count of a full chart JSON. If over ~4000 tokens, consider a "summary" vs "full" loading option. Test with a real chart to measure actual size.

**Phase:** JSON schema design (Phase 2)

---

### 5. Argument Parsing Edge Cases

**Description:** Names with spaces ("John Doe"), locations with commas ("Portland, OR"), times in different formats ("2:30 PM" vs "14:30"), dates in different formats. The skill needs to handle these reliably.

**Warning Signs:** Arguments misinterpreted. Location split incorrectly. Name slugification produces unexpected results.

**Prevention:** Define strict input format in the skill prompt (ISO date, 24h time, quoted location). Use the skill's prompt to instruct Claude on how to parse and validate before passing to Python. The Python script should also validate inputs.

**Phase:** Claude Code skill layer (Phase 3)

---

### 6. Cross-Platform File Paths

**Description:** `~/.natal-charts/` expands differently on Windows vs Mac/Linux. Python's `pathlib.Path.home()` handles this, but the Claude Code skill's bash commands need to work too.

**Warning Signs:** File not found errors on Windows. Wrong directory created. Tilde not expanded.

**Prevention:** Use `pathlib.Path.home() / ".natal-charts"` in Python. In the skill .md, use `$HOME/.natal-charts/` (bash expands `$HOME`). Test on Windows specifically since that's the current platform.

**Phase:** Storage layer (Phase 1-2)

---

### 7. Fixed Stars / Arabic Parts Data Availability

**Description:** Kerykeion may not support all requested data points natively. Fixed star conjunctions and Arabic parts may require additional calculation beyond Kerykeion's core API.

**Warning Signs:** ImportError or AttributeError when accessing extended features. Empty data sections in JSON.

**Prevention:** Audit Kerykeion's actual API surface for fixed stars and Arabic parts before designing the JSON schema. If Kerykeion doesn't support them, implement manual calculations (Part of Fortune = ASC + Moon - Sun) or document as "not available" rather than failing silently.

**Phase:** Extended calculations (Phase 4)

---

### 8. Profile Name Collisions

**Description:** Two people with the same name ("John Smith") would map to the same folder. The skill warns before overwrite, but users might not realize it's a different person.

**Warning Signs:** Overwrite warning when creating chart for a different person with same name.

**Prevention:** Slugified folder name + birth date could create unique-enough identifiers. Or: slug from name only, but store birth details in metadata so the overwrite warning can show "This will replace John Smith (born 1990-03-15) — proceed?" for clear disambiguation.

**Phase:** Storage layer (Phase 2)

---

### 9. Astrologer Guide Prompt Quality

**Description:** The guide prompt is the most critical differentiator. A poor prompt means Claude gives generic horoscope-level responses instead of chart-specific interpretations. Too short = shallow. Too long = context waste.

**Warning Signs:** Claude gives generic astrological responses ignoring chart data. Claude misinterprets aspect meanings. Claude doesn't reference specific positions.

**Prevention:** The guide prompt should: (1) define key terminology, (2) explain how to read each JSON section, (3) provide interpretation frameworks (planet-sign-house synthesis), (4) include examples of good vs bad interpretations. Test with real charts and iterate.

**Phase:** Guide prompt authoring (Phase 4)

## Risk Matrix

| Pitfall | Likelihood | Impact | Priority |
|---------|-----------|--------|----------|
| Timezone handling | Medium | High | Critical |
| Kerykeion API changes | Medium | High | Critical |
| GeoNames failures | Medium | Medium | High |
| Context window overflow | Low | High | High |
| Argument parsing | Medium | Medium | Medium |
| Cross-platform paths | Medium | Medium | Medium |
| Fixed stars availability | High | Low | Medium |
| Name collisions | Low | Low | Low |
| Guide prompt quality | Medium | High | Critical |

## Prevention Checklist

- [ ] Pin Kerykeion version in requirements
- [ ] Test timezone handling with known chart (verify ASC/MC match)
- [ ] Handle GeoNames errors with clear messages
- [ ] Measure JSON token count for full chart
- [ ] Define strict input format in skill prompt
- [ ] Use pathlib for all file operations
- [ ] Audit Kerykeion API for fixed stars + Arabic parts support
- [ ] Include birth details in overwrite warning
- [ ] Test guide prompt with real chart data against Claude
- [ ] Test on Windows (current dev platform)
