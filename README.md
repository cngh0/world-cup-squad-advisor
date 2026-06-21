# World Cup Squad Advisor Lab

A parallel project for building a World Cup team and player decision-support system.

## Working Assumption

This project currently assumes:

- tournament: men's FIFA World Cup 2026
- focus: team rosters, player profiles, squad structure, and advisor-style interaction
- user: fans, content creators, analysts, and project-demo users who want explainable team/player insights

## Product Goal

Build a system that:

1. crawls structured World Cup team and player information
2. stores both raw source documents and normalized domain data
3. uses AI to enrich player/team records into readable scouting-style summaries
4. exposes an agent that can answer deeper questions, not just search records

Current end-to-end flow:

`raw_documents -> teams / players / squad_memberships -> team_reports / player_reports -> advisor sessions / advisor messages`

Example questions:

- Which players define Spain's midfield profile?
- Compare Japan and Germany in squad balance and experience.
- If I want to understand Argentina quickly, which five players should I study first?
- Which teams have the strongest depth at full-back?
- Build a short watchlist for breakout forwards from smaller teams.

## Why This Is A Good Parallel Project

Compared with the learning-tracker project, this one pushes harder on:

- multi-source entity extraction
- normalized domain modeling
- AI-assisted structuring
- tool-using advisor behavior
- more obvious agent-style interaction

## What We Reuse From The Existing Project

High-value reusable patterns:

- FastAPI + Jinja Web skeleton
- SQLAlchemy connection / repository pattern
- service-layer orchestration style
- structured LLM output pattern with Pydantic
- pipeline page and advisor page interaction pattern

What should be redesigned instead of copied:

- source scrapers
- domain models
- prompt design
- ranking / recommendation logic
- all content-specific naming and workflow assumptions

## Initial Scope

MVP scope:

- official team/squad pages + structured squad fallback sources
- roster and player identity normalization
- AI-generated player and team reports
- advisor chat for team/player comparison and study/watchlist decisions

Non-goals for v1:

- live event tracking
- minute-by-minute match data
- betting-grade prediction
- fully autonomous background crawling

## Current Local Run Flow

Start the database:

```powershell
docker compose -f docker/docker-compose.yml up -d
```

Create tables:

```powershell
uv run python main.py create-tables
```

Seed the initial tournament and source records:

```powershell
uv run python main.py seed-reference-data
```

Crawl the configured Wikipedia squads page:

```powershell
uv run python main.py crawl-source wikipedia_world_cup_squads
```

Extract all teams from the stored raw page:

```powershell
uv run python main.py extract-wikipedia-all-teams
```

Generate one AI team report:

```powershell
uv run python main.py generate-team-report "Japan" --confirm-save
```

Generate reports in batch for teams that do not have one yet:

```powershell
uv run python main.py generate-team-reports 5
```

Read back recent generated team reports:

```powershell
uv run python main.py show-recent-team-reports 5
```

Generate one AI player report:

```powershell
uv run python main.py generate-player-report "fifa-world-cup-2026:japan:takefusa-kubo" --confirm-save
```

Generate reports in batch for players that do not have one yet:

```powershell
uv run python main.py generate-player-reports 5
```

Read back recent generated player reports:

```powershell
uv run python main.py show-recent-player-reports 5
```

Ask the advisor a grounded question over selected teams:

```powershell
uv run python main.py ask-advisor "Between Japan and Algeria, which squad looks more balanced right now?" fifa-world-cup-2026:japan fifa-world-cup-2026:algeria
```

Continue an existing advisor session:

```powershell
uv run python main.py ask-advisor "Compare them by defensive reliability only." --session advsess-6db6accc977b
```

Read back saved advisor sessions:

```powershell
uv run python main.py show-advisor-sessions 5
uv run python main.py show-advisor-session advsess-6db6accc977b
```

Show the available advisor presets:

```powershell
uv run python main.py show-advisor-presets
```

Run a preset-driven advisor turn:

```powershell
uv run python main.py run-advisor-preset compare_teams fifa-world-cup-2026:japan fifa-world-cup-2026:algeria
uv run python main.py run-advisor-preset scout_core_players fifa-world-cup-2026:japan fifa-world-cup-2026:algeria
uv run python main.py run-advisor-preset build_watchlist fifa-world-cup-2026:japan fifa-world-cup-2026:algeria
uv run python main.py run-advisor-preset defensive_review fifa-world-cup-2026:japan fifa-world-cup-2026:algeria
uv run python main.py run-advisor-preset attacking_core fifa-world-cup-2026:japan fifa-world-cup-2026:algeria
```

Start the Web workbench:

```powershell
uv run uvicorn app.web.main:app --host 127.0.0.1 --port 8012
```

Current Web routes:

- `/`
- `/teams`
- `/teams/{team_id}`
- `/players`
- `/players/{player_id}`
- `/compare`
- `/advisor`

Current MVP checkpoint:

- `team_reports` table is active
- `player_reports` table is active
- single-team AI report generation is working
- batch team report generation is available
- single-player AI report generation is working
- batch player report generation is available
- dashboard and team detail pages can read back saved team reports
- dashboard, players list, and player detail pages can read back saved player reports
- CLI advisor question answering is working through `ask-advisor`
- advisor sessions are saved into `advisor_sessions` and `advisor_messages`
- `ask-advisor` can continue the same thread through `--session <session_id>`
- advisor presets are available through:
  - `compare_teams`
  - `scout_core_players`
  - `build_watchlist`
  - `defensive_review`
  - `attacking_core`
- `run-advisor-preset` can start a saved advisor session from a preset template
- preset-created sessions now use compact tool-style titles such as `Compare Teams: Japan vs Algeria`
- `/advisor` now uses `POST` for new turns, saves the thread, and avoids duplicate generation on page refresh
- `/advisor` exposes preset cards so users can launch structured tasks without writing the full question manually
- `/advisor` exposes follow-up suggestion buttons so the next turn can be launched directly from the last answer
- dashboard can read back recent advisor sessions
- `/advisor` can scope teams, submit a question, continue a saved thread, and render grounded answers
- advisor turns are now saved as an atomic session update plus user/assistant message pair, so retries no longer leave user-only partial turns
- advisor questions now go through a task-routing layer that labels each turn and prepares route-specific tool outputs
- advisor sessions now persist `task_type`, `task_label`, and `tool_trace` so each turn is inspectable
- CLI and `/advisor` both expose the routed task label plus the tool trace used for the answer
- advisor answers are intentionally constrained to stored normalized data and saved reports

## Current Architecture

The project is split into four layers:

1. Evidence layer
   - `crawl_runs`
   - `raw_documents`
   - configured source crawling
2. Normalized entity layer
   - `tournaments`
   - `teams`
   - `players`
   - `squad_memberships`
3. AI enrichment layer
   - `team_reports`
   - `player_reports`
4. Agent interaction layer
   - `advisor_sessions`
   - `advisor_messages`
   - preset task templates
   - advisor context builder
   - task routing and scoped tool-output preparation
   - per-turn tool trace storage
   - structured advisor output
   - CLI and Web multi-turn question-answering surface

Why this shape is useful:

- each answer can be traced back to stored source evidence
- enrichment is separate from raw storage, so reports can be regenerated
- the advisor is grounded on local context instead of open-ended web lookup

## Current Gaps

Most important next upgrades:

- add more sources beyond the first Wikipedia-driven pipeline
- improve cross-source player identity resolution
- extend the task-routed advisor into richer internal tools instead of one heuristic routing layer
- add richer preset families such as defensive review, midfield study plan, and shortlist generation
- consider storing more structured per-turn metadata so follow-up actions can be filtered by task type or preset family

## Primary Planning Document

See:

- `docs/ARCHITECTURE_PLAN.md`
- `docs/PHASE1_SCAFFOLD_PLAN.md`
- `docs/DB_SCHEMA_V1.md`
- `PROJECT_BUILD_LOG.md`
