# Roadmap: generate-natal-chart

## Milestones

- ✅ **v1.0 Complete Natal Chart System** — Phases 1-6 (shipped 2026-02-16) | [Archive](milestones/v1.0-ROADMAP.md)
- 🚧 **v1.1 Transits & Progressions** — Phases 7-13 (in progress)
- 📋 **v2.0 Synastry & Returns** — Future (planned)

## Phases

<details>
<summary>v1.0 Complete Natal Chart System (Phases 1-6) — SHIPPED 2026-02-16</summary>

- [x] Phase 1: Foundation & Setup (1/1 plans) — completed 2026-02-16
- [x] Phase 2: Core Calculation Engine (1/1 plans) — completed 2026-02-16
- [x] Phase 3: Extended Calculations (2/2 plans) — completed 2026-02-16
- [x] Phase 4: Data Output & Storage (2/2 plans) — completed 2026-02-16
- [x] Phase 5: Claude Code Skill Layer (1/1 plans) — completed 2026-02-16
- [x] Phase 6: Context Loading & Interpretation (1/1 plans) — completed 2026-02-16

</details>

### 🚧 v1.1 Transits & Progressions (In Progress)

**Milestone Goal:** Add time-aware astrological analysis — current transits, transit timelines, secondary progressions, and solar arc directions — layered on top of the existing natal chart system.

- [ ] **Phase 7: Current Transit Snapshots** - Calculate current transits against natal charts
- [ ] **Phase 8: Transit Timelines** - Generate transit timelines for date ranges
- [ ] **Phase 9: Secondary Progressions** - Implement day-for-a-year progressions
- [x] **Phase 10: Solar Arc Directions** - Add solar arc calculations (completed 2026-02-17)
- [x] **Phase 11: Interpretation Guide & Context Injection** - Transit/progression interpretation and auto-loading (completed 2026-02-17)
- [x] **Phase 12: Snapshot Storage** - Optional snapshot saves for audit trails (completed 2026-02-17)
- [ ] **Phase 13: Tech Debt Cleanup** - Close audit gaps: meta.slug field + timeline --save support

## Phase Details

### Phase 7: Current Transit Snapshots
**Goal**: Users can calculate current transit positions and aspects against their natal chart
**Depends on**: v1.0 (Phase 6)
**Requirements**: TRAN-01, TRAN-02, TRAN-03, TRAN-04, TRAN-05
**Success Criteria** (what must be TRUE):
  1. User can calculate transit positions for any date against a natal chart profile
  2. User can see transit-to-natal aspects with configurable orbs per aspect type
  3. User can see which natal houses transiting planets occupy
  4. User can see retrograde status for each transiting planet
  5. User can see whether each transit aspect is applying or separating
**Plans:** 1 plan

Plans:
- [ ] 07-01-PLAN.md — Add transit snapshot calculation with CLI --transits mode

### Phase 8: Transit Timelines
**Goal**: Users can generate transit timelines showing aspect events across date ranges
**Depends on**: Phase 7
**Requirements**: TRAN-06, TRAN-07, TRAN-08
**Success Criteria** (what must be TRUE):
  1. User can generate transit timeline for preset ranges (week, 30 days, 3 months, year)
  2. User can generate transit timeline for custom start and end dates
  3. User can see exact transit aspect hits (events) within a date range
**Plans:** 1 plan

Plans:
- [ ] 08-01-PLAN.md — Add transit timeline generation with preset/custom date ranges and exact hit event detection

### Phase 9: Secondary Progressions
**Goal**: Users can calculate secondary progressions using day-for-a-year formula
**Depends on**: Phase 7
**Requirements**: PROG-01, PROG-02, PROG-03, PROG-04
**Success Criteria** (what must be TRUE):
  1. User can calculate secondary progressions for any target date or age
  2. User can see progressed-to-natal aspects with 1 degree orb
  3. User can see monthly progressed Moon positions and sign changes for a target year
  4. User can see element and modality distribution shifts between natal and progressed charts
**Plans:** 1 plan

Plans:
- [ ] 09-01-PLAN.md — Add secondary progressions with CLI --progressions mode, progressed aspects, monthly Moon, and distribution shifts

