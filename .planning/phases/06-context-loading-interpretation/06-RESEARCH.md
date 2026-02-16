# Phase 6: Context Loading & Interpretation - Research

**Researched:** 2026-02-16
**Domain:** Claude Code skill architecture, context injection, astrological chart interpretation
**Confidence:** HIGH

## Summary

Phase 6 implements context loading and interpretation for natal chart data through Claude Code's existing skill mechanisms. The technical approach is straightforward: use the Read tool within the existing skill to load chart.json into Claude's active conversation context, and provide expert interpretation guidance directly in the SKILL.md file that activates when charts are loaded.

Research reveals that Claude Code skills work through **on-demand prompt expansion** rather than requiring specialized context injection APIs. When a skill is invoked, the SKILL.md body is injected directly into the conversation, and the skill can use the Read tool (via `allowed-tools`) to load JSON files into context. This means chart data loading is simply reading the file, and interpretation guidance is markdown content within the skill definition.

**Primary recommendation:** Extend the existing natal-chart skill's SKILL.md with an interpretation guide section that activates when chart.json is loaded. Use Read tool (already in allowed-tools) to load JSON after chart creation or profile loading. Structure interpretation guidance as a systematic framework covering chart ruler, aspects, house placements, dignities, and patterns.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Claude Code Skills | Current (2026) | Context injection mechanism | Native Claude Code feature for expanding prompts on-demand |
| Read tool | Built-in | Load JSON into conversation context | Standard Claude Code tool for file access |
| SKILL.md frontmatter | YAML | Skill configuration and metadata | Agent Skills open standard (agentskills.io) |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `allowed-tools` field | Built-in | Grant Read tool access without approval | When skill needs automatic file reading |
| `$ARGUMENTS` substitution | Built-in | Dynamic skill parameters | For passing profile names or chart paths |
| Markdown sections | Standard | Structure interpretation guidance | Organize guide into digestible sections |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Read tool in skill | Dynamic context injection (`!`command``) | Dynamic injection is preprocessing (runs before Claude sees content), but chart.json already exists on disk - Read tool is simpler and correct pattern |
| Single interpretation guide | Multiple sub-skills per topic | Single guide is more coherent for astrological interpretation, which requires holistic synthesis |
| Auto-load after creation | Manual load command | Auto-load provides better UX - user shouldn't need separate action to access interpretation |

**Installation:**
No additional dependencies. Uses existing Claude Code skill infrastructure and tools.

## Architecture Patterns

### Recommended Skill Structure
```
~/.claude/skills/natal-chart/
├── SKILL.md                 # Skill definition with interpretation guide
└── (no additional files needed)
```

### Pattern 1: Context Loading via Read Tool
**What:** After chart creation or profile load, use Read tool to inject chart.json into conversation context
**When to use:** Immediately after Python backend succeeds
**Example:**
```markdown
<!-- In SKILL.md execution steps -->
4. **On success:**
   - Use Read tool to load `~/.natal-charts/{slugified-name}/chart.json` into context
   - Display chart summary: "Chart loaded for {name} — Sun in {sign}, Moon in {sign}, {sign} Rising"
   - Mention that full chart data is now available for interpretation questions
```

