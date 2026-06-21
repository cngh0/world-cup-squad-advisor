# Project Build Log

## 2026-06-20

### Phase 0 / Planning checkpoint

- Created parallel project folder: `world-cup-squad-advisor-lab/`
- Locked product direction as:
  - World Cup team and player decision-support system
  - entity-first, not article-summary-first
- Confirmed reuse strategy:
  - reuse architecture patterns from `ai-news-aggregator-lab`
  - rewrite domain models, source connectors, prompts, and advisor tools
- Locked MVP source direction:
  - official FIFA pages for tournament/team grounding
  - Wikipedia squads page for structured squad extraction
- Added implementation-facing planning docs:
  - `docs/ARCHITECTURE_PLAN.md`
  - `docs/PHASE1_SCAFFOLD_PLAN.md`
  - `docs/DB_SCHEMA_V1.md`

### Notes

- This project should feel more agentic than the learning tracker.
- The core product object is `team / player / squad membership`, not `content / digest`.
- Phase 1 should focus on scaffold + database + minimal web shell before real crawling.

### Known risks

- FIFA pages may rely on dynamic rendering.
- Cross-source player identity matching may get messy later.
- It is easy to overbuild stats and prediction features too early.

### Next step

- Initialize the `uv` project in `world-cup-squad-advisor-lab/`
- Then implement:
  - `app/database/connection.py`
  - `app/database/models.py`
  - `app/database/create_tables.py`

### Progress update

- Added the initial `app/` package skeleton:
  - `app/database/`
  - `app/services/`
  - `app/web/`
  - `app/domain/`
- Added Phase 1 database files:
  - `app/database/connection.py`
  - `app/database/models.py`
  - `app/database/create_tables.py`
  - `app/database/repository.py`

### Current status

- The project still needs local `uv init .` and dependency installation.
- Once dependencies are installed, the next verification target is:
  - read `connection.py`
  - inspect the seven core models
  - run `uv run python -m app.database.create_tables`

## 2026-06-20 - Environment setup completed

- Ran `uv init --app --description "World Cup team and player decision-support system" --vcs none --no-readme --no-workspace .`
- Installed first-pass dependencies with `uv add ...`
- `pyproject.toml`, `.python-version`, `.venv`, and `uv.lock` are now present
- Added `.gitignore` and `.env.example`

### Next verification target

- confirm imports work under `uv run`
- inspect `app/database/connection.py`
- inspect the seven Phase 1 models in `app/database/models.py`
- then prepare the local PostgreSQL connection and run:
  - `uv run python -m app.database.create_tables`

## 2026-06-20 - Docker runtime recovered

- Docker Desktop engine is healthy again
- Next concrete step is to use the project-local compose file under `docker/`
- Planned runtime target:
  - container: `world-cup-squad-advisor-lab-db`
  - database: `world_cup_squad_advisor_lab`
  - default port: `5432`

## 2026-06-20 - PostgreSQL started and Phase 1 tables verified

- Added `docker/docker-compose.yml` for the new project
- Fixed compose naming to avoid collisions with other project resources:
  - compose project name fixed to `world-cup-squad-advisor-lab`
  - volume name fixed to `world-cup-squad-advisor-lab-postgres-data`
- Started PostgreSQL container:
  - `world-cup-squad-advisor-lab-db`
- Ran:
  - `uv run python -m app.database.create_tables`
- Verified inside PostgreSQL that these seven tables exist:
  - `crawl_runs`
  - `data_sources`
  - `players`
  - `raw_documents`
  - `squad_memberships`
  - `teams`
  - `tournaments`

### Important note

- The first empty `\dt` check happened before the final container/state check settled.
- Follow-up verification confirmed Python was connected to the intended container-backed database.

### Next learning checkpoint

- Read `app/database/connection.py`
- Then read `app/database/models.py`
- Then connect `models.py` to `create_tables.py`

## 2026-06-20 - Seed/readback checkpoint prepared

