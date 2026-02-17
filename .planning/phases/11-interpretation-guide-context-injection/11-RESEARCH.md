# Phase 11: Interpretation Guide & Context Injection - Research

**Researched:** 2026-02-17
**Domain:** Claude Code skill architecture, skill routing patterns, astrological interpretation for transits/progressions/solar arcs
**Confidence:** HIGH

## Summary

Phase 11 is a pure skill layer update. All backend predictive modes are already complete and verified (Phases 7-10). The task is to extend `~/.claude/skills/natal-chart/SKILL.md` so that: (1) transits auto-load when a chart profile is opened, (2) a transit/progression/solar arc interpretation guide is embedded in SKILL.md context, (3) combined natal+predictive data loads in a single operation, and (4) the skill routes targeted predictive queries (e.g., "transits for next 3 months") to the correct backend CLI flags.

Research confirms there is no new library to install, no backend change needed, and no new architecture to design. The existing Phase 6 pattern (Read tool + inline interpretation guide in SKILL.md) scales directly to the predictive modes. The only technical work is expanding the SKILL.md to cover five additional backend modes, documenting their JSON structure in the interpretation guide, and defining the routing rules Claude must follow to invoke each mode.

**Primary recommendation:** Extend SKILL.md with (a) a new "Predictive Mode" routing section that maps user intent to CLI flags, (b) updated "Context Loading" steps that auto-invoke `--transits` on profile open and Read the result into context alongside chart.json, and (c) an expanded interpretation guide covering transit, progression, solar arc, and timeline interpretation using the actual JSON field paths from each backend mode. No new files, no new tools, no backend changes.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Claude Code Skills | Current (2026) | Context injection mechanism | Native Claude Code feature — skill body injected into conversation on invocation |
| Read tool | Built-in | Load JSON into conversation context | Standard skill tool; already in allowed-tools |
| Bash tool | Built-in | Invoke Python backend CLI | Already in allowed-tools; used for all backend modes |
| AskUserQuestion tool | Built-in | Present profile/mode selection menus | Already in allowed-tools |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `$ARGUMENTS` substitution | Built-in | Route user intent to correct mode | Parsing "transits for einstein" → `--transits albert-einstein` |
| Inline markdown | Standard | Structure interpretation guide sections | Embed transit/progression/SA guide in SKILL.md body |
| Python backend | 2297 LOC | Calculate all predictive modes | Invoked via Bash; outputs structured JSON to stdout |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Inline interpretation guide in SKILL.md | Separate guide file loaded with Read | Inline is simpler — no path management, always injected with skill, consistent with Phase 6 pattern |
| Auto-load transits on every chart open | Only load transits on explicit request | Auto-load satisfies INTG-01 requirement and improves UX — transits are always relevant context |
| Single combined output mode | Separate natal and transit JSON loads | Two separate Read calls (natal chart.json + transit JSON) is simpler than a new backend endpoint; backend already outputs transit JSON to stdout |

**Installation:** None. All dependencies exist in the current stack.

## Architecture Patterns

### Recommended Skill Structure

The existing SKILL.md structure (Phase 6) extends naturally:

```
~/.claude/skills/natal-chart/
└── SKILL.md    # Extended with predictive routing + interpretation guide
```

No new files needed. SKILL.md will grow from ~385 lines to approximately 600-700 lines, which is within the practical limit for skill files.

### Pattern 1: Predictive Mode Routing

**What:** User says something like "show me transits for einstein" or "what are my progressions?" — skill must detect intent and route to correct CLI flag.

**When to use:** When user mentions transits, progressions, solar arcs, or timeline in the context of a loaded/named chart.

**Routing map:**

