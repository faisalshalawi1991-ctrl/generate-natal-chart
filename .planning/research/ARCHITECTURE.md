# Architecture Research: generate-natal-chart

## System Components

### 1. Claude Code Skill Layer (`~/.claude/commands/generate-natal-chart.md`)

**Responsibility:** Slash command definition, argument routing, context injection.

- Parses user input to determine mode: create / list / load
- Invokes Python backend via bash for chart generation
- Reads stored JSON for context loading
- Injects astrologer guide prompt alongside chart data
- Handles overwrite confirmation flow

**Interface:** User invokes `/generate-natal-chart [args]` → skill orchestrates everything.

### 2. Python Backend (`natal_chart.py`)

**Responsibility:** All astrological calculations and file I/O.

- Accepts CLI arguments: name, date, time, location
- Creates Kerykeion AstrologicalSubject
- Extracts all planetary data into structured dict
- Calculates extended data (asteroids, Arabic parts, dignities, fixed stars)
- Generates SVG via KerykeionChartSVG
- Writes JSON + SVG to storage directory
- Outputs result status to stdout for skill to read

**Interface:** `python natal_chart.py --name "X" --date "YYYY-MM-DD" --time "HH:MM" --location "City"`

Subcommands:
- `python natal_chart.py create --name ... --date ... --time ... --location ...`
- `python natal_chart.py list`
- `python natal_chart.py check --name ...` (check if profile exists for overwrite warning)

### 3. Storage Layer (`~/.natal-charts/`)

**Structure:**
```
~/.natal-charts/
├── john-doe/
│   ├── chart.json          # Full natal chart data
│   ├── chart.svg           # Visual natal wheel
│   └── metadata.json       # Birth details, generation timestamp (optional)
├── jane-smith/
│   ├── chart.json
│   └── chart.svg
└── ...
```

**Responsibility:** Persistent storage of chart profiles.

- Folder names are slugified person names
- chart.json contains all calculated astrological data
- chart.svg is Kerykeion's default natal wheel visualization
- Directory listing serves as profile index

### 4. Context Injection Layer

**Responsibility:** Transform stored chart data into Claude-interpretable context.

**Components:**
- **Astrologer guide prompt** — A carefully crafted prompt section that teaches Claude how to interpret natal chart data (planet meanings, sign qualities, house topics, aspect interpretations, dignity significance)
- **JSON loading** — Raw chart.json read into conversation context
- **Combined output** — Guide prompt + JSON presented together so Claude can immediately begin astrological interpretation

## Data Flow

### Chart Creation Flow
```
User: /generate-natal-chart John Doe 1990-03-15 14:30 "New York, NY"
  │
  ▼
Skill (.md): Parse arguments → detect CREATE mode
  │
  ├─► Check if profile exists (python natal_chart.py check --name "john-doe")
  │     If exists → warn user, ask to confirm overwrite
  │
  ▼
Skill: Run python natal_chart.py create --name "John Doe" --date "1990-03-15" --time "14:30" --location "New York, NY"
  │
  ▼
Python: Kerykeion AstrologicalSubject → calculate all positions
  │
  ├─► Write ~/.natal-charts/john-doe/chart.json
  ├─► Write ~/.natal-charts/john-doe/chart.svg
  └─► Print success + file paths to stdout
  │
  ▼
Skill: Read ~/.natal-charts/john-doe/chart.json
  │
  ▼
Skill: Inject astrologer guide prompt + chart JSON into context
  │
  ▼
Claude: Now has full chart data + interpretation framework → ready for questions
```

### Chart Loading Flow
```
User: /generate-natal-chart
  │
  ▼
Skill (.md): No args → detect LIST mode
  │
  ▼
Skill: Run python natal_chart.py list
  │
  ▼
Python: Scan ~/.natal-charts/ → print available profiles
  │
  ▼
Skill: Present list to user → ask which to load
  │
  ▼
User: Selects "john-doe"
  │
  ▼
Skill: Read ~/.natal-charts/john-doe/chart.json
  │
  ▼
Skill: Inject astrologer guide prompt + chart JSON into context
  │
  ▼
Claude: Chart loaded → ready for interpretation
```

## Component Boundaries

| From | To | Interface | Data |
|------|----|-----------|------|
| User | Skill | Slash command + args | Text arguments |
| Skill | Python | Bash command | CLI flags |
| Python | Kerykeion | Python API | AstrologicalSubject |
| Python | Storage | File I/O | JSON + SVG files |
| Skill | Storage | Read tool | JSON file content |
| Skill | Claude context | Text injection | Guide prompt + JSON |

## Suggested Build Order

1. **Python backend core** — Kerykeion integration, basic chart calculation, JSON output
2. **Storage layer** — Directory structure, JSON/SVG writing, profile listing
3. **JSON schema design** — Comprehensive structure covering all astrological data points
4. **SVG generation** — Kerykeion chart SVG output
5. **Claude Code skill** — Routing logic, argument parsing, bash invocation
6. **Astrologer guide prompt** — Interpretation framework for Claude
7. **Context injection** — Wire skill to read JSON + inject with guide prompt
8. **Extended calculations** — Asteroids, fixed stars, Arabic parts, dignities
9. **Polish** — Overwrite protection, error handling, edge cases

**Rationale:** Python backend first because it's the foundation. Skill layer depends on knowing what the Python script's interface looks like. Guide prompt can be refined independently once JSON schema is set.

## Key Architecture Decisions

| Decision | Options Considered | Choice | Rationale |
|----------|-------------------|--------|-----------|
| Python script vs Node.js | Python (Kerykeion), Node.js (no good astro lib) | Python | Kerykeion only exists in Python |
| Single script vs package | One natal_chart.py vs pip package | Single script | Simpler deployment, no pip install of custom code needed |
| JSON schema | Flat vs nested vs Kerykeion native | Custom nested | Organized by domain (planets, houses, aspects) for Claude readability |
| Skill routing | Multiple skills vs single smart skill | Single smart skill | User requested intelligent routing in one command |
| Guide prompt location | Embedded in skill vs separate file | Separate file | Easier to iterate on prompt quality independently |
