# Phase 5: Claude Code Skill Layer - Research

**Researched:** 2026-02-16
**Domain:** Claude Code Skills, Bash integration, Python CLI invocation
**Confidence:** HIGH

## Summary

Phase 5 implements a Claude Code skill that serves as the user-facing interface to the natal chart generation system. The skill acts as an intelligent router, determining user intent from invocation context and directing flow between three primary modes: chart creation (with birth details), profile listing (no arguments), and profile loading (interactive selection).

Claude Code skills are markdown files with YAML frontmatter stored in `~/.claude/skills/` that extend Claude's capabilities. Skills use the `$ARGUMENTS` variable for parameter passing, the Bash tool to invoke Python scripts, and the AskUserQuestion tool for interactive selection workflows. The skill architecture emphasizes progressive disclosure (metadata loaded always, full content loaded on trigger, supporting files loaded on demand) to manage context window efficiently.

The Python backend already provides all necessary functionality via CLI flags: chart generation with birth details, `--list` for profile enumeration, `--force` for overwrite protection. The skill's primary responsibility is routing logic and user experience, not computation.

**Primary recommendation:** Create single SKILL.md with conditional routing logic that inspects `$ARGUMENTS` to determine mode (create vs list/load), invokes Python backend via Bash with proper virtual environment activation using direct interpreter path, and uses AskUserQuestion for interactive profile selection when listing mode is triggered.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Claude Code Skills | Agent Skills Standard | Skill definition and invocation | Official Anthropic extension mechanism for Claude Code |
| Bash tool | Built-in | Python script execution | Standard cross-platform command execution in Claude Code |
| AskUserQuestion | Built-in | Interactive user selection | Standard Claude Code tool for multi-choice interactions |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Python venv | Python 3.11+ | Virtual environment isolation | Already exists in backend/venv/ from Phase 1 |
| pathlib (Python) | Built-in | Cross-platform path handling | Backend already uses for profile paths |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Single skill with routing | Separate skills per mode | Single skill: simpler discovery, unified context. Separate: explicit invocation but 3x files to maintain |
| Direct interpreter invocation | Activation script sourcing | Direct path: works on all platforms consistently. Activation: requires platform detection (bin/ vs Scripts/) |
| AskUserQuestion | Bash output parsing | AskUserQuestion: native Claude interaction, better UX. Bash: works but requires manual parsing |

**Installation:**
No installation required. Skills are markdown files. Python backend and dependencies already installed in Phase 1.

## Architecture Patterns

### Recommended Project Structure
```
~/.claude/skills/natal-chart/
├── SKILL.md              # Skill definition with routing logic
└── scripts/              # (Optional) Helper scripts if needed
```

Project backend (already exists):
```
C:/NEW/backend/
├── astrology_calc.py     # Python CLI with all functionality
├── venv/                 # Virtual environment
│   ├── Scripts/          # Windows
│   └── bin/              # Unix
└── requirements.txt      # Dependencies already pinned
```

### Pattern 1: Argument-Based Routing

**What:** Inspect `$ARGUMENTS` to determine user intent and route to appropriate workflow

**When to use:** Single skill serving multiple related modes (create, list, load)

**Example:**
```markdown
---
name: natal-chart
description: Generate natal astrological charts with birth data or list/load existing profiles. Use when user mentions birth chart, natal chart, astrology, or wants to see their chart.
allowed-tools:
  - Bash
  - AskUserQuestion
---

# Natal Chart Generator

## Determine Mode

Analyze the arguments to determine intent:

**Has birth details (name, date, time, location)?** → Create new chart
**No arguments or just "list"?** → List existing profiles and offer to load one
**Specific person name only?** → Search for existing profile, create if not found

## Create Mode

When birth details are provided in $ARGUMENTS:

1. Parse birth data from arguments (name, date, time, location)
2. Invoke Python backend with appropriate flags
3. Handle GeoNames lookup or coordinate mode
4. Load generated chart.json into context automatically

Example invocation:
```bash
cd C:/NEW/backend
./venv/Scripts/python astrology_calc.py "Jane Doe" --date 1990-06-15 --time 14:30 --city "London" --nation "GB"
```

## List/Load Mode

When no arguments or "list" provided:

1. Invoke backend with --list flag to enumerate profiles
2. Parse output to extract profile names and details
3. Use AskUserQuestion to present selection menu
4. Load selected profile's chart.json into context
5. Display chart details for interpretation
```