| User Intent | CLI Flag | Example invocation |
|-------------|----------|-------------------|
| Current transits for a chart | `--transits SLUG` | `./venv/Scripts/python astrology_calc.py --transits albert-einstein` |
| Transit timeline (next 30d) | `--timeline SLUG --range 30d` | `./venv/Scripts/python astrology_calc.py --timeline albert-einstein --range 30d` |
| Transit timeline (next 3mo) | `--timeline SLUG --range 3m` | `./venv/Scripts/python astrology_calc.py --timeline albert-einstein --range 3m` |
| Transit timeline (custom range) | `--timeline SLUG --start DATE --end DATE` | `./venv/Scripts/python astrology_calc.py --timeline albert-einstein --start 2026-03-01 --end 2026-06-30` |
| Secondary progressions | `--progressions SLUG` | `./venv/Scripts/python astrology_calc.py --progressions albert-einstein` |
| Progressions at specific date | `--progressions SLUG --target-date DATE` | `./venv/Scripts/python astrology_calc.py --progressions albert-einstein --target-date 2027-01-01` |
| Solar arc directions | `--solar-arcs SLUG` | `./venv/Scripts/python astrology_calc.py --solar-arcs albert-einstein` |
| Solar arc at specific date | `--solar-arcs SLUG --target-date DATE` | `./venv/Scripts/python astrology_calc.py --solar-arcs albert-einstein --target-date 2027-01-01` |

**Decision point:** Skill must determine the profile slug. If chart.json is already loaded in context (natal chart was opened), use the slug from `meta.slug` in that JSON. If no chart is loaded, ask the user which profile.

### Pattern 2: Auto-Load Transits on Chart Open (INTG-01)

**What:** When a natal chart profile is opened (create or load), immediately also run `--transits SLUG` and load the result alongside chart.json.

**Implementation in SKILL.md "Context Loading" section:**

After loading chart.json via Read tool, the skill should:
1. Run `--transits SLUG` via Bash
2. Store the stdout JSON (transit snapshot)
3. The transit JSON is now in context alongside chart.json
4. Display a brief summary: "Current transits loaded — N active transit aspects"

This satisfies INTG-01 without adding a new backend mode. The transit snapshot gives "what's happening right now" context for every profile load.

**Important:** Transit JSON outputs to stdout. The Bash tool captures stdout automatically. The skill instruction should tell Claude to treat the Bash output as the transit data (read it from stdout, not from a file).

### Pattern 3: Combined Natal + Predictive Load (INTG-03)

**What:** A single skill invocation loads both natal chart data and predictive data.

**Implementation:** Two-step in skill execution:
1. `Read ~/.natal-charts/{slug}/chart.json` → natal data in context
2. `Bash --transits SLUG` → transit JSON in context (stdout capture)

Both are now in Claude's context window simultaneously. Claude can answer questions that synthesize natal placements with current transits (e.g., "transiting Saturn is conjuncting my natal Moon — what does that mean?").

For targeted queries (progressions, solar arcs), the user explicitly requests them. The skill loads chart.json first (if not already loaded), then runs the specific predictive mode, and loads both into context.

### Pattern 4: Targeted Query Routing (INTG-04)

**What:** User asks a specific predictive question like "what are my transits for next 3 months?" and the skill routes to `--timeline SLUG --range 3m`.

**Implementation:** New "Predictive Mode" section in SKILL.md with routing logic similar to the existing "Mode Determination" section. Key signals to detect:

- "transits" → `--transits` (snapshot)
- "timeline", "next week/month/3 months/year", "upcoming transits" → `--timeline`
- "progressions", "progressed chart" → `--progressions`
- "solar arc", "SA directions" → `--solar-arcs`
- Date-specific → add `--target-date YYYY-MM-DD`

### Anti-Patterns to Avoid