### Pattern 2: Inline Interpretation Guide
**What:** Embed expert astrologer interpretation framework directly in SKILL.md
**When to use:** Provide systematic guidance for Claude when answering chart questions
**Example:**
```markdown
## Astrological Interpretation Guide

When interpreting natal charts, follow this systematic framework:

### 1. Chart Overview
- **Chart Ruler**: Identify rising sign, find its ruling planet, assess dignity and aspects
- **Sect**: Day chart (Sun houses 7-12) or Night chart (Sun houses 1-6)
- **Dominant Elements/Modalities**: Note imbalances (>40% or <10% in any category)

### 2. Core Identity (Sun, Moon, Rising)
- **Sun**: Conscious identity, life purpose, vitality
- **Moon**: Emotional nature, instinctive reactions, needs
- **Rising**: Outward persona, approach to life, physical body

### 3. Planetary Analysis
For each planet, synthesize:
- **Sign placement**: How the planet expresses itself
- **House placement**: Where it acts out
- **Aspects**: How it relates to other planets
- **Dignity**: Strength/weakness in current sign

### 4. House Emphasis
- Note houses containing multiple planets (stelliums)
- Empty houses are less emphasized, not absent from life
- House rulers show where that life area's energy flows

### 5. Aspect Patterns
- **T-Square**: Tension triangle requiring action
- **Grand Trine**: Easy flow, potential complacency
- **Grand Cross**: Major tension, endurance required
- **Stellium**: 3+ planets together, concentrated energy

### 6. Synthesis
Weave individual threads into coherent narrative:
- Contradictions reveal complexity, not errors
- Look for themes that repeat across chart
- Major life themes emerge from multiple testimonies
```

### Pattern 3: Auto-Load After Chart Creation
**What:** Automatically load chart.json into context immediately after successful creation
**When to use:** Enhance UX by making interpretation available without explicit load command
**Example:**
```markdown
3. **Check exit code:**
   - `0` = Success (chart created)

4. **On success:**
   - Use Read tool to load `~/.natal-charts/{slugified-name}/chart.json` into context
   - Parse JSON to extract: Sun sign, Moon sign, Rising sign
   - Display summary
   - State: "Full chart data is loaded. Ask questions about aspects, houses, or patterns."
```

### Anti-Patterns to Avoid
- **Loading interpretation guide as separate file**: Increases context overhead and adds complexity. Inline guide is simpler and always available.
- **Verbose JSON summarization**: Don't echo all chart data back to user. They want interpretation, not raw data. Extract key points only.
- **Future prediction without disclaimer**: Astrology describes potentials, not fated outcomes. Frame as insights and tendencies.
- **Ignoring contradictions**: Charts contain paradoxes. Don't cherry-pick harmonious placements. Synthesis requires integrating tensions.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Context injection API | Custom MCP server for chart loading | Read tool in existing skill | Skills use Read tool natively; no custom server needed |
| Interpretation prompt management | External prompt file system | Inline markdown in SKILL.md | Skill body is injected into conversation automatically |
| Chart data parsing | Custom JSON parser in skill | Direct JSON reading | Claude parses JSON natively when loaded via Read |
| Session state tracking | Custom context manager | Existing skill invocation model | Skills have access to full conversation context |
| Progressive disclosure | Lazy-loading interpretation sections | Full guide in SKILL.md | Interpretation guide is ~500 lines - well within skill content limits |

**Key insight:** Claude Code skills already solve context injection. Don't build external systems when the platform provides the mechanism. Use Read tool + SKILL.md markdown = complete solution.

## Common Pitfalls

### Pitfall 1: Overcomplicating Context Injection
**What goes wrong:** Attempting to build MCP servers or dynamic injection systems for chart loading
**Why it happens:** Unfamiliarity with skill architecture - skills seem like they need external tools
**How to avoid:** Understand that skills use Read tool naturally. Chart data loading = `Read ~/.natal-charts/{slug}/chart.json`
**Warning signs:** Researching MCP server creation, writing custom context managers, planning external APIs

### Pitfall 2: Separating Interpretation from Skill
**What goes wrong:** Creating separate interpretation guide files that must be loaded separately
**Why it happens:** Concern about SKILL.md file size or mistaken belief that guides need separate structure
**How to avoid:** Embed interpretation guide directly in SKILL.md. Documentation states skills should stay under 500 lines for main content - astrological guide fits easily
**Warning signs:** Creating `interpretation-guide.md`, planning file loading sequences, adding file path complexity