- Added `config/sources.toml` with two initial sources:
  - `fifa_teams`
  - `wikipedia_world_cup_squads`
- Added service scripts:
  - `app/services/seed_reference_data.py`
  - `app/services/show_reference_data.py`
- Replaced placeholder `main.py` with a thin command dispatcher

### New commands

- `uv run python main.py create-tables`
- `uv run python main.py seed-reference-data`
- `uv run python main.py show-reference-data`

## 2026-06-20 - Raw document checkpoint prepared

- Added source config helper:
  - `app/services/source_config.py`
- Added first crawl service:
  - `app/services/crawl_source_once.py`
- Added raw-document readback service:
  - `app/services/show_raw_documents.py`
- Extended `main.py` with:
  - `crawl-source <source_id>`
  - `show-raw-documents [limit]`

### Goal of this checkpoint

- fetch one real configured page
- save it into `raw_documents`
- prove that the project now has a real evidence layer before entity extraction

## 2026-06-20 - Raw document checkpoint completed

- Crawled the configured Wikipedia squads page:
  - source: `wikipedia_world_cup_squads`
  - url: `https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_squads`
- Saved one `raw_documents` record with:
  - document type: `squad_page`
  - title: `2026 FIFA World Cup squads - Wikipedia`
  - text length: about `152717`
- Verified readback through:
  - `uv run python main.py show-raw-documents 3`
  - direct `psql` query inside the PostgreSQL container

### Important behavior confirmed

- `raw_documents` count is now `1`
- `crawl_runs` count is now `2`
- Repeating the same crawl:
  - updates the same `raw_documents` row by `(source_id, external_id)`
  - creates a new `crawl_runs` history row

### Meaning

- `raw_documents` is now working as the evidence layer
- `crawl_runs` is now working as execution history
- The next step should be extracting the first normalized entity records from this raw page

## 2026-06-20 - First normalized entity checkpoint prepared

- Added ID helpers:
  - `app/domain/ids.py`
- Added first extractor:
  - `app/services/extract_wikipedia_team.py`
- Added normalized readback:
  - `app/services/show_team_squad.py`
- Extended `main.py` with:
  - `extract-wikipedia-team "<team_name>"`
  - `show-team-squad "<team_name>"`

### Goal of this checkpoint

- use the stored Wikipedia raw page as input
- extract one team section
- save the first `teams`, `players`, and `squad_memberships` rows

## 2026-06-20 - First normalized entity checkpoint completed

- Extracted the `Czech Republic` section from the stored Wikipedia raw page
- Saved the first normalized records into:
  - `teams`
  - `players`
  - `squad_memberships`
- Verified readback through:
  - `uv run python main.py show-team-squad "Czech Republic"`
  - direct `psql` queries inside PostgreSQL

### Final verified state

- `teams` now contains:
  - `fifa-world-cup-2026:czech-republic`
- `players` count is now `26`
- `squad_memberships` count is now `26`
- Group assignment captured:
  - `Group A`

### Important implementation lessons

- Wikipedia squad rows are not plain `td`-only rows:
  - each player row begins with a `th` cell for shirt number
- Windows CLI output needed UTF-8 reconfiguration to print player names correctly
- Re-running the extractor must clean stale rows:
  - an early parsing bug inserted a fake `Player` row from the table header
  - the extractor was updated to skip header-like rows and delete stale team records on rerun

### Meaning

- The project now has the first complete normalized path:
  - `raw_documents` -> extractor -> `teams / players / squad_memberships`
- This is the point where the project stops being only a crawler and starts becoming an entity system

## 2026-06-20 - Generic extractor validated on a second team

- Reused the same `extract-wikipedia-team` flow for `Mexico`
- Verified:
  - `team_action=inserted`
  - `player_rows=26`
  - `players inserted=26`
  - `memberships inserted=26`

### Final verified state

- `teams` count is now `2`
  - `Czech Republic`
  - `Mexico`
- `players` count is now `52`
- `squad_memberships` count is now `52`
- Both extracted teams are in:
  - `Group A`