- **Loading transit JSON from a file**: Transit modes output to stdout, not to a file. Skill must capture Bash stdout, not attempt to Read a file.
- **Running all predictive modes on every chart open**: Only auto-load transits (INTG-01). Progressions and solar arcs are heavier computations and should load on-demand.
- **Separate SKILL.md for predictive interpretation**: Keep everything in one SKILL.md. Two skills for the same tool context is confusing.
- **Building a new "combined" backend flag**: The existing `--transits`, `--progressions`, `--solar-arcs` flags are sufficient. Combining them in the skill layer via sequential Bash calls is cleaner than modifying the backend.
- **Calling transit JSON a "file"**: It's stdout from Bash. The skill should tell Claude to treat the Bash tool's output as the transit data, not attempt a Read call.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Transit/progression data fetch | Custom Python scripts | Existing CLI flags (`--transits`, `--progressions`, `--solar-arcs`, `--timeline`) | Backend already implements all modes, verified end-to-end |
| JSON parsing in skill | Custom JSON extractors | Claude reads JSON natively from context | Once in context via Read or Bash stdout, Claude can reference any JSON field |
| Combined predictive report endpoint | New `--full-report` CLI flag | Two sequential Bash calls (natal already on disk; transits via CLI) | Simpler to orchestrate in skill than to add backend complexity |
| Routing logic in Python | Backend mode detection | SKILL.md routing instructions | Skill is the right place for UX routing — backend is computation-only |
| Interpretation guide as MCP server | MCP server with astrology tools | Inline markdown in SKILL.md | Skills solve this natively; no MCP needed for interpretation guidance |

**Key insight:** The backend is already complete. Phase 11 is 100% SKILL.md work — routing instructions and an interpretation guide. No Python required.

## Common Pitfalls

### Pitfall 1: Treating Bash Stdout as a File

**What goes wrong:** Skill instructions tell Claude to "Read the transit JSON from `~/.natal-charts/{slug}/transits.json`" — but transit JSON is never written to a file. It's stdout from `--transits`.

**Why it happens:** Confusing the natal chart profile storage pattern (chart.json is saved) with the transit pattern (transits are ephemeral, computed on-demand, output to stdout).

**How to avoid:** Transit JSON is captured from Bash tool output (stdout). The skill instruction must say "the output of the Bash command is the transit JSON — use it directly." No Read tool needed for transit data.

**Warning signs:** Skill instructions reference a file path for transit/progression/solar arc data that doesn't exist.

### Pitfall 2: Auto-Loading All Predictive Modes on Chart Open

**What goes wrong:** Skill runs `--transits`, `--progressions`, `--solar-arcs`, and `--timeline` every time a chart is opened. This floods context with ~4x JSON payloads and slows chart loading.

**Why it happens:** Interpreting "combined JSON" (INTG-03) too broadly.

**How to avoid:** INTG-01 requires only transits to auto-load. Progressions and solar arcs load on-demand when user requests them. Transit snapshot is lightweight (typically 10-20 aspects) and always relevant.

**Warning signs:** Skill runs more than 2 commands (Read chart.json + one Bash for transits) on every chart open.

### Pitfall 3: Missing Slug Derivation in Predictive Mode

**What goes wrong:** User asks "show me my transits" but no chart is loaded — skill doesn't know which slug to use for `--transits SLUG`.

**Why it happens:** Predictive routing assumes chart context is already established.

**How to avoid:** Before invoking any `--transits SLUG` or `--progressions SLUG` call, skill must verify a profile slug is known. If chart.json is loaded, read `meta.slug`. If not, check if user mentioned a name and look it up via `--list`. If ambiguous, use AskUserQuestion to present profile selection.

**Warning signs:** Bash command has empty or wrong SLUG; backend returns `Error: Profile not found`.

### Pitfall 4: Interpretation Guide Doesn't Reference JSON Field Paths

**What goes wrong:** Interpretation guide says "look at the transiting planets" without telling Claude which JSON field to reference.

**Why it happens:** Guide written abstractly without tying to actual data structures.

**How to avoid:** Each section of the interpretation guide must cite the actual JSON field paths:
- Transit planets: `transit_planets[].name`, `transit_planets[].sign`, `transit_planets[].natal_house`, `transit_planets[].retrograde`
- Transit aspects: `transit_aspects[].transit_planet`, `transit_aspects[].natal_planet`, `transit_aspects[].aspect`, `transit_aspects[].orb`, `transit_aspects[].movement`
- Timeline events: `events[].date`, `events[].transit_planet`, `events[].aspect`, `events[].natal_planet`, `events[].orb_at_hit`
- Progressions: `progressed_planets[].name`, `progressed_planets[].sign`, `progressed_aspects[].progressed_planet`, `monthly_moon[].month`
- Solar arcs: `directed_planets[].name`, `directed_planets[].directed_sign`, `aspects[].directed_point`, `aspects[].natal_point`, `aspects[].movement`