### Pitfall 3: Not Auto-Loading After Creation
**What goes wrong:** User creates chart but must manually invoke load command to access interpretation
**Why it happens:** Separating creation and loading as distinct operations
**How to avoid:** After successful chart creation, immediately Read the chart.json and state it's available for questions
**Warning signs:** User workflow requires multiple commands, chart exists but isn't in context, "now load it" prompts

### Pitfall 4: Verbosity in Chart Summary
**What goes wrong:** Echoing entire chart.json back to user after loading
**Why it happens:** Trying to "prove" the data loaded successfully
**How to avoid:** Extract only Sun/Moon/Rising for summary. State "Full chart data is now in context" without listing all 50+ data points
**Warning signs:** Multi-paragraph chart dumps, listing all aspects/houses/planets, token bloat

### Pitfall 5: Cookbook Interpretation
**What goes wrong:** Providing isolated planet meanings without synthesis
**Why it happens:** Treating chart as collection of independent facts rather than integrated system
**How to avoid:** Interpretation guide emphasizes synthesis. Look for themes, contradictions, repeated motifs across multiple chart factors
**Warning signs:** "Sun in Aries means X, Moon in Cancer means Y" without integration, ignoring conflicting testimonies

### Pitfall 6: Forgetting Ethical Boundaries
**What goes wrong:** Making definitive predictions about user's life or future
**Why it happens:** Interpretation guide doesn't establish boundaries
**How to avoid:** Include ethics section in guide: frame as potentials/tendencies, emphasize free will, avoid medical/legal/financial advice
**Warning signs:** Definitive statements about future, medical diagnoses, relationship guarantees

## Code Examples

Verified patterns from official sources and existing implementation:

### Auto-Loading Chart After Creation
```markdown
## Create Mode

When birth details are provided in arguments:

### Execution Steps

1. **Parse birth details** from `$ARGUMENTS`

2. **Invoke Python backend** using Bash tool:
   ```bash
   cd C:/NEW/backend
   ./venv/Scripts/python astrology_calc.py "PERSON_NAME" --date DATE --time TIME --city "CITY" --nation "NATION"
   ```

3. **Check exit code:**
   - `0` = Success (chart created)
   - `1` = Error (overwrite conflict or runtime error)
   - `2` = Validation error (invalid arguments)

4. **On success:**
   - Use Read tool to load `~/.natal-charts/{slugified-name}/chart.json` into context
   - Parse JSON to extract:
     - Sun sign: `planets[0].sign`
     - Moon sign: `planets[1].sign`
     - Rising sign: `houses[0].sign` (1st house cusp)
   - Display chart summary:
     ```
     Chart loaded for {name} — Sun in {sun_sign}, Moon in {moon_sign}, {rising_sign} Rising

     Birth Details:
     - Date: {date}
     - Time: {time}
     - Location: {city}, {nation}

     The complete chart data is now in context. Ask questions about:
     - Planetary aspects and configurations
     - House placements and life areas
     - Dignities and planetary strength
     - Chart patterns (T-Square, Grand Trine, etc.)
     - Element and modality distributions
     ```

5. **On overwrite conflict** (exit code 1 with "already exists" in output):
   - Inform user the profile already exists
   - Show existing birth data from backend output
   - Ask if they want to overwrite by re-running with `--force` flag
```
<!-- Source: Existing SKILL.md at ~/.claude/skills/natal-chart/SKILL.md -->

