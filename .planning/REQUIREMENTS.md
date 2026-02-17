# Requirements: generate-natal-chart

**Defined:** 2026-02-17
**Core Value:** Load a person's complete natal chart data into Claude's context so it can answer deeply specific questions about life path, psychology, and astrological patterns based on real calculated positions.

## v1.1 Requirements

Requirements for Transits & Progressions milestone. Each maps to roadmap phases.

### Transits

- [ ] **TRAN-01**: User can calculate current transit positions against a natal chart profile
- [ ] **TRAN-02**: User can see transit-to-natal aspects with configurable orbs (default: 1-3° by aspect type)
- [ ] **TRAN-03**: User can see which natal houses transiting planets occupy
- [ ] **TRAN-04**: User can see retrograde status for each transiting planet
- [ ] **TRAN-05**: User can see whether each transit aspect is applying or separating
- [ ] **TRAN-06**: User can generate a transit timeline for preset ranges (week, 30 days, 3 months, year)
- [ ] **TRAN-07**: User can generate a transit timeline for custom start/end dates
- [ ] **TRAN-08**: User can see transit events (exact aspect hits) within a date range

### Progressions

- [ ] **PROG-01**: User can calculate secondary progressions for a target date or age
- [ ] **PROG-02**: User can see progressed-to-natal aspects with 1° orb
- [ ] **PROG-03**: User can see monthly progressed Moon positions and sign changes for a target year
- [ ] **PROG-04**: User can see element/modality distribution shifts between natal and progressed charts

### Solar Arc

- [ ] **SARC-01**: User can calculate solar arc directions for a target year
- [ ] **SARC-02**: User can see solar arc-to-natal aspects with 0.5-1° orb
- [ ] **SARC-03**: User can choose between true arc (default) and mean arc calculation methods

### Integration

- [ ] **INTG-01**: Current transits auto-load when a chart profile is opened
- [ ] **INTG-02**: Dedicated transit/progression interpretation guide injected into Claude's context
- [ ] **INTG-03**: Combined JSON output includes natal + predictive data in a single load
- [ ] **INTG-04**: Skill routing supports targeted queries (e.g., "transits for next 3 months")
- [ ] **INTG-05**: User can save transit/progression/solar arc snapshots for future reference
- [ ] **INTG-06**: Snapshot files stored with date-based naming in existing profile directories

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Synastry

- **SYNC-01**: User can compare two natal charts for compatibility analysis
- **SYNC-02**: User can see synastry aspects between two charts
- **SYNC-03**: User can generate composite chart from two natal charts

### Returns

- **RETN-01**: User can calculate solar return chart for a given year
- **RETN-02**: User can calculate lunar return chart for a given month

### Advanced Predictive

- **ADVP-01**: User can see transit aspects to progressed planets (not just natal)
- **ADVP-02**: User can receive transit alerts for key upcoming aspects

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Multi-chart synastry/compatibility | Deferred to v2 — requires different interpretation context |
| Solar/lunar returns | Different chart type with location dependency — deferred to v2 |
| Transit alerts/notifications | Requires scheduling infrastructure beyond CLI scope |
| Minor aspects for transits | Low signal-to-noise — standard practice uses major aspects only |
| Multiple house systems | Kerykeion limitation, config complexity — Placidus only |
| Real-time updating transits | No benefit for CLI tool — calculate on-demand instead |
| Custom SVG styling | Using Kerykeion defaults — deferred |
| Mobile or web UI | Claude Code CLI only |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| TRAN-01 | Phase 7 | Pending |
| TRAN-02 | Phase 7 | Pending |
| TRAN-03 | Phase 7 | Pending |
| TRAN-04 | Phase 7 | Pending |
| TRAN-05 | Phase 7 | Pending |
| TRAN-06 | Phase 8 | Pending |
| TRAN-07 | Phase 8 | Pending |
| TRAN-08 | Phase 8 | Pending |
| PROG-01 | Phase 9 | Pending |
| PROG-02 | Phase 9 | Pending |
| PROG-03 | Phase 9 | Pending |
| PROG-04 | Phase 9 | Pending |
| SARC-01 | Phase 10 | Pending |
| SARC-02 | Phase 10 | Pending |
| SARC-03 | Phase 10 | Pending |
| INTG-01 | Phase 11 | Pending |
| INTG-02 | Phase 11 | Pending |
| INTG-03 | Phase 11 | Pending |
| INTG-04 | Phase 11 | Pending |
| INTG-05 | Phase 12 | Pending |
| INTG-06 | Phase 12 | Pending |

**Coverage:**
- v1.1 requirements: 21 total
- Mapped to phases: 21/21 ✓
- Unmapped: 0

---
*Requirements defined: 2026-02-17*
*Last updated: 2026-02-17 after roadmap creation*