**Warning signs:** Guide says "look at transiting Saturn" without specifying `transit_planets` array path.

### Pitfall 5: SKILL.md Becomes Too Long to Be Effective

**What goes wrong:** Adding full predictive routing + interpretation guide pushes SKILL.md to 800+ lines, degrading its effectiveness as a skill prompt.

**Why it happens:** Being too comprehensive — documenting every edge case in the interpretation guide.

**How to avoid:** Phase 6 interpretation guide is ~200 lines and covers 8 framework areas. The predictive extension should target ~200 additional lines (routing section + predictive guide). Keep the transit/progression/SA interpretation guide focused on the most actionable interpretive principles, not exhaustive keyword lists.

**Warning signs:** SKILL.md exceeds 700 lines. Consider splitting routing instructions from interpretation guide if this happens (separate file in `~/.claude/skills/natal-chart/` directory).

### Pitfall 6: Confusing Progressive Orbs Between Modes

**What goes wrong:** Interpretation guide describes transit aspects with 1-degree orbs when transit aspects actually use 3/3/2/2/1 orbs. Or describes SA aspects with 3-degree orbs when SA uses 1-degree.

**Why it happens:** Each mode has different orb standards. The guide must document orbs per mode.

**How to avoid:**
- Transit snapshot: conjunction/opposition 3°, trine/square 2°, sextile 1° (from `meta.orbs_used`)
- Transit timeline: same as snapshot (3/3/2/2/1)
- Progressions: 1° for all aspects (Kepler College standard)
- Solar arcs: 1° for all aspects (Noel Tyl standard, 1° = 1-year timing window)

**Warning signs:** Interpretation guide gives generic orb advice that doesn't match actual backend output.

## Code Examples

Verified from actual backend output and existing SKILL.md:

### Mode Routing in SKILL.md

```markdown
## Predictive Mode

When user asks about transits, progressions, solar arcs, or upcoming events:

1. **Identify profile slug**
   - If chart.json is already loaded in context: use `meta.slug`
   - If not loaded: ask user which profile, or run `--list` to show options

2. **Route based on user intent:**
   - "transits", "what's happening now" → `--transits SLUG`
   - "upcoming", "next N months", "timeline" → `--timeline SLUG --range [week|30d|3m|year]`
   - "progressions", "progressed chart" → `--progressions SLUG`
   - "solar arc", "SA directions" → `--solar-arcs SLUG`
   - With specific date → add `--target-date YYYY-MM-DD` to any mode

3. **Invoke via Bash tool:**
   ```bash
   cd C:/NEW/backend
   ./venv/Scripts/python astrology_calc.py --transits SLUG
   ```

4. **The Bash output IS the predictive JSON.** No file to Read — transit/progression/SA data
   is printed to stdout. Treat the Bash command output as the data.
```

### Auto-Load Transits in Context Loading Section

```markdown
## Context Loading

After successfully creating or loading a natal chart:

1. **Use Read tool** to load `~/.natal-charts/{slug}/chart.json`
2. **Auto-load current transits** via Bash:
   ```bash
   cd C:/NEW/backend
   ./venv/Scripts/python astrology_calc.py --transits {slug}
   ```
3. **Parse transit output** to display summary:
   - Count `transit_aspects` array length (active aspects right now)
   - Note any planets with `retrograde: true` in `transit_planets`
4. **Display combined summary:**
   ```
   Chart loaded for {name} — Sun in {sign}, Moon in {sign}, {sign} Rising
   Current transits: {N} active aspects — [highlight 2-3 notable ones]

   Full natal chart data and current transit snapshot are now in context.
   ```
```

### Transit Aspect Interpretation Reference

