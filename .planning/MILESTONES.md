# Milestones

## v1.0 Complete Natal Chart System (Shipped: 2026-02-16)

**Phases completed:** 6 phases, 8 plans, 6 tasks

**Key accomplishments:**
- Python 3.11 backend with Kerykeion 5.7.2 calculating full natal charts (planets, houses, aspects, angles)
- Dual-mode geocoding (offline/online GeoNames) with comprehensive input validation
- Extended calculations: asteroids, Arabic Parts, essential dignities, fixed star conjunctions, element/modality distributions
- Structured JSON export + SVG natal wheel chart with profile management (~/.natal-charts/)
- Claude Code skill with three-mode routing (create/list/load) and automatic context loading
- 8-part astrological interpretation guide with ethical guidelines embedded in skill

---


## v1.1 Transits & Progressions (Shipped: 2026-02-17)

**Phases completed:** 7 phases (7-13), 8 plans
**Backend LOC:** 1,070 → 2,360 Python (+1,290 LOC)
**Timeline:** 2026-02-17 (1 day, 44 commits)

**Key accomplishments:**
- Transit snapshots: current planet transits against natal charts with configurable orbs, house placement, retrograde status, and applying/separating aspects
- Transit timelines: event timelines with preset (week/30d/3m/year) and custom date ranges with exact aspect hit detection
- Secondary progressions: day-for-a-year progressed charts with progressed-to-natal aspects, monthly Moon tracking, and element/modality distribution shifts
- Solar arc directions: true arc and mean arc calculation methods with directed positions and SA-to-natal aspects
- Skill integration: predictive routing, auto-load transits on chart open, and comprehensive transit/progression interpretation guide
- Snapshot storage: --save flag persists all 4 predictive modes as date-based JSON files in profile directories

---