### Interpretation Guide Structure
```markdown
## Astrological Interpretation Guide

When answering questions about a loaded natal chart, apply this systematic framework:

### Core Principles

1. **Synthesis Over Isolation**: Don't interpret placements in isolation. Weave multiple factors together.
2. **Multiple Testimonies**: Strong themes appear in multiple places (e.g., leadership via Leo Sun + Mars conjunct MC + 10th house stellium)
3. **Contradictions Are Real**: Charts contain paradoxes. Fire Sun + Water Moon = identity tension, not error.
4. **Potentials, Not Fate**: Frame interpretations as tendencies and potentials. Emphasize free will.

### Systematic Reading Framework

#### 1. Chart Ruler Analysis
The chart ruler is the planet that rules the rising sign. This planet has special emphasis.

**Steps:**
- Identify rising sign from `houses[0].sign`
- Find ruling planet (Aries→Mars, Taurus→Venus, Gemini→Mercury, Cancer→Moon, Leo→Sun, Virgo→Mercury, Libra→Venus, Scorpio→Mars/Pluto, Sagittarius→Jupiter, Capricorn→Saturn, Aquarius→Saturn/Uranus, Pisces→Jupiter/Neptune)
- Locate chart ruler in `planets` array
- Assess: house placement, sign dignity, major aspects
- **Interpretation**: Chart ruler shows how person approaches life, primary expression mode

#### 2. Sect Determination
Day vs Night chart affects planetary strength.

**From chart.json:**
- `meta.chart_type` = "Day" or "Night"
- Day chart: Sun houses 7-12 (above horizon) - solar planets stronger (Sun, Jupiter, Saturn)
- Night chart: Sun houses 1-6 (below horizon) - lunar planets stronger (Moon, Venus, Mars)

#### 3. Element & Modality Balance
**From chart.json:** `distributions.elements` and `distributions.modalities`

**Interpretation guidelines:**
- **Dominant element** (>40%): Strong expression of that quality
  - Fire: Action, enthusiasm, leadership
  - Earth: Practicality, stability, material focus
  - Air: Communication, ideas, social connection
  - Water: Emotion, intuition, empathy
- **Lacking element** (<10%): Area requiring conscious development
- **Dominant modality** (>40%): Primary operating mode
  - Cardinal: Initiating, starting, leadership
  - Fixed: Sustaining, persistence, resistance to change
  - Mutable: Adapting, flexibility, changeability

#### 4. Planetary Dignities
**From chart.json:** `dignities` array

**Strength hierarchy:**
1. **Domicile** (rulership): Planet in home sign - strongest, acts with authority
2. **Exaltation**: Planet honored - strong, elevated expression
3. **Peregrine**: Neutral territory - moderate, adaptable
4. **Detriment**: Opposite rulership - challenged, must work harder
5. **Fall**: Opposite exaltation - weakest, must overcome limitations

**Interpretation**: Strong dignities = ease of expression. Weak dignities = growth through challenge.

#### 5. Aspect Interpretation
**From chart.json:** `aspects` array

**Major aspects:**
- **Conjunction** (0°): Blended energies, intensification
- **Opposition** (180°): Tension, awareness, integration needed
- **Trine** (120°): Harmony, ease, natural talent (can lead to complacency)
- **Square** (90°): Friction, challenge, motivation for growth
- **Sextile** (60°): Opportunity, support, requires action to activate

**Orb consideration:** `aspects[].orb` - tighter orbs (closer to exact) are stronger

**Movement:** `aspects[].movement` - "applying" (getting closer) vs "separating" (moving apart)

#### 6. House Emphasis
**From chart.json:** Count planets per house from `planets[].house`

**Angular houses** (1, 4, 7, 10): Public, active, initiating
**Succedent houses** (2, 5, 8, 11): Stabilizing, resources, values
**Cadent houses** (3, 6, 9, 12): Mental, adaptive, transitional

**Stellium**: 3+ planets in one house = major life emphasis in that area

#### 7. Fixed Stars
**From chart.json:** `fixed_stars` array

When present, fixed stars add mythological layer:
- **Regulus**: Leadership, courage, royal qualities
- **Spica**: Gifts, success, artistic talent
- **Algol**: Intensity, transformation, shadow work
- **Aldebaran**: Drive, ambition, integrity
- **Antares**: Courage, conflict, intensity
- **Fomalhaut**: Idealism, spirituality, vision

**Only mention if present in chart.** Most charts have 0-2 fixed star conjunctions.

#### 8. Arabic Parts
**From chart.json:** `arabic_parts`

- **Part of Fortune**: Where joy and prosperity flow naturally
- **Part of Spirit**: Where conscious will and action manifest

Interpret by sign and compare to house placements of planets.

### Answering Specific Questions

**"What does my Sun/Moon/Rising mean?"**
1. State sign + house placement
2. Check dignity status
3. Note major aspects
4. Synthesize: How these factors modify core expression
5. Give concrete examples

**"What does this aspect mean?"**
1. Identify the two planets and aspect type
2. Explain what each planet represents
3. Describe aspect dynamic (harmony/tension/etc.)
4. Check houses involved
5. Give life area context

**"What about my [house number/life area]?"**
1. Identify house cusp sign
2. Find ruling planet of that sign
3. Check planets IN that house
4. Aspects to house ruler
5. Synthesize house expression

**"What are my strengths/challenges?"**
1. Planets in domicile/exaltation = natural strengths
2. Planets in detriment/fall = growth areas
3. Harmonious aspects (trines, sextiles) = talents
4. Tense aspects (squares, oppositions) = character builders
5. Element/modality balance shows natural abilities and blind spots

### Ethical Guidelines

**Always:**
- Frame as potentials and tendencies, not fate
- Emphasize free will and choice
- Focus on growth and self-awareness
- Respect client autonomy

**Never:**
- Make medical diagnoses
- Provide legal advice
- Guarantee specific outcomes
- Make definitive predictions about life/death/health
- Shame or judge chart placements

**Language:**
- "This suggests..." not "You are..."
- "Potential for..." not "You will..."
- "One way to work with this is..." not "You must..."

### Example Synthesis

**Question:** "What does my Sun square Moon mean?"

**Weak response:** "Sun square Moon creates tension between your identity and emotions."

**Strong response:**
"Your Sun in Leo (10th house) square Moon in Scorpio (1st house) creates a dynamic tension between your public, expressive identity and your private, intense emotional nature. The Sun wants recognition and creative expression in career (10th house), while the Moon needs emotional depth and privacy (1st house). This isn't comfortable, but it's powerful - you're learning to integrate outer confidence with inner emotional truth. Look at how you've navigated moments when career demands clashed with emotional needs. The square provides motivation to develop both sides rather than choosing one. With Leo's courage and Scorpio's depth, you can bring authentic feeling into public work."
```
<!-- Source: Synthesized from professional astrology reading frameworks -->
<!-- References:
- https://astrologywithheather.helpscoutdocs.com/article/270-level-1-planets-signs-houses-aspects
- https://www.astrology.com/article/birth-chart-astrology-houses-planets-signs-aspects/
- https://trustpsyche.com/how-to-read-a-birth-chart/
-->