**Source:** Synthesized from [Claude Code Skills documentation](https://code.claude.com/docs/en/skills) and [GSD skill examples](C:/Users/faisa/.claude/commands/gsd/)

### Pattern 2: Cross-Platform Python Invocation

**What:** Invoke Python scripts in virtual environments reliably across Windows, Linux, macOS

**When to use:** Claude Code skills executing Python scripts via Bash

**Best practice:** Use direct interpreter path rather than activation scripts

**Example:**
```bash
# Windows (Git Bash)
C:/NEW/backend/venv/Scripts/python astrology_calc.py --list

# Unix (Linux/macOS) - same command works via /usr/bin/env
/usr/bin/env python C:/NEW/backend/venv/bin/python astrology_calc.py --list
```

**Why direct path:** Activation scripts differ by platform (`venv/Scripts/activate` vs `venv/bin/activate`), but direct interpreter invocation works universally. Claude Code's bash environment uses Unix conventions even on Windows (Git Bash), so forward slashes work everywhere.

**Source:** [Bash script invoke python virtual environment cross-platform](https://lucdev.net/blog/bash-python-venv), [venv documentation](https://docs.python.org/3/library/venv.html)

### Pattern 3: Interactive Selection with AskUserQuestion

**What:** Present multiple-choice menu for user selection with timeout handling

**When to use:** Selecting from enumerated profiles, choosing between options

**Example:**
```markdown
## Profile Selection

After listing profiles with `--list`, present selection:

Use AskUserQuestion to ask:
- "Which profile would you like to load?"
- Options: [List of profile names from --list output]
- Include "(New chart)" option to create instead

After selection:
1. If "(New chart)" → Switch to create mode
2. Otherwise → Read chart.json from ~/.natal-charts/{selected-slug}/chart.json
3. Load JSON into context
4. Summarize chart details for interpretation
```

**AskUserQuestion features:**
- 60-second timeout (users can click "Type something else" to pause)
- Multiple choice with recommended option marking
- Numbered selection interface
- Integrated into conversation flow

**Source:** [Claude Code AskUserQuestion tool guide](https://www.atcyrus.com/stories/claude-code-ask-user-question-tool-guide), [AskUserQuestion examples](https://www.neonwatty.com/posts/interview-skills-claude-code/)

### Pattern 4: Progressive Disclosure

**What:** Metadata loaded always (name + description ~100 words), SKILL.md body loaded on trigger, supporting files loaded on demand

**When to use:** All skills (context window management best practice)

**Application to natal-chart skill:**
- **Metadata (always loaded):** name: "natal-chart", description with keywords "birth chart, natal chart, astrology, generate, list, load"
- **SKILL.md body (loaded on trigger):** Routing logic, invocation examples, mode determination
- **Supporting files (loaded as needed):** Could add INTERPRETATION_GUIDE.md for astrological reading tips (deferred to Phase 6)

**Source:** [Skills overview - progressive disclosure](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview#how-skills-work)

### Anti-Patterns to Avoid

- **Windows-style paths:** Never use backslashes (`C:\path\file.py`). Always forward slashes (`C:/path/file.py`) for cross-platform compatibility
- **Activation script sourcing:** Don't `source venv/bin/activate` - platform-specific and unreliable. Use direct interpreter path
- **Parsing user input in bash:** Don't parse birth details with grep/sed. Python backend already validates. Skill passes arguments through
- **Multiple skills for related operations:** Don't create separate skills for create/list/load. Single skill with routing maintains unified context
- **Vague descriptions:** Don't use "Helps with astrology". Include specific triggers: "Generate natal charts, list existing profiles, load saved charts"

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Date/time validation | Bash date parsing | Python backend's `valid_date()`, `valid_time()` | Already implemented with proper error handling, year range validation |
| Location geocoding | Manual coordinate lookup | Python backend's GeoNames integration | Handles online/offline modes, city/nation validation, coordinate fallback |
| Profile name sanitization | Bash string manipulation | Python backend's `slugify()` | Unicode handling, safe directory names, consistent with existing profiles |
| Chart data parsing | JSON parsing in bash/skill | Python backend generates structured JSON | Complex nested structure with dignities, distributions, aspects |
| User selection menu | Bash read loops | AskUserQuestion tool | Native Claude integration, timeout handling, recommendation support |
| Virtual environment management | Custom activation logic | Direct interpreter path | Cross-platform, no platform detection needed, works in Git Bash |

**Key insight:** Backend CLI already implements all domain logic, validation, and data operations. Skill's role is routing and orchestration, not reimplementation. Skills that duplicate business logic create maintenance burden and version drift.

## Common Pitfalls

### Pitfall 1: Context Window Bloat

**What goes wrong:** SKILL.md becomes kitchen sink of documentation, examples, astrological interpretation guides, all loaded on every invocation

**Why it happens:** Natural tendency to add "helpful" information without considering token cost. Every token in SKILL.md loads when skill triggers

**How to avoid:**
- Keep SKILL.md under 500 lines (current recommendation)
- Focus on routing logic and essential invocation patterns
- Defer interpretation guides to Phase 6's CONTEXT.md or separate skill
- Challenge each paragraph: "Does Claude need this to route correctly?"

**Warning signs:**
- SKILL.md exceeds 1000 tokens
- Includes astrological interpretation details
- Duplicates information Claude already knows
- Has extensive examples when 1-2 would suffice

**Source:** [Skills best practices - conciseness](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#concise-is-key)

### Pitfall 2: Platform-Specific Path Assumptions

**What goes wrong:** Skill hardcodes `C:\NEW\backend\venv\Scripts\python.exe` or assumes Unix-only paths, breaks on other platforms

**Why it happens:** Testing on single platform, forgetting Claude Code runs on Windows (Git Bash), Linux, macOS

**How to avoid:**
- Always use forward slashes: `C:/NEW/backend/venv/Scripts/python`
- Use relative paths where possible
- Test with `pwd` to verify working directory assumptions
- Consider using `cd` to backend directory before invocation

**Warning signs:**
- Backslashes in paths
- Platform-specific commands without alternatives
- Untested on non-development platform
- Hardcoded absolute paths with Windows drive letters

**Source:** [Skills best practices - avoid Windows paths](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#avoid-windows-style-paths)

### Pitfall 3: Argument Passing Confusion

**What goes wrong:** Skill expects structured arguments but `$ARGUMENTS` is raw string. Birth details get mangled or lost.

**Why it happens:** Misunderstanding that `$ARGUMENTS` is simple string substitution, not parameter parsing

**How to avoid:**
- Document expected argument format clearly: "Jane Doe --date 1990-06-15 --time 14:30 --city London --nation GB"
- Provide examples in skill description
- Let Python backend handle parsing and validation
- Skill focuses on routing (has args vs no args), not parsing

**Warning signs:**
- Skill tries to parse date formats in markdown instructions
- Complex regex or string manipulation in routing logic
- Errors about malformed arguments
- Missing or duplicated parameters

**Source:** [Skills - pass arguments](https://code.claude.com/docs/en/skills#pass-arguments-to-skills)

### Pitfall 4: Profile Selection Without User Confirmation

**What goes wrong:** Skill auto-loads first profile without asking, or creates new chart when existing profile exists

**Why it happens:** Over-automation, not considering ambiguous cases (user says "show my chart" but has multiple profiles)

**How to avoid:**
- Always use AskUserQuestion when multiple choices exist
- Explicit confirmation before overwriting (but Python backend already has `--force` protection)
- Clear mode indication: "Creating new chart for..." vs "Loading existing profile..."
- Handle "no profiles" case gracefully (offer to create first chart)

**Warning signs:**
- Silent auto-selection of profiles
- No confirmation on ambiguous requests
- Confusion when user has multiple profiles
- Missing "create new" option in selection menu

**Source:** [AskUserQuestion tool guide](https://www.atcyrus.com/stories/claude-code-ask-user-question-tool-guide)

### Pitfall 5: Missing Error Handling for Backend Failures

**What goes wrong:** Python script fails (invalid date, GeoNames timeout, missing venv) but skill doesn't handle gracefully

**Why it happens:** Assuming happy path, not testing edge cases, trusting Python backend will always succeed

**How to avoid:**
- Check exit codes from Bash invocations
- Parse error output and present helpful messages
- Provide recovery suggestions (e.g., "GeoNames lookup failed, try with coordinates")
- Test failure modes: invalid dates, network errors, missing dependencies

**Warning signs:**
- Raw Python tracebacks shown to user
- No guidance on how to fix errors
- Silent failures with no output
- Skill doesn't detect when chart generation failed

**Source:** [Skills best practices - solve don't punt](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#solve-dont-punt)

## Code Examples

Verified patterns from official sources:

### Skill Definition with Routing Logic

```yaml
---
name: natal-chart
description: Generate natal astrological charts from birth data (name, date, time, location) or list/load existing chart profiles. Use when user mentions birth charts, natal charts, astrology, or wants to see their astrological chart.
allowed-tools:
  - Bash
  - AskUserQuestion
---

# Natal Chart Generator

## Mode Determination

Inspect $ARGUMENTS to determine intent:

- **Birth details provided** (contains date/time/location) → Create new chart
- **Empty or "list"** → List existing profiles and offer selection
- **Name only** → Search existing, offer to create if not found

## Create Chart Mode

When $ARGUMENTS contains birth details:

1. Extract birth data (name, date, time, location)
2. Determine location mode (city/nation OR lat/lng/tz)
3. Invoke Python backend via Bash
4. Handle errors (validation, GeoNames, overwrite protection)
5. Load generated chart.json into context
6. Summarize chart creation success

**Python backend invocation:**

```bash
cd C:/NEW/backend
./venv/Scripts/python astrology_calc.py "$PERSON_NAME" --date $DATE --time $TIME --city "$CITY" --nation "$NATION"
```

## List/Load Mode

When $ARGUMENTS is empty or "list":

1. List existing profiles:

```bash
cd C:/NEW/backend
./venv/Scripts/python astrology_calc.py --list
```

2. Parse output to extract profile names and birth details

3. Present selection menu via AskUserQuestion:
   - Question: "Which chart profile would you like to load?"
   - Options: [Profile names from list output] + "Create new chart"
   - Recommended: First profile if only one exists

4. After selection:
   - If "Create new chart" → Prompt for birth details, switch to create mode
   - Otherwise → Load chart.json from ~/.natal-charts/{selected-slug}/

5. Display chart data for interpretation

## Error Handling

- **Invalid date/time:** Display Python validation error, prompt for correction
- **GeoNames timeout:** Suggest offline mode with coordinates
- **Profile exists:** Python backend shows warning, skill asks to confirm --force
- **No profiles:** Offer to create first chart
```

**Source:** Synthesized from [Skills documentation](https://code.claude.com/docs/en/skills) and [Skills best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)

### Cross-Platform Python Invocation

```bash
# Approach 1: Direct interpreter path (RECOMMENDED)
# Works on Windows (Git Bash), Linux, macOS
cd C:/NEW/backend
./venv/Scripts/python astrology_calc.py --list

# Approach 2: Conditional platform detection (if needed)
if [ -f "./venv/Scripts/python" ]; then
    # Windows
    ./venv/Scripts/python astrology_calc.py --list
else
    # Unix
    ./venv/bin/python astrology_calc.py --list
fi

# Approach 3: Using /usr/bin/env (less reliable with venv)
cd C:/NEW/backend
/usr/bin/env python astrology_calc.py --list  # May use system Python, not venv
```

**Recommendation:** Use Approach 1 (direct path) since Git Bash on Windows handles Unix-style paths. Claude Code's bash environment is consistent across platforms.

**Source:** [Bash script Python venv cross-platform](https://lucdev.net/blog/bash-python-venv)

### AskUserQuestion Pattern

```markdown
After retrieving profile list, present selection:

Use AskUserQuestion to ask:
- Question: "Which natal chart would you like to load?"
- Options:
  1. "Albert Einstein (Born: 1879-03-14 at 11:30, Ulm, Germany)"
  2. "Test Person (Born: 1990-06-15 at 14:30, London, GB)"
  3. "Create new chart instead"
- Timeout: 60 seconds (user can pause)

Process selection:
- Option 1 or 2: Extract slug, read chart.json
- Option 3: Switch to create mode, prompt for birth details
```

**Note:** AskUserQuestion presents numbered options. User selects by number or can type alternative.

**Source:** [AskUserQuestion Claude Code](https://www.atcyrus.com/stories/claude-code-ask-user-question-tool-guide)

### Profile List Parsing

```bash
# Invoke backend list command
cd C:/NEW/backend
OUTPUT=$(./venv/Scripts/python astrology_calc.py --list)

# Backend output format (from astrology_calc.py lines 560-593):
# Found N chart profile(s):
#
#   albert-einstein/
#     Name:     Albert Einstein
#     Born:     1879-03-14 at 11:30
#     Location: Ulm, Germany
#     Files:    chart.json, chart.svg
#
#   test-person/
#     Name:     Test Person
#     Born:     1990-06-15 at 14:30
#     Location: London, GB
#     Files:    chart.json, chart.svg

# Parse profile names (slug directories) and display names
# Skill presents to AskUserQuestion
```

**Source:** C:/NEW/backend/astrology_calc.py, lines 538-594

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Custom slash commands (.claude/commands/) | Skills (.claude/skills/) | Claude Code 2.0, 2025 | Skills support progressive disclosure, supporting files, namespace isolation |
| Activation script sourcing | Direct interpreter invocation | Best practice 2026 | More reliable cross-platform, no platform detection needed |
| Bash parsing for user input | AskUserQuestion tool | Claude Code 2.0.21, 2025 | Native UI, timeout handling, better UX than terminal prompts |
| Metadata + body always loaded | Progressive disclosure | Agent Skills standard | Scales to 100+ skills without context bloat |

**Deprecated/outdated:**
- `.claude/commands/` files: Still work but lack features (supporting files, controlled invocation). Use `.claude/skills/` instead
- `source venv/bin/activate` in bash: Platform-specific, unreliable. Use direct interpreter path
- Parsing arguments in skill markdown: Let backend CLI handle with argparse. Skill routes, backend parses

## Open Questions

1. **Working directory assumption**
   - What we know: Skill will be in `~/.claude/skills/natal-chart/`, backend in `C:/NEW/backend/`
   - What's unclear: Is working directory predictable when skill invokes bash? Do we need `cd` or can we use absolute paths?
   - Recommendation: Use `cd C:/NEW/backend` before Python invocation to ensure consistent working directory. Test during implementation.

2. **Profile selection presentation**
   - What we know: AskUserQuestion supports multiple choice with descriptions
   - What's unclear: Character limit for option descriptions? Can we include full birth details or just names?
   - Recommendation: Start with "Name (Born: date at time)" format. Truncate if length issues arise. Test with multiple profiles.

3. **Chart.json context loading**
   - What we know: Phase 6 handles interpretation prompt. Phase 5 loads JSON into context
   - What's unclear: Should Phase 5 skill just output chart data, or provide minimal interpretation scaffolding?
   - Recommendation: Phase 5 loads JSON and summarizes basic info (Sun sign, Moon sign, Rising sign). Leave interpretation framework to Phase 6.

4. **Skill namespace**
   - What we know: Skills can be namespaced as `plugin-name:skill-name`
   - What's unclear: Should natal-chart be namespaced or top-level? Risk of collision with other astrology skills?
   - Recommendation: Use top-level `natal-chart` name. Namespace is for plugins. Single-project skills use simple names.

## Sources

### Primary (HIGH confidence)
- [Extend Claude with skills - Claude Code Docs](https://code.claude.com/docs/en/skills) - Skill structure, frontmatter, arguments, routing
- [Skill authoring best practices - Claude API Docs](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) - Progressive disclosure, conciseness, degrees of freedom
- [Claude Agent Skills: A First Principles Deep Dive](https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/) - Architecture, metadata, triggering
- [Inside Claude Code Skills: Structure, prompts, invocation](https://mikhail.io/2025/10/claude-code-skills/) - Invocation mechanism, argument handling
- C:/NEW/backend/astrology_calc.py - Existing CLI interface, list format, validation
- C:/Users/faisa/.claude/commands/gsd/ - GSD skill examples (execute-phase.md, plan-phase.md, resume-work.md)

### Secondary (MEDIUM confidence)
- [What is Claude Code's AskUserQuestion tool?](https://www.atcyrus.com/stories/claude-code-ask-user-question-tool-guide) - Selection menu patterns, timeout handling
- [Claude Code Skills Examples: Using AskUserQuestion](https://www.neonwatty.com/posts/interview-skills-claude-code/) - Multi-round interview patterns
- [How to use a Python venv from a Bash script](https://lucdev.net/blog/bash-python-venv) - Cross-platform venv invocation
- [venv — Creation of virtual environments](https://docs.python.org/3/library/venv.html) - Virtual environment structure

### Tertiary (LOW confidence)
- [Claude Code skill best practices routing arguments](https://shipyard.build/blog/claude-code-cheat-sheet/) - General guidance, not skill-specific
- [I Watched 100+ People Hit the Same Claude Skills Problems](https://natesnewsletter.substack.com/p/i-watched-100-people-hit-the-same) - Common pitfalls (anecdotal, useful patterns)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Skills are official Anthropic standard, Bash/AskUserQuestion are built-in tools
- Architecture: HIGH - Official docs comprehensive, GSD examples confirm patterns, backend CLI already tested
- Pitfalls: MEDIUM-HIGH - Mix of official best practices (HIGH) and community experience (MEDIUM)

**Research date:** 2026-02-16
**Valid until:** 2026-03-16 (30 days - Skills architecture stable, unlikely to change)
