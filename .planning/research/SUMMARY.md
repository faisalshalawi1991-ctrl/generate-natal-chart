# Project Research Summary

**Project:** generate-natal-chart
**Domain:** Astrological calculation & interpretation tool
**Researched:** 2026-02-16
**Confidence:** HIGH

## Executive Summary

The generate-natal-chart project is a Claude Code skill that generates full natal charts from birth data and injects the structured calculation results into Claude's context for astrological interpretation. The recommended approach uses Python with Kerykeion (the only actively maintained Python astrology library) for all calculations, stores chart profiles locally in `~/.natal-charts/`, and couples calculated data with an expert-authored interpretation prompt to enable Claude to provide specific, data-driven astrological analysis rather than generic readings.

This is a moderate-complexity integration project with well-defined boundaries: the Python backend handles all calculations and storage, the Claude Code skill layer handles user interaction and context routing, and the astrologer guide prompt is the critical differentiator that transforms raw data into interpretable context. The main risks are Kerykeion API surface changes between versions, timezone handling precision, and ensuring the interpretation prompt is sufficiently detailed to avoid generic output.

The build order should prioritize the Python backend first (foundation for all other work), followed by JSON schema design and SVG output, then the skill layer, and finally extended calculations and prompt refinement. This sequence ensures the skill interface is built on solid foundations and the interpretation prompt can be refined independently once data structures stabilize.

## Key Findings

### Recommended Stack

**Core:** Python 3.10+ with Kerykeion 4.x is the only viable path. Kerykeion is the sole actively maintained Python astrology library with built-in SVG generation, comprehensive planetary calculations, asteroid support, and GeoNames geocoding. No alternatives exist that provide equivalent functionality — Flatlib is unmaintained, Astropy is for astronomy not astrology, and raw Swiss Ephemeris bindings would require extensive custom work.

**Supporting technologies are all stdlib or minimal dependencies:** pathlib for cross-platform file handling, argparse for CLI parsing, json for serialization, and python-slugify for name normalization. The skill layer is pure Markdown with embedded bash commands and Read/Write tool calls. No external databases, APIs, or complex frameworks are needed.

**Critical consideration:** Kerykeion's API has changed between v3 and v4. The script must pin the version in requirements and document which API surface it targets. This is listed as a Critical pitfall.

### Expected Features

**Table stakes (must have):** All core astrological calculations that users expect from any chart tool — planetary positions, house cusps, major aspects, angles, birth data validation, SVG visualization, and JSON export. These are all directly provided by Kerykeion with minimal custom work.

**Differentiators (competitive):** The skill's main value comes from three integrated features: (1) loading full chart JSON directly into Claude context for deep interpretation, (2) an expert-authored astrologer guide prompt that teaches Claude how to read the data astrologically, (3) smart routing in a single command (create/list/load flows based on arguments). Extended data (asteroids, fixed stars, Arabic parts, dignities) adds interpretive depth but is not essential for v1.

**Defer to v2:** Synastry (multi-chart comparison), transit charts, progression charts, custom SVG styling, and chart comparison overlays. These all require significant additional complexity and are outside the "single natal chart + context loading" scope.

**Feature dependency chain:** Everything flows from birth data validation through geocoding to Kerykeion calculation, then diverges into JSON structure design and SVG generation before context loading and interpretation. This dependency sequence directly informs build order.

### Architecture Approach

The system is a clean three-tier composition: (1) Claude Code skill layer that handles routing and context injection, (2) Python backend that does all calculations and file I/O, (3) local filesystem storage for profiles. The skill invokes Python via bash, Python writes JSON/SVG files, and the skill reads those files back in for context injection.

**Major components:**
1. **Claude Code skill** — Parses user arguments, invokes Python, reads JSON, injects astrologer guide + data into context
2. **Python backend** — Kerykeion integration, data extraction, JSON/SVG generation, profile management
3. **Storage layer** — `~/.natal-charts/` directory structure with per-person subfolders containing chart.json and chart.svg
4. **Context injection layer** — Astrologer guide prompt (separate, iterable) + raw JSON presented together to Claude

**Key architectural decisions:** Single Python script (not a package) for simpler deployment, single skill with smart routing (user requested), custom nested JSON schema (organized by domain for Claude readability), guide prompt as separate file (easier iteration).

**Build sequence matters:** Python backend first (foundation), then JSON schema + SVG, then skill layer, then guide prompt refinement. This ensures the skill interface is built on stable foundations and the prompt can be tuned independently.

### Critical Pitfalls

1. **Timezone handling for birth times** — Birth time must be interpreted in the timezone of the birth location, not UTC or user's current timezone. Kerykeion handles this internally via GeoNames, but passing the location correctly is critical. Wrong timezone shifts every house cusp and angle. *Prevention:* Pass local birth time + location; let Kerykeion resolve timezone.