### SKILL.md Frontmatter Configuration
```yaml
---
name: natal-chart
description: >
  Generate natal astrological charts from birth data (name, date, time, location)
  or list/load existing chart profiles. Use when user mentions birth chart,
  natal chart, astrology, horoscope, or wants to see their astrological chart.
allowed-tools:
  - Bash
  - Read
  - AskUserQuestion
---
```
<!-- Source: Existing skill definition at ~/.claude/skills/natal-chart/SKILL.md -->

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Custom slash commands in `.claude/commands/` | Unified skills in `.claude/skills/` | October 2025 | Skills support additional features: supporting files directory, frontmatter control, automatic Claude invocation |
| Upfront MCP tool loading (all tools in context) | MCP Tool Search (dynamic loading) | January 2026 | 85% reduction in token overhead, preserves 95% of context window |
| Manual prompt engineering | Context engineering with skills | October 2025 | Progressive disclosure, on-demand expansion, systematic orchestration |
| Separate prompt files | Inline SKILL.md with frontmatter | October 2025 | Single source of truth, automatic injection when invoked |

**Deprecated/outdated:**
- `.claude/commands/` directory: Still works but skills are recommended for new development
- Separate interpretation guide files: Skills support inline content up to reasonable limits (~500 lines)
- Custom context injection mechanisms: Skills handle this natively via Read tool + markdown body