```markdown
## Transit Interpretation Guide

### Transit Snapshot Data Fields
- `transit_planets[].name` — Transiting planet name
- `transit_planets[].sign` — Transiting planet's current sign
- `transit_planets[].natal_house` — Which natal house the transiting planet occupies
- `transit_planets[].retrograde` — Whether planet is retrograde (true/false)
- `transit_aspects[].transit_planet` — Moving planet making the aspect
- `transit_aspects[].natal_planet` — Natal planet being aspected
- `transit_aspects[].aspect` — Aspect type (conjunction, opposition, trine, square, sextile)
- `transit_aspects[].orb` — Current orb in degrees (lower = closer to exact)
- `transit_aspects[].movement` — "Applying" (getting closer to exact) or "Separating" (past exact)

### Orbs by Mode
- Transit snapshot and timeline: conjunction/opposition 3°, trine/square 2°, sextile 1°
- Secondary progressions: 1° for all aspects
- Solar arcs: 1° for all aspects (1° ≈ 1-year timing window)
```

### Progressions Interpretation Reference

```markdown
### Progressions Data Fields
- `progressed_planets[].name` — Progressed planet
- `progressed_planets[].sign` — Progressed sign (may differ from natal)
- `progressed_aspects[].progressed_planet` — Moving progressed planet
- `progressed_aspects[].natal_planet` — Natal planet being contacted
- `monthly_moon[].month` — Month number (1-12)
- `monthly_moon[].sign` — Progressed Moon sign for that month
- `monthly_moon[].sign_change` — true if Moon changed signs this month
- `distribution_shift.elements.{Fire|Earth|Air|Water}.delta` — Change in element count (natal→progressed)
- `meta.progressed_date` — The actual date in the ephemeris representing target date
```

### Solar Arc Interpretation Reference

```markdown
### Solar Arc Data Fields
- `directed_planets[].name` — Directed planet name
- `directed_planets[].directed_sign` — Sign of the directed position
- `directed_planets[].directed_degree` — Degree within sign (0-30)
- `directed_planets[].natal_sign` / `natal_degree` — Original natal position for comparison
- `aspects[].directed_point` — Planet or angle being directed
- `aspects[].natal_point` — Natal point being contacted
- `aspects[].aspect` — Aspect type
- `aspects[].orb` — Orb in degrees (1° = ~1 year from exact)
- `aspects[].movement` — "Applying" (approaching exact, ~1 year ahead) or "Separating" (past exact)
- `meta.arc_degrees` — Total arc in degrees (elapsed years ≈ arc in degrees)
- `meta.arc_method` — "true" (actual Sun arc) or "mean" (Naibod 0.98565°/year)
```

### Timeline Events Interpretation Reference

```markdown
### Timeline Data Fields
- `events[].date` — YYYY-MM-DD date of exact aspect hit
- `events[].transit_planet` — Transiting planet making the aspect
- `events[].aspect` — Aspect type at exact hit
- `events[].natal_planet` — Natal planet being aspected
- `events[].orb_at_hit` — Orb at closest approach (usually < 0.5°)
- `meta.start_date` / `meta.end_date` — Date range of timeline
- `meta.event_count` — Total number of exact hit events in range
```

## State of the Art

| Old Approach | Current Approach | Impact |
|--------------|------------------|--------|
| Separate skills per astrological mode | Single SKILL.md with routing for all modes | Unified context — no context fragmentation between predictive modes |
| Manual context loading (user must ask) | Auto-load transits on chart open | Satisfies INTG-01 without user friction |
| Static interpretation guide (natal only) | Extended guide covering transit/progression/SA | Claude can answer predictive questions with same depth as natal questions |
| Backend modes only accessible via CLI | Skill layer exposes all backend modes via natural language | Satisfies INTG-04 (targeted query routing) |

## Open Questions

1. **SKILL.md size limit**
   - What we know: Phase 6 SKILL.md is ~385 lines. Phase 11 adds routing (~50 lines) + predictive interpretation guide (~200 lines) = estimated ~635 lines total.
   - What's unclear: Whether 635 lines is within practical skill size limits. Phase 6 research noted "under 500 lines for main content" as a guideline.
   - Recommendation: Write the extension first and measure. If total exceeds 700 lines, split interpretation guide into a supporting file at `~/.claude/skills/natal-chart/predictive-guide.md` and reference it from SKILL.md with a Read instruction. Claude Code skills support a supporting files directory.