### Phase 10: Solar Arc Directions
**Goal**: Users can calculate solar arc directions using true arc method
**Depends on**: Phase 7
**Requirements**: SARC-01, SARC-02, SARC-03
**Success Criteria** (what must be TRUE):
  1. User can calculate solar arc directions for any target year
  2. User can see solar arc-to-natal aspects with 0.5-1 degree orb
  3. User can choose between true arc and mean arc calculation methods
**Plans:** 1/1 plans complete

Plans:
- [ ] 10-01-PLAN.md — Add solar arc directions with true/mean arc methods, directed positions, and SA-to-natal aspects

### Phase 11: Interpretation Guide & Context Injection
**Goal**: Transits and progressions auto-load with charts and include expert interpretation guidance
**Depends on**: Phase 7, Phase 9, Phase 10
**Requirements**: INTG-01, INTG-02, INTG-03, INTG-04
**Success Criteria** (what must be TRUE):
  1. Current transits auto-load when a chart profile is opened
  2. Dedicated transit and progression interpretation guide loads into Claude's context
  3. Combined JSON output includes natal plus predictive data in a single load
  4. Skill routing supports targeted queries (e.g., "transits for next 3 months")
**Plans:** 2/2 plans complete

Plans:
- [x] 11-01-PLAN.md — Extend SKILL.md with predictive routing, auto-load transits, and interpretation guide
- [ ] 11-02-PLAN.md — Gap closure: add cross-references from mode-specific loading steps to Context Loading steps 6-8

### Phase 12: Snapshot Storage
**Goal**: Users can optionally save transit and progression snapshots for future reference
**Depends on**: Phase 7, Phase 9, Phase 10
**Requirements**: INTG-05, INTG-06
**Success Criteria** (what must be TRUE):
  1. User can save transit, progression, and solar arc snapshots with --save flag
  2. Snapshot files are stored with date-based naming in existing profile directories
**Plans:** 1/1 plans complete

Plans:
- [ ] 12-01-PLAN.md — Add --save flag, save_snapshot() helper, call sites in 3 calculate functions, and SKILL.md routing update

### Phase 13: Tech Debt Cleanup
**Goal**: Close audit gaps — add missing meta.slug field to chart.json and wire --save into timeline mode
**Depends on**: Phase 12
**Requirements**: None (tech debt closure from v1.1 audit)
**Gap Closure:** Closes gaps from v1.1-MILESTONE-AUDIT.md
**Success Criteria** (what must be TRUE):
  1. chart.json meta object includes a `slug` field matching the profile directory name
  2. `--save` flag works with `--timeline` mode (saves timeline snapshot to profile directory)
  3. SKILL.md routing table accurately reflects which modes support `--save`
**Plans:** 1 plan

Plans:
- [ ] 13-01-PLAN.md — Add meta.slug to build_chart_json(), wire --save into calculate_timeline(), verify SKILL.md accuracy

## Progress

**Execution Order:**
Phases execute in numeric order: 1-6 (complete) → 7 → 8 → 9 → 10 → 11 → 12 → 13

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Foundation & Setup | v1.0 | 1/1 | Complete | 2026-02-16 |
| 2. Core Calculation Engine | v1.0 | 1/1 | Complete | 2026-02-16 |
| 3. Extended Calculations | v1.0 | 2/2 | Complete | 2026-02-16 |
| 4. Data Output & Storage | v1.0 | 2/2 | Complete | 2026-02-16 |
| 5. Claude Code Skill Layer | v1.0 | 1/1 | Complete | 2026-02-16 |
| 6. Context Loading & Interpretation | v1.0 | 1/1 | Complete | 2026-02-16 |
| 7. Current Transit Snapshots | v1.1 | 0/1 | Not started | - |
| 8. Transit Timelines | v1.1 | 0/1 | Not started | - |
| 9. Secondary Progressions | v1.1 | 0/1 | Not started | - |
| 10. Solar Arc Directions | v1.1 | Complete    | 2026-02-17 | - |
| 11. Interpretation Guide & Context Injection | v1.1 | Complete    | 2026-02-17 | - |
| 12. Snapshot Storage | v1.1 | Complete    | 2026-02-17 | - |
| 13. Tech Debt Cleanup | v1.1 | 0/1 | Not started | - |