### Meaning

- The extractor is no longer a one-team demo
- The current parsing logic is stable enough to handle multiple team sections from the same Wikipedia squads page
- The next step can move from single-team extraction to either:
  - batch extraction for all teams on the page
  - or a first comparison/query surface over the normalized tables

## 2026-06-20 - Wikipedia squads page batch extraction completed

- Added batch extraction entrypoint:
  - `app/services/extract_wikipedia_all_teams.py`
- Reused the single-team extractor as the per-team worker
- Ran:
  - `uv run python main.py extract-wikipedia-all-teams`

### Final verified state

- `teams = 48`
- `players = 1248`
- `squad_memberships = 1248`
- `12` groups detected:
  - `Group A` through `Group L`
- Every group currently has `4` teams

### Sample verification

- Verified direct readback for:
  - `Japan`
- Verified aggregate group distribution through PostgreSQL

### Meaning

- The project now has a usable entity dataset, not just a crawler
- This is enough to begin building the first query/comparison layer that an eventual advisor agent can call

## 2026-06-20 - First query/comparison layer completed

- Added:
  - `app/services/show_team_overview.py`
  - `app/services/compare_teams.py`
- Extended CLI with:
  - `show-team-overview "<team_name>"`
  - `compare-teams "<team_a>" "<team_b>"`

### Verified commands

- `uv run python main.py show-team-overview "Japan"`
- `uv run python main.py compare-teams Japan Mexico`

### What this layer proves

- The normalized tables are now useful for direct decision-oriented queries
- We can already answer lightweight questions such as:
  - what is one squad's position balance?
  - which team has more total caps?
  - who are the most capped and top-scoring players in each squad?

### Meaning

- The project is now beyond ingestion-only work
- The next step can move into:
  - tool-style query APIs for an advisor agent
  - or the first Web readback pages over teams and comparisons

## 2026-06-20 - First Web readback workbench completed

- Added FastAPI Web app entrypoint:
  - `app/web/main.py`
- Added server-rendered routes:
  - `app/web/routes.py`
- Added page data builders:
  - `app/web/viewmodels.py`
- Added first template set:
  - `app/web/templates/base.html`
  - `app/web/templates/dashboard.html`
  - `app/web/templates/teams.html`
  - `app/web/templates/team_detail.html`
  - `app/web/templates/compare.html`
- Added first stylesheet:
  - `app/web/static/css/app.css`

### Verified routes

- `GET /`
- `GET /teams`
- `GET /teams/{team_id}`
- `GET /compare`

### Verification notes

- Import-level check passed:
  - `uv run python -c "from app.web.main import app; print(app.title)"`
- HTTP checks returned `200` for:
  - `/`
  - `/teams`
  - `/teams/fifa-world-cup-2026:japan`
  - `/compare?left_team_id=fifa-world-cup-2026:japan&right_team_id=fifa-world-cup-2026:mexico`
- In-app browser automation was not reliable in this session, so route verification used direct HTTP/content checks instead

### Meaning

- The project now has a real readback surface, not just CLI inspection
- Teams, group distribution, squad leaders, and head-to-head comparison are visible through the browser
- The next layer should move from readback into either:
  - richer entity pages such as `/players`
  - or the first real advisor/tool layer

## 2026-06-20 - First AI team report layer completed

- Added Phase 4 report models:
  - `player_reports`
  - `team_reports`
- Extended repository support for:
  - create/update/get team reports
  - recent report readback
  - team-without-report batch selection
- Added LLM-backed team report agent:
  - `app/agent/team_report_agent.py`
- Added report services:
  - `app/services/generate_team_report.py`
  - `app/services/generate_team_reports.py`
  - `app/services/show_recent_team_reports.py`
- Extended CLI with:
  - `generate-team-report "<team_name>" [--replace] [--confirm-save]`
  - `generate-team-reports [limit] [--replace-existing]`
  - `show-recent-team-reports [limit]`
