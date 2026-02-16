# Roadmap: generate-natal-chart

## Overview

This roadmap delivers a complete natal chart generation system as a Claude Code skill. Starting with Python foundation and Kerykeion integration, progressing through comprehensive astrological calculations, structured data output with profile storage, skill layer implementation, and culminating in context-aware interpretation through Claude integration with expert guide prompts. Each phase builds on the previous, ensuring stable foundations before layering additional complexity.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation & Setup** - Python environment, dependencies, and core infrastructure
- [x] **Phase 2: Core Calculation Engine** - Essential planetary calculations, houses, aspects, angles, and input validation
- [x] **Phase 3: Extended Calculations** - Asteroids, fixed stars, Arabic parts, dignities, element/modality distributions
- [ ] **Phase 4: Data Output & Storage** - JSON schema design, SVG generation, profile management system
- [ ] **Phase 5: Claude Code Skill Layer** - Skill definition, routing logic, profile operations
- [ ] **Phase 6: Context Loading & Interpretation** - JSON context injection and astrologer guide prompt

## Phase Details

### Phase 1: Foundation & Setup
**Goal**: Python backend is executable with Kerykeion installed and core infrastructure in place
**Depends on**: Nothing (first phase)
**Requirements**: INFR-03, INFR-04, INFR-05
**Success Criteria** (what must be TRUE):
  1. Python script exists with CLI interface accepting name, date, time, location arguments
  2. Kerykeion library is installed and version is pinned in requirements file
  3. Script successfully creates AstrologicalSubject object from test birth data
  4. Cross-platform path handling works correctly using pathlib
**Plans:** 1 plan

Plans:
- [ ] 01-01-PLAN.md — Project structure, pinned dependencies, CLI script with Kerykeion integration

### Phase 2: Core Calculation Engine
**Goal**: All essential astrological calculations work correctly with validated input
**Depends on**: Phase 1
**Requirements**: CALC-01, CALC-02, CALC-03, CALC-04, CALC-11, INPT-01, INPT-02, INPT-03, INPT-04, INPT-05
**Success Criteria** (what must be TRUE):
  1. Script calculates all 10 planetary positions with sign, degree, and minute accuracy
  2. Script calculates all 12 house cusps using Placidus system
  3. Script calculates major aspects between planets with correct orbs
  4. Script calculates all 4 angles (ASC, MC, DSC, IC) with sign and degree
  5. Script identifies retrograde status for applicable bodies
  6. Birth date validation rejects invalid calendar dates
  7. Birth time is required (script errors if missing)
  8. Location resolves to coordinates via GeoNames lookup
  9. Resolved city/country displays for user verification
  10. GeoNames failures produce clear error messages
**Plans:** 1 plan

Plans:
- [ ] 02-01-PLAN.md — Dual-mode location handling, enhanced input validation, and full natal chart calculation output

### Phase 3: Extended Calculations
**Goal**: Advanced astrological data beyond core planets is calculated and available
**Depends on**: Phase 2
**Requirements**: CALC-05, CALC-06, CALC-07, CALC-08, CALC-09, CALC-10
**Success Criteria** (what must be TRUE):
  1. Script calculates asteroid positions (Chiron, Lilith, Juno, Ceres, Pallas, Vesta) by sign and degree
  2. Script calculates fixed star conjunctions to planets and angles for major stars
  3. Script calculates Arabic parts (Part of Fortune, Part of Spirit)
  4. Script determines essential dignities for each planet (domicile, exaltation, detriment, fall)
  5. Script calculates element distribution (fire, earth, air, water) across all placements
  6. Script calculates modality distribution (cardinal, fixed, mutable) across all placements
**Plans:** 2 plans

Plans:
- [ ] 03-01-PLAN.md — Asteroids, Arabic parts, and essential dignities
- [ ] 03-02-PLAN.md — Fixed star conjunctions and element/modality distributions

### Phase 4: Data Output & Storage
**Goal**: Chart data is structured in comprehensive JSON format, visualized as SVG, and stored in organized profile system
**Depends on**: Phase 3
**Requirements**: DATA-01, DATA-02, DATA-03, DATA-04, DATA-05, DATA-06, PROF-01, PROF-02, PROF-03, PROF-04, PROF-05
**Success Criteria** (what must be TRUE):
  1. Script generates structured JSON file with all calculated data organized by astrological domain
  2. Script generates SVG natal wheel chart using Kerykeion's default visualization
  3. JSON includes planets section with sign, degree, house, retrograde status
  4. JSON includes houses section with cusp signs and degrees
  5. JSON includes aspects section with participating bodies, aspect type, orb, applying/separating
  6. JSON includes asteroids, fixed stars, Arabic parts, dignities, element/modality distributions
  7. Chart profiles store in ~/.natal-charts/{slugified-name}/ subfolders
  8. Each profile contains both chart.json and chart.svg files
  9. Script lists all existing chart profiles with person names
  10. Script warns and displays existing birth details before overwriting profile
  11. Profile name slugification handles unicode correctly
**Plans:** 2 plans

Plans:
- [ ] 04-01-PLAN.md — JSON structured data export and SVG natal wheel generation
- [ ] 04-02-PLAN.md — Profile management system with storage, listing, and overwrite protection

### Phase 5: Claude Code Skill Layer
**Goal**: Claude Code skill is installed and operational with smart routing between create/list/load workflows
**Depends on**: Phase 4
**Requirements**: INFR-01, INFR-02, INTG-04
**Success Criteria** (what must be TRUE):
  1. Skill definition file exists in ~/.claude/skills/natal-chart/ (updated from commands/ per research)
  2. Invoking skill with birth details creates new chart
  3. Invoking skill without arguments lists existing profiles
  4. User can select profile from list to load
  5. Skill correctly routes between create, list, and load modes based on arguments
  6. Python backend is invoked via bash from skill
**Plans:** 1 plan

Plans:
- [ ] 05-01-PLAN.md — Skill definition with three-mode routing and backend integration verification

### Phase 6: Context Loading & Interpretation
**Goal**: Chart JSON loads into Claude's context with expert interpretation guide enabling specific astrological analysis
**Depends on**: Phase 5
**Requirements**: INTG-01, INTG-02, INTG-03
**Success Criteria** (what must be TRUE):
  1. Chart JSON loads directly into Claude's active conversation context
  2. Astrologer interpretation guide prompt injects alongside raw JSON
  3. Chart JSON auto-loads into context immediately after new chart creation
  4. Claude can answer specific questions about planetary aspects, house placements, and patterns from loaded chart data
**Plans:** 1 plan

Plans:
- [ ] 06-01-PLAN.md — Astrologer interpretation guide integration into SKILL.md with end-to-end verification

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation & Setup | 1/1 | Complete | 2026-02-16 |
| 2. Core Calculation Engine | 1/1 | Complete | 2026-02-16 |
| 3. Extended Calculations | 2/2 | Complete | 2026-02-16 |
| 4. Data Output & Storage | 0/? | Not started | - |
| 5. Claude Code Skill Layer | 0/1 | Not started | - |
| 6. Context Loading & Interpretation | 0/1 | Not started | - |