2. **Kerykeion API version differences** — Property names, class structures, method signatures changed significantly between v3 and v4. Code written for one version breaks on another. *Prevention:* Pin version in requirements, document API surface, check changelog before upgrading.

3. **GeoNames lookup failures** — Ambiguous city names ("Springfield" has 30+ matches), non-English names, or service issues cause failures or wrong coordinates. *Prevention:* Handle errors gracefully with clear messages, show resolved city/country for user verification, support "City, State/Country" disambiguation format.

4. **Context window overflow with maximum data** — Full JSON (planets, asteroids, houses, aspects, fixed stars, Arabic parts, dignities, element distributions) could consume significant context window. *Prevention:* Structure JSON efficiently, estimate token count (if over ~4000 tokens, consider "summary" vs "full" loading modes).

5. **Argument parsing edge cases** — Names with spaces, locations with commas, time format variations, date format variations. *Prevention:* Define strict input format in skill prompt (ISO date, 24h time, quoted location), validate in both skill and Python script.

6. **Astrologer guide prompt quality** — Poor prompt = generic horoscope responses instead of chart-specific interpretation. Too short = shallow, too long = context waste. *Prevention:* Prompt should define terminology, explain JSON sections, provide interpretation frameworks with examples. Test with real charts and iterate.

## Implications for Roadmap

Based on the dependency chain, architecture components, and pitfall matrix, the project naturally structures into 4 focused phases:

### Phase 1: Python Backend Core
**Rationale:** Foundation for all other work. Cannot write the skill or design JSON schema until the backend interface is defined.
**Delivers:** Working Python script that invokes Kerykeion, extracts data, validates input, writes to filesystem, provides CLI interface.
**Implements:**
- Kerykeion integration with AstrologicalSubject
- CLI argument parsing (name, date, time, location)
- Birth data validation
- GeoNames geocoding with error handling
- Profile directory structure creation

**Addresses features:** Accurate planetary positions, house calculations, aspects, angles, birth data validation, geocoding.
**Avoids pitfalls:** Timezone handling (delegate to Kerykeion), Kerykeion API versioning (pin version, test with known chart), GeoNames failures (handle errors gracefully), cross-platform paths (use pathlib).
**Research flag:** HIGH — Requires testing with Kerykeion to verify exact API surface and version behavior. Test timezone handling with known chart (verify ASC/MC match expected values).

### Phase 2: Storage & JSON Schema Design
**Rationale:** Once the Python backend can calculate, design the data structure before implementing SVG output. JSON schema affects everything downstream (context loading, guide prompt, performance).
**Delivers:** Comprehensive JSON schema that organizes all astrological data by domain (planets, houses, aspects, asteroids, etc.), efficient and Claude-readable. Storage layer fully functional with profile listing.
**Implements:**
- Nested JSON schema organization
- All core data exports from Kerykeion
- Profile listing and lookup
- Overwrite protection with metadata
- Token count estimation (warn if >4000)

**Addresses features:** JSON data export, profile storage, profile listing, SVG visual (via Kerykeion).
**Avoids pitfalls:** Context window overflow (estimate token count, design efficiently), profile name collisions (include birth date in overwrite warning).
**Research flag:** MEDIUM — JSON schema design benefits from astrological domain knowledge. Estimate token counts with real charts. Verify which Kerykeion data fields are reliably available.

### Phase 3: Claude Code Skill Layer
**Rationale:** Once Python backend and storage are stable, build the skill wrapper and routing logic.
**Delivers:** Working Claude Code skill in `~/.claude/` that handles create/list/load flows, invokes Python via bash, reads JSON, manages overwrite confirmation.
**Implements:**
- Skill definition (.md file) with argument routing
- Bash invocation of Python backend
- File reading with Read tool
- Three distinct flows (create, list, load)
- Overwrite confirmation UX

**Addresses features:** Smart routing, profile storage, profile listing, overwrite protection.
**Avoids pitfalls:** Argument parsing edge cases (define strict format in prompt, validate before passing to Python), cross-platform paths (use $HOME expansion in bash).
**Research flag:** LOW — Standard Claude Code skill pattern. Build on stable Python backend interface.

### Phase 4: Extended Data & Astrologer Guide Prompt
**Rationale:** With core system working, refine the astrological output quality and add advanced features.
**Delivers:** Asteroids, fixed stars, Arabic parts, dignity/debility calculations. Expert-authored interpretation guide prompt that teaches Claude how to read the chart data astrologically.
**Implements:**
- Asteroid data extraction (Chiron, Lilith, Juno, Ceres, Pallas, Vesta)
- Fixed star conjunction calculations
- Arabic parts (Part of Fortune, Part of Spirit)
- Essential dignities (domicile, exaltation, detriment, fall)
- Astrologer guide prompt authoring and refinement