- Updated Web readback:
  - dashboard now shows team report count and recent report cards
  - team detail now shows the saved AI team report when present

### Verified commands

- `uv run python main.py create-tables`
- `uv run python main.py generate-team-report Japan --replace`
- `uv run python main.py show-recent-team-reports 3`

### Verified database state

- PostgreSQL now contains:
  - `player_reports`
  - `team_reports`
- Verified one saved row in `team_reports` for:
  - `fifa-world-cup-2026:japan`

### Verified web readback

- `GET /` shows:
  - `Team Reports`
  - recent report card content
- `GET /teams/fifa-world-cup-2026:japan` shows:
  - `AI Team Report`
  - generated summary, strengths, risks, and watch players

### Meaning

- The project is no longer only an entity browser
- It now has the first real AI enrichment layer over normalized football data
- The next step should move into:
  - player reports
  - advisor tools over teams and reports
  - or a first `/advisor` interaction surface

## 2026-06-20 - Player report layer and player pages completed

- Added player-level query helpers:
  - `app/services/player_queries.py`
- Added LLM-backed player report agent:
  - `app/agent/player_report_agent.py`
- Added player report services:
  - `app/services/generate_player_report.py`
  - `app/services/generate_player_reports.py`
  - `app/services/show_recent_player_reports.py`
- Extended repository support for:
  - player search with team/position filters
  - player context readback
  - recent player report readback
  - players-without-report batch selection
- Extended CLI with:
  - `generate-player-report "<player_id>" [--replace] [--confirm-save]`
  - `generate-player-reports [limit] [--replace-existing]`
  - `show-recent-player-reports [limit]`
- Added Web pages:
  - `GET /players`
  - `GET /players/{player_id}`
- Updated existing Web pages:
  - dashboard now shows player report count and recent player reports
  - team detail now links player names into player detail pages

### Verified commands

- `uv run python main.py generate-player-report "fifa-world-cup-2026:japan:takefusa-kubo" --replace`
- `uv run python main.py generate-player-reports 1`
- `uv run python main.py show-recent-player-reports 5`

### Verified database state

- PostgreSQL contains saved `player_reports` rows for:
  - `fifa-world-cup-2026:japan:takefusa-kubo`
  - `fifa-world-cup-2026:algeria:melvin-mastil`

### Verified web readback

- `GET /players` shows:
  - player list rows
  - report availability column
  - links into player detail pages
- `GET /players/fifa-world-cup-2026:japan:takefusa-kubo` shows:
  - `AI Player Report`
  - saved summary, strengths, concerns, and role tags
- `GET /` shows:
  - `Player Reports`
  - recent player report cards

### Meaning

- The AI enrichment layer now exists at both team and player granularity
- The project now has enough structured football entities and report surfaces to support a first real advisor/tool layer
- The next step should move into:
  - advisor tools over players and teams
  - player/team comparison workflows
  - or a first `/advisor` page with question answering over stored data

## 2026-06-20 - First advisor layer completed

- Added advisor agent:
  - `app/agent/advisor_agent.py`
- Added advisor context/service layer:
  - `app/services/advisor_service.py`
  - `app/services/ask_advisor.py`
- Extended CLI with:
  - `ask-advisor "<question>" [team_id ...]`
- Extended Web routes with:
  - `GET /advisor`
- Added advisor page template:
  - `app/web/templates/advisor.html`
- Updated Web view-model layer:
  - `build_advisor_page_data(...)`
- Updated navigation and styling so the advisor page is part of the workbench

### Verified behavior

- CLI advisor question answering works for scoped team comparison questions
- advisor answers return structured fields:
  - `answer`
  - `key_points`
  - `cited_team_ids`
  - `cited_player_ids`
  - `follow_up_suggestions`
- Web advisor page can:
  - accept a free-text question
  - scope multiple teams
  - render answer, key points, follow-ups, cited teams, and cited players

### Important architecture decision

