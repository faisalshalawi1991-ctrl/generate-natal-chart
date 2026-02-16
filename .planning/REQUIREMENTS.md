# Requirements: generate-natal-chart

**Defined:** 2026-02-16
**Core Value:** Load a person's complete natal chart data into Claude's context so it can answer deeply specific questions about life path, psychology, and astrological patterns based on real calculated positions.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Chart Calculation

- [ ] **CALC-01**: Calculate planetary positions (Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune, Pluto) by sign, degree, and minute
- [ ] **CALC-02**: Calculate all 12 house cusps using Placidus house system
- [ ] **CALC-03**: Calculate major aspects (conjunction, opposition, trine, square, sextile) between all planets with standard orbs
- [ ] **CALC-04**: Calculate angles (Ascendant, Midheaven, Descendant, IC) with sign and degree
- [ ] **CALC-05**: Calculate asteroid positions (Chiron, Lilith, Juno, Ceres, Pallas, Vesta) by sign and degree
- [ ] **CALC-06**: Calculate fixed star conjunctions to planets and angles (Regulus, Algol, Spica, and other major fixed stars)
- [ ] **CALC-07**: Calculate Arabic parts (Part of Fortune, Part of Spirit)
- [ ] **CALC-08**: Determine essential dignities for each planet (domicile, exaltation, detriment, fall)
- [ ] **CALC-09**: Calculate element distribution (fire, earth, air, water) across all placements
- [ ] **CALC-10**: Calculate modality distribution (cardinal, fixed, mutable) across all placements
- [ ] **CALC-11**: Identify retrograde status for all applicable bodies

### Input Validation

- [ ] **INPT-01**: Validate birth date is a valid calendar date
- [ ] **INPT-02**: Require exact birth time (reject if not provided)
- [ ] **INPT-03**: Resolve birth location to coordinates via Kerykeion GeoNames lookup
- [ ] **INPT-04**: Display resolved city/country for user verification after geocoding
- [ ] **INPT-05**: Handle GeoNames lookup failures with clear error messages

### Data Output

- [ ] **DATA-01**: Generate structured JSON file containing all calculated chart data organized by astrological domain
- [ ] **DATA-02**: Generate SVG natal wheel chart using Kerykeion's default visualization
- [ ] **DATA-03**: JSON schema includes planets section with sign, degree, house, retrograde status
- [ ] **DATA-04**: JSON schema includes houses section with cusp signs and degrees
- [ ] **DATA-05**: JSON schema includes aspects section with participating bodies, aspect type, orb, and applying/separating
- [ ] **DATA-06**: JSON schema includes asteroids, fixed stars, Arabic parts, dignities, element/modality distributions

### Profile Management

- [ ] **PROF-01**: Store chart profiles in ~/.natal-charts/{slugified-name}/ subfolders
- [ ] **PROF-02**: Each profile contains chart.json and chart.svg
- [ ] **PROF-03**: List all existing chart profiles with person names when invoked without arguments
- [ ] **PROF-04**: Warn and display existing birth details before overwriting an existing profile
- [ ] **PROF-05**: Handle profile name slugification with unicode support (python-slugify)

### Claude Integration

- [ ] **INTG-01**: Load chart JSON directly into Claude's active conversation context
- [ ] **INTG-02**: Inject astrologer interpretation guide prompt alongside raw JSON when loading
- [ ] **INTG-03**: Auto-load chart JSON into context immediately after new chart creation
- [ ] **INTG-04**: Support loading existing profile by selection from list

### Skill Infrastructure

- [ ] **INFR-01**: Claude Code skill definition as .md file in ~/.claude/commands/
- [ ] **INFR-02**: Smart routing: birth details provided → create chart; no args → list/load profiles
- [ ] **INFR-03**: Python backend script invoked via bash from skill
- [ ] **INFR-04**: Cross-platform path handling (pathlib in Python, $HOME in bash)
- [ ] **INFR-05**: Pin Kerykeion version in requirements file

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Synastry

- **SYNC-01**: Load two chart profiles simultaneously for compatibility analysis
- **SYNC-02**: Calculate inter-chart aspects between two people's planets
- **SYNC-03**: Generate composite chart from two natal charts

### Transits

- **TRNS-01**: Calculate current planetary transits to natal positions
- **TRNS-02**: Highlight significant upcoming transits

### Progressions

- **PROG-01**: Calculate secondary progressions for a natal chart
- **PROG-02**: Calculate solar arc directions

### Customization

- **CUST-01**: Configurable house system (Whole Sign, Koch, Equal)
- **CUST-02**: Custom SVG styling and color themes
- **CUST-03**: Configurable orb settings for aspects

## Out of Scope

| Feature | Reason |
|---------|--------|
| Synastry/compatibility analysis | Significant complexity increase — deferred to v2 |
| Transit charts | Requires real-time ephemeris, different calculation model |
| Progression charts | Secondary progressions and solar arc — v2 |
| Custom SVG styling | Kerykeion default sufficient for v1 |
| Web UI | CLI skill only — not a web app |
| Pre-generated horoscope text | Claude generates interpretations from raw data |
| Multiple house systems | Placidus only for v1 |
| Mobile app | Claude Code is desktop CLI |
| Paid API integrations | Local calculation only, no external services beyond GeoNames |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| CALC-01 | Phase 2 | Pending |
| CALC-02 | Phase 2 | Pending |
| CALC-03 | Phase 2 | Pending |
| CALC-04 | Phase 2 | Pending |
| CALC-05 | Phase 3 | Pending |
| CALC-06 | Phase 3 | Pending |
| CALC-07 | Phase 3 | Pending |
| CALC-08 | Phase 3 | Pending |
| CALC-09 | Phase 3 | Pending |
| CALC-10 | Phase 3 | Pending |
| CALC-11 | Phase 2 | Pending |
| INPT-01 | Phase 2 | Pending |
| INPT-02 | Phase 2 | Pending |
| INPT-03 | Phase 2 | Pending |
| INPT-04 | Phase 2 | Pending |
| INPT-05 | Phase 2 | Pending |
| DATA-01 | Phase 4 | Pending |
| DATA-02 | Phase 4 | Pending |
| DATA-03 | Phase 4 | Pending |
| DATA-04 | Phase 4 | Pending |
| DATA-05 | Phase 4 | Pending |
| DATA-06 | Phase 4 | Pending |
| PROF-01 | Phase 4 | Pending |
| PROF-02 | Phase 4 | Pending |
| PROF-03 | Phase 4 | Pending |
| PROF-04 | Phase 4 | Pending |
| PROF-05 | Phase 4 | Pending |
| INTG-01 | Phase 6 | Pending |
| INTG-02 | Phase 6 | Pending |
| INTG-03 | Phase 6 | Pending |
| INTG-04 | Phase 5 | Pending |
| INFR-01 | Phase 5 | Pending |
| INFR-02 | Phase 5 | Pending |
| INFR-03 | Phase 1 | Pending |
| INFR-04 | Phase 1 | Pending |
| INFR-05 | Phase 1 | Pending |

**Coverage:**
- v1 requirements: 36 total
- Mapped to phases: 36
- Unmapped: 0

---
*Requirements defined: 2026-02-16*
*Last updated: 2026-02-16 after roadmap creation*