**Addresses features:** Maximum data depth, dignity/debility, astrologer guide prompt (critical differentiator).
**Avoids pitfalls:** Fixed stars/Arabic parts availability (audit Kerykeion API first, implement manual calc or document as unavailable), guide prompt quality (test with real charts against Claude, iterate based on output quality).
**Research flag:** MEDIUM — Audit Kerykeion's actual API coverage for asteroids and fixed stars before assuming they're available. Guide prompt authoring requires real astrological domain expertise and iterative testing.

### Phase Ordering Rationale

1. **Python backend first** — It's the foundation. The skill layer and storage design both depend on knowing exactly what the Python script can do and what interface it exposes.

2. **JSON schema before SVG** — Data structure decisions affect token consumption and context loading performance, which impacts storage design. SVG is Kerykeion's default; minimal custom work.

3. **Skill layer before advanced features** — Core skill needs to be working and tested before layering in extended calculations and prompt refinement.

4. **Extended features last** — Asteroids, fixed stars, and especially the guide prompt are iterations on a working system. The core system proves the concept.

This sequence also naturally avoids the pitfalls: Kerykeion pinning happens in Phase 1, GeoNames handling is Phase 1, timezone logic is Phase 1, context window planning is Phase 2, argument parsing is Phase 3, guide prompt quality is Phase 4 with real testing.

### Research Flags

**Phases needing deeper research during planning:**
- **Phase 1:** Complex Kerykeion integration. Needs validation of exact API surface, version stability, timezone handling with known charts, GeoNames error modes. Recommend spike testing with actual Kerykeion API before finalizing backend interface.
- **Phase 2:** JSON schema design. Astrological domain knowledge needed to organize data in ways that are both computationally efficient and interpretively useful for Claude. Recommend consulting with astrological practitioner or research existing chart software JSON structures.
- **Phase 4:** Guide prompt authoring and extended feature coverage. Recommend researching Kerykeion's actual support for asteroids, fixed stars, and Arabic parts before committing to including them. Guide prompt iteration requires real testing against Claude with sample charts.

**Phases with standard patterns (skip research-phase):**
- **Phase 3:** Claude Code skill routing is a well-established pattern. Straightforward bash invocation, file I/O, argument parsing. No novel research needed.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Kerykeion is the clear choice — only maintained option with required features. Python 3.10+ is current standard. All supporting dependencies are stable stdlib or minimal. |
| Features | HIGH | Table stakes and differentiators are well-understood from domain expertise. Feature dependencies are explicitly mapped. Anti-features are clearly scoped out for v2. |
| Architecture | HIGH | Three-tier composition is simple and well-defined. Component boundaries are clear (skill ↔ Python via bash, Python ↔ storage via files, skill ↔ context via Read tool). No novel patterns required. |
| Pitfalls | HIGH | Pitfall research identified real integration points and gotchas (timezone, API versioning, geocoding, context size, argument parsing). Prevention strategies are concrete and testable. Risk matrix provides clear priority ranking. |

**Overall confidence:** HIGH

Research quality across all areas is strong — based on direct Kerykeion documentation review, established Claude Code skill patterns, proven astrological calculation principles, and realistic integration risk assessment. No major unknowns remain; uncertainties are well-identified and have clear mitigation strategies.

### Gaps to Address

1. **Exact Kerykeion v4 API surface** — Should be validated during Phase 1 backend development. Check current Kerykeion 4.x docs for exact property names, supported data fields (asteroids, fixed stars), and any breaking changes from recent releases.

2. **Astrological guide prompt expertise** — Guide prompt authoring requires genuine astrological knowledge. Recommend consulting with or hiring an experienced astrologer to author the initial prompt and validate Claude's interpretations against real chart data.

3. **Token count of real charts** — Estimate context consumption by generating several sample charts and measuring actual JSON size. Validate whether context window management or "summary vs full" modes are needed.

4. **Windows path handling** — Cross-platform testing is noted as important. Verify pathlib + `$HOME` expansion work correctly on Windows during Phase 1-2.

5. **GeoNames service behavior** — Understanding actual failure modes (timeout vs bad coordinates vs ambiguous match) will inform Phase 1 error handling strategy. Recommend testing with difficult location names (Springfield, San Jose, etc.).

## Sources

### Primary (HIGH confidence)
- **Kerykeion official documentation** (GitHub, PyPI) — Core library features, AstrologicalSubject API, SVG generation, GeoNames integration
- **Python 3.10+ standard library docs** — pathlib, argparse, json
- **Claude Code documentation** — Skill definition format, bash invocation, Read/Write tools, context injection patterns
- **Astrological calculation principles** — Placidus house system, aspect orbs, dignity rules (standard references)

### Secondary (MEDIUM confidence)
- **PITFALLS.md research** — Integration-specific risk assessment based on domain knowledge and expected failure modes
- **ARCHITECTURE.md research** — Component design and build sequence derived from dependency analysis
- **FEATURES.md research** — Feature prioritization and complexity estimates from domain research

### Tertiary (LOW confidence)
- None identified — all major decisions rest on well-documented foundations

---
*Research completed: 2026-02-16*
*Ready for roadmap: yes*