- The advisor is intentionally grounded on stored context only:
  - normalized team records
  - normalized player records
  - saved team reports
  - saved player reports
- It does not perform live web lookup, injury lookup, or speculative prediction

### Meaning

- The project has now crossed from "AI-enriched CRUD/readback app" into a first real agent-style interaction surface
- The current system loop is now:
  - `crawl -> raw evidence -> normalized entities -> AI reports -> advisor answer`
- The next major improvement should make the advisor feel more like a workbench, for example:
  - saved sessions/history
  - richer comparison presets
  - explicit advisor tools instead of a single prompt over packed context

## 2026-06-20 - Advisor session/history layer completed

- Added advisor persistence models:
  - `advisor_sessions`
  - `advisor_messages`
- Extended repository support for:
  - session list/readback
  - message list/readback
  - session/message counts
- Extended advisor service layer so each turn now:
  - saves the user message
  - saves the assistant answer
  - reuses recent conversation history on follow-up turns
- Updated the advisor agent prompt flow to include recent conversation history
- Extended CLI with:
  - `ask-advisor "<question>" [team_id ...] [--session <session_id>]`
  - `show-advisor-sessions [limit]`
  - `show-advisor-session <session_id>`
- Reworked Web advisor flow:
  - `POST /advisor` now creates or continues a saved session
  - successful submit redirects to `GET /advisor?session_id=...`
  - page refresh no longer regenerates an LLM answer
- Updated Web readback:
  - dashboard now shows recent advisor sessions
  - advisor page now shows a session sidebar, conversation thread, latest answer block, and cited records

### Verified database state

- PostgreSQL now contains:
  - `advisor_sessions`
  - `advisor_messages`
- Verified saved multi-turn session:
  - `advsess-6db6accc977b`
- Verified saved Web-created session:
  - `advsess-c5b6e480b4f0`

### Verified commands

- `uv run python main.py create-tables`
- `uv run python main.py ask-advisor "Between Japan and Algeria, which squad looks more balanced right now?" fifa-world-cup-2026:japan fifa-world-cup-2026:algeria`
- `uv run python main.py ask-advisor "Compare them by defensive reliability only." --session advsess-6db6accc977b`
- `uv run python main.py show-advisor-sessions 5`
- `uv run python main.py show-advisor-session advsess-6db6accc977b`

### Verified web behavior

- `GET /` returns `200` and shows `Recent Advisor Sessions`
- `GET /advisor` returns `200`
- `POST /advisor` returns `303` and redirects to `/advisor?session_id=...`
- `GET /advisor?session_id=...` returns `200` and shows:
  - conversation thread
  - latest advisor output
  - latest cited records
- empty `POST /advisor` now redirects safely instead of failing

### Meaning

- The advisor is no longer a stateless single-shot page
- The project now has a first real saved interaction loop:
  - `question -> grounded answer -> saved thread -> follow-up question`
- This makes the product much closer to an actual agent workbench instead of a plain LLM wrapper

## 2026-06-20 - Advisor preset task layer completed

- Added preset prompt catalog:
  - `compare_teams`
  - `scout_core_players`
  - `build_watchlist`
- Added shared preset preparation service:
  - `app/services/advisor_presets.py`
- Added CLI preset readback:
  - `app/services/show_advisor_presets.py`
- Extended advisor execution flow so both CLI and Web can run:
  - free-text questions
  - preset-generated questions
- Extended CLI with:
  - `show-advisor-presets`
  - `run-advisor-preset <preset_id> [team_id ...] [--session <session_id>]`
- Updated Web advisor page:
  - preset cards now appear above the free-text question box
  - clicking a preset creates a saved advisor session without requiring manual question entry

### Verified commands

- `uv run python main.py show-advisor-presets`
- `uv run python main.py run-advisor-preset compare_teams fifa-world-cup-2026:japan fifa-world-cup-2026:algeria`
- `uv run python main.py run-advisor-preset build_watchlist fifa-world-cup-2026:japan fifa-world-cup-2026:algeria`
- `uv run python main.py show-advisor-session advsess-9c3bd0ef0942`
- `uv run python main.py show-advisor-session advsess-90cc4c9f186e`

