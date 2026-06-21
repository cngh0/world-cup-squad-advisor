# World Cup Squad Advisor Lab - Architecture Plan

## 1. Project Framing

### 1.1 Core Idea

This project is not just a football database or a static roster viewer.

It should become:

> a World Cup team and player decision-support system with AI-assisted structuring and an interactive advisor agent

The key difference is:

- database product: stores and displays player/team facts
- LLM summary product: summarizes documents
- advisor agent product: answers user decisions using stored data, structured reports, and tool calls

### 1.2 Default Assumption

Unless we explicitly change scope later, the default target is:

- tournament: men's FIFA World Cup 2026
- data unit: teams, players, squad memberships, team reports, player reports
- interaction goal: compare, shortlist, understand, and explain

---

## 2. What To Reuse From `ai-news-aggregator-lab`

We should reuse patterns, not blindly clone code.

### 2.1 High Reuse

#### A. Project structure pattern

Reusable:

- `app/database/`
- `app/services/`
- `app/agent/`
- `app/web/`
- `config/`

Reason:

- the layering is already good for crawl -> normalize -> enrich -> interact

#### B. SQLAlchemy connection and repository pattern

Reusable idea:

- `connection.py`
- `create_tables.py`
- repository class as the data access layer

Reason:

- the new project will still need normalized tables and service-side queries

#### C. Structured LLM output pattern

Reusable idea:

- Pydantic output models
- prompt version tracking
- fallback from structured parse to JSON parsing

Reason:

- player reports and team reports are much safer if outputs are structured

#### D. Service orchestration style

Reusable idea:

- small service functions
- thin CLI/router entrypoints
- result dict summaries for UI and logs

#### E. Web MVP style

Reusable idea:

- FastAPI + Jinja workbench
- pipeline page
- advisor page
- inspectable internal workflow

### 2.2 Medium Reuse

#### A. Config-driven source management

The `sources.toml` idea is reusable, but the schema must change.

The new config should describe:

- source type
- team-level or player-level coverage
- crawl frequency
- parsing strategy
- reliability level

#### B. Learner/advisor pattern

The current learning advisor shows the right shape:

- persistent profile
- current request
- candidate records
- structured advice

But the new advisor must become sports-domain specific.

### 2.3 Low Reuse / Should Be Rewritten

Do not directly reuse:

- content-item / digest naming
- learning brief buckets
- configured feed scraper logic
- blog-oriented extraction assumptions

Reason:

- football domain is entity-centric, not article-centric

---

## 3. Domain Model Direction

The old project is centered on:

`source content -> digest`

The new project should be centered on:

`raw source -> structured football entities -> reports -> advisor tools`

That means the main objects change from generic content records to domain entities.

### 3.1 Recommended Core Tables

#### `data_sources`

Purpose:

- defines each upstream source

Fields:

- `id`
- `name`
- `base_url`
- `source_type`
- `coverage_type` (`teams`, `players`, `mixed`)
- `reliability_level`
- `enabled`

#### `crawl_runs`

Purpose:

- records each crawl execution

Fields:

- `id`
- `source_id`
- `started_at`
- `finished_at`
- `status`
- `fetched_count`
- `saved_count`
- `error_summary`

#### `raw_documents`

Purpose:

- keeps raw fetched pages or normalized raw text before entity extraction

Fields:

- `id`
- `source_id`
- `external_id`
- `url`
- `document_type`
- `title`
- `raw_text`
- `raw_html`
- `content_hash`
- `fetched_at`

#### `tournaments`

Purpose:

- makes the project reusable beyond one tournament

Fields:

- `id`
- `name`
- `year`
- `host`
- `status`

#### `teams`

Purpose:

- stores team-level identity

Fields:

- `id`
- `tournament_id`
- `name`
- `fifa_code`
- `group_name`
- `confederation`
- `coach_name`

#### `players`

Purpose:

- stores player identity

Fields:

- `id`
- `full_name`
- `birth_date`
- `age_at_tournament`
- `nationality`
- `club_name`
- `club_country`
- `preferred_position`
- `footedness` (optional later)

#### `squad_memberships`

Purpose:

- links players to teams for the tournament squad

Fields:

- `id`
- `tournament_id`
- `team_id`
- `player_id`
- `shirt_number`
- `position_group`
- `is_captain`
- `caps`
- `goals`
- `status`

#### `player_reports`

Purpose:

- AI-enriched player summaries

Fields:

- `id`
- `player_id`
- `source_document_id`
- `summary`
- `strengths`
- `concerns`
- `role_tags`
- `confidence`
- `prompt_version`
- `model_name`
- `created_at`

#### `team_reports`

Purpose:

- AI-enriched team summaries

Fields:

- `id`
- `team_id`
- `summary`
- `style_of_play`
- `strengths`
- `risks`
- `watch_players`
- `prompt_version`
- `model_name`
- `created_at`

#### `advisor_sessions`

Purpose:

- stores multi-turn human-agent interaction threads

Fields:

- `id`
- `title`
- `selected_team_ids`
- `created_at`
- `updated_at`

#### `advisor_messages`

Purpose:

- stores each user/assistant turn inside a saved advisor session
- keeps the turn inspectable instead of only preserving the final answer

Fields:

- `id`
- `session_id`
- `role`
- `content`
- `generated`
- `task_type`
- `task_label`
- `tool_trace`
- `scope_mode`
- `scope_team_ids`
- `scope_team_count`
- `scope_player_count`
- `key_points`
- `cited_team_ids`
- `cited_player_ids`
- `follow_up_suggestions`
- `prompt_version`
- `model_name`
- `created_at`

This is no longer optional in the current project state; it is already part of the working advisor loop.

---

## 4. Data Source Strategy

## 4.1 Current Recommended Source Mix

### Primary source of truth

1. **FIFA official World Cup team/squad pages**
   - best for official team and tournament framing
   - likely strongest source for final squads and official player identity

### Structured fallback / normalization source

2. **Wikipedia squad pages**
   - highly structured squad tables
   - includes position, age, caps, goals, club
   - easier for MVP extraction than many dynamic official pages

### Optional stats expansion source

3. **team/player stats source**
   - only after access stability is confirmed
   - should be treated as an enhancement layer, not the MVP dependency

### 4.2 Practical Source Recommendation

For MVP, do **not** make detailed stat scraping the critical path.

Best MVP path:

- official FIFA for tournament/team grounding
- Wikipedia squad tables for stable structured roster data
- optional later source for richer stats

Reason:

- current sports stats sites often block scraping or are unstable
- we want the MVP to succeed first

### 4.3 Source Risks

#### FIFA pages

- may be dynamic
- page structure may change

#### Wikipedia

- not official source
- may need cleanup and validation

#### third-party stats sites

- anti-bot protection
- legal/terms concerns
- unstable HTML

### 4.4 Conclusion

MVP should be built around:

`FIFA + Wikipedia structured fallback`

and treat richer stats as phase 2.

---

## 5. System Architecture

## 5.1 End-to-End Flow

Recommended full flow:

1. crawl source pages
2. save raw documents
3. parse or AI-extract structured entities
4. upsert normalized team/player/squad records
5. generate AI player/team reports
6. expose advisor tools over the normalized database
7. serve Web pages and chat-style agent interaction

### 5.2 Layered Design

#### Layer A - Source connectors

Responsibilities:

- fetch roster pages
- fetch team pages
- fetch player-related pages where available

Output:

- `RawDocument`

#### Layer B - Extractors / normalizers

Responsibilities:

- turn raw HTML/text into structured entities
- resolve player/team naming consistency
- decide what becomes canonical

Output:

- `TeamRecord`
- `PlayerRecord`
- `SquadMembershipRecord`

#### Layer C - AI enrichment

Responsibilities:

- build readable player reports
- summarize team identity and squad balance
- attach role tags and caution flags

Output:

- `PlayerReport`
- `TeamReport`

#### Layer D - Advisor tools

Responsibilities:

- route the question into a task shape
- prepare scoped comparison / leadership / defensive / attacking / watchlist outputs
- expose inspectable intermediate structures for the agent
- keep later expansion toward explicit tool calls easy

Output:

- structured tool results for agent use
- per-turn execution trace that can be shown in CLI/Web

#### Layer E - Agent interaction layer

Responsibilities:

- interpret user question
- use routed task outputs
- synthesize answer
- support deeper follow-up
- save the turn with route metadata and tool trace

#### Layer F - Web / API layer

Responsibilities:

- pipeline controls
- team/player inspection
- advisor chat page

---

## 6. Agent Design

## 6.1 Why This Can Become A Real Agent Project

Unlike the learning tracker, this project can more naturally become agentic because the user decisions are richer:

- compare players
- compare teams
- explain strengths/weaknesses
- build shortlists
- answer follow-up questions
- adapt to user intent

### 6.2 Advisor Agent Current Goal

The current agent answers:

> given the stored teams, players, and AI reports, what should the user focus on or conclude?

Example requests:

- Give me a quick way to understand Japan's squad.
- Compare Argentina and France at forward depth.
- Build a watchlist of breakout midfielders from non-favorites.
- Which team looks most balanced based on squad structure?

The current implementation already includes:

- persistent saved sessions
- preset-driven tasks
- heuristic task routing for free-text questions
- per-turn tool traces shown in CLI and Web

### 6.3 Current Internal Tool Shapes

Current routed tool families:

#### `compare_teams`

- prepares side-by-side team cards
- useful for balance, structure, experience, and broad verdict questions

#### `leadership_spine`

- prepares veteran/core leader views by position and captaincy
- useful for captaincy, seniority, and spine questions

#### `defensive_review`

- prepares goalkeeper + defender focused cards and risk signals
- useful for goalkeeper reliability and defensive stability questions

#### `attacking_core`

- prepares scorer / creator / depth focused cards and dependency signals
- useful for forward depth, goal production, and attack concentration questions

#### `build_watchlist`

- prepares ranked watchlist candidates across the scoped teams
- useful for study priority and watchlist questions

### 6.4 Future Explicit Tool Interfaces

Next-step candidate tool interfaces:

#### `search_teams(query: str) -> list[TeamResult]`

Find likely teams.

#### `get_team_squad(team_id: str) -> TeamSquadView`

Return roster with positions, caps, club, and report snippets.

#### `search_players(query: str, team_id: str | None = None, position: str | None = None) -> list[PlayerResult]`

Find players.

#### `get_player_profile(player_id: str) -> PlayerProfileView`

Return identity + report + squad context.

#### `compare_players(player_ids: list[str], context: str) -> ComparisonResult`

Used by the agent for targeted comparison.

#### `get_team_report(team_id: str) -> TeamReportView`

Return AI-enriched team summary.

#### `find_position_depth(position_group: str, limit: int = 10) -> list[DepthResult]`

Useful for questions like full-back depth or striker depth.

#### `build_watchlist(criteria: str, limit: int = 8) -> WatchlistResult`

Can initially be implemented as agent + search + ranking.

### 6.5 Agent Memory

For v1:

- no complex long-term memory required
- keep lightweight session context only

For v2:

- store user preferences:
  - favorite teams
  - desired depth of analysis
  - creator / fan / analyst persona

---

## 7. Web MVP Design

### 7.1 Pages

#### `/`

Dashboard / overview:

- tournament snapshot
- teams count
- players count
- latest crawl/extract run
- quick links

#### `/teams`

Team list with:

- name
- group
- coach
- roster size
- quick summary

#### `/teams/{team_id}`

Team detail:

- roster table
- team report
- watch players
- squad balance view

#### `/players`

Player search/list

#### `/players/{player_id}`

Player detail:

- identity
- club
- role
- report
- team membership

#### `/pipeline`

Pipeline controls:

- crawl selected sources
- extract/update normalized entities
- generate reports

#### `/advisor`

Interactive advisor page:

- user question
- candidate scope control
- answer
- task route
- tool trace
- linked records used in answer

### 7.2 UI Positioning

This should not feel like a toy chatbot.

It should feel like:

> a football intelligence workbench

So the UI emphasis should be:

- tables
- comparison
- inspectability
- linked evidence

---

## 8. Interface Predesign

## 8.1 Connector Interface

```python
class SourceConnector(Protocol):
    def list_targets(self) -> list[dict]: ...
    def fetch_document(self, target: dict) -> dict: ...
```

Example output:

```python
{
    "external_id": "...",
    "url": "...",
    "title": "...",
    "document_type": "team_page",
    "raw_html": "...",
    "raw_text": "...",
}
```

## 8.2 Normalizer Interface

```python
def extract_squad_entities(raw_document_id: str) -> dict:
    ...
```

Example output:

```python
{
    "team": {...},
    "players": [...],
    "memberships": [...],
}
```

## 8.3 AI Report Interface

```python
def generate_player_report(player_id: str) -> dict: ...
def generate_team_report(team_id: str) -> dict: ...
```

## 8.4 Advisor Interface

```python
def answer_advisor_question(question: str, scope: dict | None = None) -> dict: ...
```

Example output:

```python
{
    "answer": "...",
    "used_teams": [...],
    "used_players": [...],
    "used_reports": [...],
    "follow_up_suggestions": [...],
}
```

## 8.5 Web Route Predesign

```text
GET  /                    dashboard
GET  /teams               team list
GET  /teams/{team_id}     team detail
GET  /players             player list/search
GET  /players/{player_id} player detail
GET  /pipeline            pipeline controls
POST /pipeline/crawl
POST /pipeline/extract
POST /pipeline/reports
GET  /advisor             advisor page
POST /advisor             advisor interaction
```

## 8.6 Repository Predesign

Suggested repository methods:

```python
save_raw_document(...)
upsert_team(...)
upsert_player(...)
upsert_squad_membership(...)
save_player_report(...)
save_team_report(...)
get_team_by_code(...)
get_team_squad(...)
get_player_by_name(...)
search_players(...)
get_recent_crawl_runs(...)
```

---

## 9. Task Breakdown

## Phase 0 - Scope Lock

Deliverables:

- confirm tournament assumption
- confirm MVP data source mix
- confirm decision-support scenarios

## Phase 1 - Project Scaffold

Deliverables:

- new project folder
- `uv` project init
- basic app structure
- database connection
- empty tables

## Phase 2 - Raw Crawl Pipeline

Deliverables:

- source config
- FIFA connector
- Wikipedia connector
- raw document storage
- crawl run logging

## Phase 3 - Entity Extraction / Normalization

Deliverables:

- squad extraction flow
- team / player / membership upsert
- first inspectable data pages

## Phase 4 - AI Enrichment

Deliverables:

- player report prompt
- team report prompt
- batch generation scripts
- report inspection page

## Phase 5 - Advisor Agent v1

Deliverables:

- internal tool layer
- advisor agent
- `/advisor` page
- explainable linked answers

## Phase 6 - Comparison and Decision UX

Deliverables:

- compare teams
- compare players
- watchlist builder
- saved scenarios or presets

## Phase 7 - Hardening

Deliverables:

- source health checks
- basic tests
- crawl retry/error handling
- demo polish

---

## 10. MVP Recommendation

To maximize success, the first true MVP should be:

1. 8-12 teams fully ingested
2. official + structured fallback source path working
3. normalized team/player/squad data visible in Web pages
4. AI team/player reports generated
5. advisor can answer comparison and watchlist questions

That is enough to make it feel like a real agent-assisted product.

---

## 11. Key Risks

### Risk 1 - Source instability

Mitigation:

- use fallback source mix
- save raw documents
- avoid binding MVP to one fragile stats site

### Risk 2 - Too much scope

Mitigation:

- lock MVP to squads + player profiles + advisor
- do not chase live match analytics first

### Risk 3 - Fake agent feel

Mitigation:

- build real internal tools
- make answers reference stored teams/players/reports
- keep inspectable evidence links

### Risk 4 - AI hallucination on player style

Mitigation:

- only summarize from stored source evidence
- expose confidence / evidence source
- prefer conservative reports

---

## 12. Recommended Immediate Next Step

The project has already moved well beyond scaffold and first advisor chat.

Best next step from the current state:

1. deepen the internal advisor tools so routing is backed by more explicit analysis helpers
2. add more preset families around midfield control, defensive depth, and shortlist generation
3. expand source coverage beyond the first Wikipedia-driven path while preserving traceable evidence

That keeps the project moving from:

> grounded single-prompt advisor

toward:

> inspectable football intelligence workbench with clearer internal tools