## Open Questions

1. **JSON size impact on context window**
   - What we know: Average chart.json is ~15KB (50-100 lines formatted), contains comprehensive data
   - What's unclear: Exact token count of loaded chart.json (estimated 2000-4000 tokens for typical chart)
   - Recommendation: Load full chart.json. Token cost is justified by complete interpretation capability. If context becomes constrained, can optimize by extracting essential fields only.

2. **Interpretation guide optimal length**
   - What we know: Skill documentation recommends keeping SKILL.md under 500 lines; detailed reference material can go in separate files
   - What's unclear: Whether full astrological interpretation guide exceeds practical limits
   - Recommendation: Start with comprehensive inline guide (~300-400 lines total). If too long, split execution logic (mode routing) from interpretation guide (separate file referenced from main SKILL.md).

3. **Multiple chart comparison**
   - What we know: Current implementation handles one chart at a time
   - What's unclear: How to support synastry (relationship comparison) or transit analysis (current sky vs natal chart)
   - Recommendation: Phase 6 scope is single chart interpretation. Mark synastry/transits as future enhancement. Could use Read tool to load two chart files if needed.

4. **Chart data caching in conversation**
   - What we know: Once Read tool loads chart.json, it's in conversation context for that session
   - What's unclear: Whether chart remains accessible across skill invocations or needs re-reading
   - Recommendation: Test assumption that Read tool loads persist. If not, may need to re-read chart.json when user asks interpretation questions after initial load.

## Sources

### Primary (HIGH confidence)
- [Claude Code Skills Documentation](https://code.claude.com/docs/en/skills) - Official skill structure, frontmatter fields, Read tool usage
- [Inside Claude Code Skills: Structure, prompts, invocation](https://mikhail.io/2025/10/claude-code-skills/) - Technical deep-dive on how SKILL.md injection works
- [Extending Claude's capabilities with skills and MCP](https://claude.com/blog/extending-claude-capabilities-with-skills-mcp-servers) - Progressive disclosure, skills vs MCP architecture
- Existing natal-chart skill at `~/.claude/skills/natal-chart/SKILL.md` - Working implementation of chart generation and profile loading
- Existing backend at `C:/NEW/backend/astrology_calc.py` - chart.json structure and data format

### Secondary (MEDIUM confidence)
- [Birth Charts for Beginners: Four Things You Need to Know](https://www.astrology.com/article/birth-chart-astrology-houses-planets-signs-aspects/) - Foundational interpretation structure (houses, planets, signs, aspects)
- [How to Read A Birth Chart](https://trustpsyche.com/how-to-read-a-birth-chart/) - Systematic approach used by professional astrologers
- [Level 1: Planets, Signs, Houses & Aspects](https://astrologywithheather.helpscoutdocs.com/article/270-level-1-planets-signs-houses-aspects) - Interpretation framework structure
- [Claude Skills Architecture Decoded](https://medium.com/aimonks/claude-skills-architecture-decoded-from-prompt-engineering-to-context-engineering-a6625ddaf53c) - Context engineering principles

### Tertiary (LOW confidence)
- Various astrology prompt templates - General patterns, not verified for accuracy
- WebSearch results on interpretation approaches - Multiple sources agree on systematic framework but specific methodologies vary by tradition

## Metadata

**Confidence breakdown:**
- Context loading mechanism: HIGH - Official docs confirm Read tool + skill body injection
- Skill architecture: HIGH - Multiple authoritative sources (official docs, detailed technical analysis)
- Interpretation framework: MEDIUM - Standard astrological structure verified across multiple sources, but specific interpretive approaches vary by tradition
- Auto-load pattern: HIGH - Read tool confirmed to work within skill execution steps

**Research date:** 2026-02-16
**Valid until:** 60 days (stable domain - Claude Code skills are established feature, astrological interpretation is centuries-old tradition)