### Verified web behavior

- `GET /advisor` shows:
  - `Compare Teams`
  - `Scout Core Players`
  - `Build Watchlist`
- `POST /advisor` with `preset_id=scout_core_players` returns `303`
- redirected advisor session page shows:
  - conversation thread
  - generated preset-derived question
  - latest advisor answer

### Verified saved sessions

- CLI preset-created comparison session:
  - `advsess-9c3bd0ef0942`
- Web preset-created scout session:
  - `advsess-8cf00cad8a43`
- CLI preset-created watchlist session:
  - `advsess-90cc4c9f186e`

### Meaning

- The advisor no longer depends on the user writing a good prompt from scratch
- The product now has first-class task-shaped entrypoints, which makes it feel more like a decision tool than a thin chat wrapper
- This is the first point where the advisor starts resembling a small agent workbench with repeatable workflows

## 2026-06-20 - Advisor interaction polish completed

- Updated preset-created sessions so new threads use compact task-style titles such as:
  - `Compare Teams: Japan vs Algeria`
- Updated advisor page so follow-up suggestions are now rendered as one-click actions
- Follow-up buttons submit the suggested question back into the same saved session with the same scoped teams

### Verified behavior

- CLI preset-created comparison session now saves as:
  - `advsess-d3b0c2d33776`
  - title: `Compare Teams: Japan vs Algeria`
- Web advisor page for that session shows follow-up suggestion buttons
- Triggering a follow-up action against the same session keeps:
  - the same `session_id`
  - the same team scope
  - a correctly appended user/assistant message pair

### Meaning

- The advisor interaction loop now feels less like isolated saved messages and more like a reusable task workflow
- This is a small but real shift from "chat with memory" toward "tool-like guided agent interaction"

## 2026-06-20 - Advisor turn persistence stabilized

- Refactored advisor turn saving so one turn is persisted as:
  - advisor session create/update
  - user message
  - assistant message
  - all inside one database transaction path
- Added repository helper:
  - `save_advisor_turn(...)`
- Updated `answer_advisor_question(...)` so it now:
  - generates the answer before writing any message rows
  - saves success turns as one user/assistant pair
  - saves failure turns as one user/failed-assistant pair
- Fixed new-session insert ordering by flushing the pending `advisor_sessions` row before inserting dependent `advisor_messages`
- Fixed session readback ordering so same-timestamp rows still display `user -> assistant` in the expected order

### Why this was needed

- The old flow could write a user message first and then fail before the assistant row was saved
- That produced half-written sessions and duplicate-looking follow-ups during retries
- After switching to one commit path, a second issue appeared:
  - new-session writes could hit a foreign-key error because the session row had not yet been flushed before message insertion
- That is now handled explicitly

### Verified commands

- `uv run python -m py_compile app\\database\\repository.py app\\services\\advisor_service.py app\\services\\ask_advisor.py app\\web\\routes.py main.py`
- `uv run python main.py run-advisor-preset compare_teams fifa-world-cup-2026:japan fifa-world-cup-2026:algeria`
- `uv run python main.py ask-advisor "Compare their likely leadership spine only." --session advsess-58497a6003b9`
- `uv run python main.py show-advisor-session advsess-58497a6003b9`
- `docker exec world-cup-squad-advisor-lab-db psql -U postgres -d world_cup_squad_advisor_lab -c "SELECT role, generated, LEFT(content, 90) AS content_preview, created_at FROM advisor_messages WHERE session_id = 'advsess-58497a6003b9' ORDER BY created_at, id;"`

### Verified result

- New preset-created session:
  - `advsess-58497a6003b9`
- Follow-up against the same session:
  - appended cleanly to the same thread
- Readback now shows the expected turn order:
  - `user -> assistant`
  - `user -> assistant`
- No user-only partial turn was created in the verified session