2. **Token cost of auto-loading transit JSON**
   - What we know: Transit JSON for a profile includes 10 transit_planets + 10-30 transit_aspects. Estimated 800-1500 tokens.
   - What's unclear: Whether this token cost is always justified (it might not be useful if user is asking purely natal questions).
   - Recommendation: Auto-load is still worthwhile. Transit context rarely hurts and often enhances interpretation. The token cost is modest compared to chart.json (~2000-4000 tokens). Document the combined load cost: chart.json + transit JSON ≈ 4000-6000 tokens total.

3. **Multiple predictive modes in one session**
   - What we know: User might load natal + transits, then ask for progressions. Both JSONs would be in context.
   - What's unclear: Whether having 3+ JSON blobs (natal + transits + progressions) is coherent or confusing for interpretation.
   - Recommendation: Design interpretation guide to handle each mode independently. When multiple modes are in context, Claude should synthesize them (e.g., "your progressed Moon is conjuncting your natal Venus, and transiting Jupiter is also activating that area"). Flag this as a synthesis opportunity in the guide.

4. **Handling the `--query-date` flag in skill routing**
   - What we know: `--transits SLUG --query-date YYYY-MM-DD` allows historical or future transit snapshots.
   - What's unclear: Whether Phase 11 should expose this flag via skill routing.
   - Recommendation: Yes, expose it. If user says "show me transits for March 2026" or "what were the transits on my wedding day", the skill should pass `--query-date`. This is a simple natural-language-to-flag mapping.

5. **Routing when no chart is loaded**
   - What we know: User might invoke the skill with "show me transits" as the first message, before any natal chart is loaded.
   - What's unclear: Best UX for this case.
   - Recommendation: Use the existing `--list` command to show profiles, then AskUserQuestion to select one, then run the predictive mode. This mirrors the existing List/Load Mode pattern.

## Sources

### Primary (HIGH confidence)

- `~/.claude/skills/natal-chart/SKILL.md` (current, verified) — Existing skill routing patterns, Mode Determination section, Context Loading steps, interpretation guide structure from Phase 6
- `C:/NEW/backend/astrology_calc.py` (2297 LOC, verified 2026-02-17) — All backend CLI flags and their behavior, JSON output structures for all 5 modes
- Phase 6 RESEARCH.md (`C:/NEW/.planning/phases/06-context-loading-interpretation/06-RESEARCH.md`) — Established patterns for inline skill interpretation guides, Read tool usage, anti-patterns
- Phase 7 SUMMARY.md — Transit JSON structure, routing pattern precedents
- Phase 9 SUMMARY.md — Progressions JSON structure, orb decisions
- Phase 10 SUMMARY.md — Solar arc JSON structure, applying/separating detection
- Live backend output (verified 2026-02-17) — Actual JSON field names confirmed via `--transits`, `--progressions`, `--solar-arcs`, `--timeline` runs against albert-einstein profile

### Secondary (MEDIUM confidence)

- Astrological interpretation principles for transits/progressions — Standard professional frameworks for timing techniques (transit duration by planet speed, progressed Moon significance, SA 1-degree = 1-year rule)
- Claude Code skills documentation — Size guidelines, supported tools, frontmatter fields

### Tertiary (LOW confidence)

- Optimal SKILL.md size limits — Guidelines exist ("under 500 lines") but are not hard limits; practical experience from Phase 6 suggests they are flexible

## Metadata

**Confidence breakdown:**
- Backend CLI flags and JSON structure: HIGH — Verified by running actual commands against real profiles
- Skill layer routing pattern: HIGH — Existing SKILL.md and Phase 6 research confirm the pattern works
- Interpretation guide framework: HIGH — Phase 6 natal guide is production-validated; same structure extends to predictive modes
- SKILL.md size limits: MEDIUM — Guideline exists but isn't a hard constraint; estimated 635 lines is larger than current but manageable
- Targeted query routing: HIGH — Natural language to CLI flag mapping is well-defined based on existing flag documentation

**Research date:** 2026-02-17
**Valid until:** 60 days (stable domain — backend is complete, skill architecture is established, astrological interpretation principles are centuries-old)
