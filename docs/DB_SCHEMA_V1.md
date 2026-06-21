# Database Schema V1

## 设计原则

这次数据库不再围绕“文章摘要”建，而是围绕“实体 + 证据 + 报告”建。

一句话版：

```text
source page -> raw_document -> normalized entities -> AI reports -> advisor tools
```

其中：

- `raw_documents` 是证据层
- `teams / players / squad_memberships` 是实体层
- `player_reports / team_reports` 是 AI 加工层

---

## 为什么这次要这样建

旧项目的核心对象是：

```text
content_item -> digest
```

因为旧项目的最终产品就是“读内容摘要”。

这次不是。

这次最终产品是：

- 看球队
- 看球员
- 做比较
- 做 watchlist
- 跟 agent 深度互动

所以核心对象必须换成：

- team
- player
- squad membership

---

## 表分批落地策略

## 第一批就建

- `data_sources`
- `crawl_runs`
- `raw_documents`
- `tournaments`
- `teams`
- `players`
- `squad_memberships`

## 第二批再建

- `player_reports`
- `team_reports`

## 先不建

- `advisor_sessions`
- `advisor_messages`
- `player_aliases`
- `match_events`

原因：

先把抓取、规范化、可查询实体打通，再引入 AI enrich 和会话历史。

---

## ID 策略

为了便于学习和调试，V1 优先使用 **可读字符串主键**。

推荐：

- `tournaments.id = "fifa-world-cup-2026"`
- `data_sources.id = "fifa_teams"`
- `teams.id = "fifa-world-cup-2026:argentina"`
- `players.id = "fifa-world-cup-2026:argentina:lionel-messi"`
- `squad_memberships.id = "fifa-world-cup-2026:argentina:lionel-messi"`

这样做的好处：

- 查询数据库时一眼能看懂
- 跟你现在的学习方式更契合
- 暂时不需要额外解释 UUID

代价：

- 跨来源球员身份合并没有那么优雅

这个代价在 MVP 阶段可以接受。

---

## 关系总览

```text
data_sources 1 --- n crawl_runs
data_sources 1 --- n raw_documents

tournaments 1 --- n teams
tournaments 1 --- n squad_memberships

teams 1 --- n squad_memberships
players 1 --- n squad_memberships

raw_documents 1 --- n squad_memberships   (可选，用于追溯抽取来源)

players 1 --- 1 player_reports           (Phase 4)
teams   1 --- 1 team_reports             (Phase 4)
```

---

## Table 1 - data_sources

用途：

- 描述有哪些上游源
- 不直接存抓到的内容

建议字段：

| field | type | notes |
|---|---|---|
| id | String PK | 例如 `fifa_teams` |
| name | String | 展示名 |
| base_url | String | 源站根地址 |
| source_type | String | `official` / `wikipedia` / `stats` |
| coverage_type | String | `teams` / `players` / `mixed` |
| reliability_level | String | `high` / `medium` / `low` |
| enabled | Boolean | 是否启用 |
| created_at | DateTime | 创建时间 |

约束建议：

- `id` 主键

---

## Table 2 - crawl_runs

用途：

- 每次 crawl 都留痕
- 后面排查“这批数据是哪次抓来的”靠它

建议字段：

| field | type | notes |
|---|---|---|
| id | String PK | 例如 `crawl:2026-06-20T20-15-00:fifa_teams` |
| source_id | String FK | 指向 `data_sources.id` |
| target_key | String nullable | 本次抓取的具体目标，例如 `group-a` 或 `team:argentina` |
| status | String | `started` / `success` / `failed` |
| fetched_count | Integer | 抓了多少目标 |
| saved_count | Integer | 保存了多少 raw documents |
| error_summary | Text nullable | 错误摘要 |
| started_at | DateTime | 开始时间 |
| finished_at | DateTime nullable | 结束时间 |

约束建议：

- `source_id` 外键到 `data_sources`

---

## Table 3 - raw_documents

用途：

- 保存网页原文、解析前文本、追溯证据
- 这是后面 AI 提取和 debug 的基础

建议字段：

| field | type | notes |
|---|---|---|
| id | String PK | 内部主键 |
| source_id | String FK | 指向 `data_sources.id` |
| crawl_run_id | String FK nullable | 指向 `crawl_runs.id` |
| external_id | String | 该页面在当前 source 下的稳定标识 |
| url | String | 原始 URL |
| document_type | String | `teams_index` / `team_page` / `squad_page` |
| title | String nullable | 页面标题 |
| raw_html | Text nullable | 原始 HTML |
| raw_text | Text nullable | 清洗后的正文文本 |
| content_hash | String nullable | 去重或变更检测 |
| fetched_at | DateTime | 抓取时间 |

约束建议：

- `source_id` 外键到 `data_sources`
- `crawl_run_id` 外键到 `crawl_runs`
- 唯一约束：`(source_id, external_id)`

为什么 `raw_html` 和 `raw_text` 都想留：

- `raw_html` 便于重新解析
- `raw_text` 便于 LLM 或人工直接查看

---

## Table 4 - tournaments

用途：

- 把项目从“一次性的脚本”提升为可扩展产品
- 后面换成别的赛事时不至于重做表结构

建议字段：

| field | type | notes |
|---|---|---|
| id | String PK | `fifa-world-cup-2026` |
| name | String | 展示名 |
| year | Integer | 2026 |
| host | String | `Canada / Mexico / United States` |
| status | String | `upcoming` / `ongoing` / `finished` |

---

## Table 5 - teams

用途：

- 存球队主实体

建议字段：

| field | type | notes |
|---|---|---|
| id | String PK | `fifa-world-cup-2026:argentina` |
| tournament_id | String FK | 指向 `tournaments.id` |
| name | String | 球队名 |
| fifa_code | String nullable | 例如 `ARG` |
| group_name | String nullable | 例如 `Group J` |
| confederation | String nullable | 例如 `CONMEBOL` |
| coach_name | String nullable | 主教练 |
| official_page_url | String nullable | 官方页 |
| created_at | DateTime | 创建时间 |

约束建议：

- `tournament_id` 外键到 `tournaments`
- 唯一约束：`(tournament_id, name)`

---

## Table 6 - players

用途：

- 存球员身份主实体

建议字段：

| field | type | notes |
|---|---|---|
| id | String PK | 可读主键 |
| full_name | String | 球员姓名 |
| normalized_name | String | 方便检索和去重 |
| birth_date | String nullable | MVP 先允许字符串，后面可升级为 Date |
| nationality | String nullable | 国籍 |
| club_name | String nullable | 所属俱乐部 |
| club_country | String nullable | 俱乐部所属协会 |
| preferred_position | String nullable | 主位置 |
| profile_source_url | String nullable | 参考页 |
| created_at | DateTime | 创建时间 |

为什么 `birth_date` 先允许 String：

- MVP 阶段先优先打通抽取流程
- 不同源的日期格式可能不同
- 后面如果稳定，再统一为真正的 `Date`

---

## Table 7 - squad_memberships

用途：

- 这是最关键的一张关系表
- 负责把“球员属于哪支队、在这届赛事扮演什么角色”表达出来

建议字段：

| field | type | notes |
|---|---|---|
| id | String PK | 可直接复用组合键风格 |
| tournament_id | String FK | 指向 `tournaments.id` |
| team_id | String FK | 指向 `teams.id` |
| player_id | String FK | 指向 `players.id` |
| source_document_id | String FK nullable | 指向 `raw_documents.id` |
| shirt_number | Integer nullable | 球衣号码 |
| position_group | String nullable | `GK` / `DF` / `MF` / `FW` |
| caps | Integer nullable | 国家队出场 |
| goals | Integer nullable | 国家队进球 |
| is_captain | Boolean | 是否队长 |
| status | String | `active` / `replaced` / `withdrawn` |
| created_at | DateTime | 创建时间 |

约束建议：

- `tournament_id` 外键到 `tournaments`
- `team_id` 外键到 `teams`
- `player_id` 外键到 `players`
- `source_document_id` 外键到 `raw_documents`
- 唯一约束：`(tournament_id, team_id, player_id)`

为什么必须单独成表：

- 同一个球员以后可能出现在不同赛事
- 同一个球员的 caps / goals / shirt number 是“这次名单上下文里的属性”
- 这些字段不应该硬塞到 `players` 表里

---

## Phase 4 再加的表

## Table 8 - player_reports

建议采用“一对一复用主键”模式：

| field | type | notes |
|---|---|---|
| player_id | String PK + FK | 指向 `players.id` |
| summary | Text | 面向用户的球员摘要 |
| strengths | Text nullable | 强项 |
| concerns | Text nullable | 风险或注意点 |
| role_tags | Text nullable | 先存逗号分隔或 JSON 字符串 |
| evidence_note | Text nullable | 摘要依赖了哪些证据 |
| prompt_version | String nullable | prompt 版本 |
| model_name | String nullable | 模型名 |
| created_at | DateTime | 生成时间 |

为什么这样设计：

- 和你已经学过的 `Digest.id = ForeignKey(...) + primary_key=True` 很像
- 一名球员当前只保留一份最新报告，最适合 MVP

## Table 9 - team_reports

同理：

| field | type | notes |
|---|---|---|
| team_id | String PK + FK | 指向 `teams.id` |
| summary | Text | 球队概览 |
| style_of_play | Text nullable | 风格描述 |
| strengths | Text nullable | 主要强项 |
| risks | Text nullable | 风险点 |
| watch_players | Text nullable | 建议重点关注球员 |
| evidence_note | Text nullable | 来源说明 |
| prompt_version | String nullable | prompt 版本 |
| model_name | String nullable | 模型名 |
| created_at | DateTime | 生成时间 |

---

## V1 的刻意简化

这里有几处是我故意保守处理的：

1. `players.birth_date` 先不急着强制成真正日期类型
2. 不提前做复杂 alias / identity resolution
3. 不提前做 stats fact tables
4. 不提前做聊天消息持久化

这些不是“不重要”，而是现在做会把你拖进更重的建模泥潭。

---

## 你现在最该理解的 3 件事

1. 为什么 `raw_documents` 是证据层，不是垃圾桶
2. 为什么 `squad_memberships` 比 `players` 本身更接近业务核心
3. 为什么 `player_reports / team_reports` 最适合一对一表，而不是直接塞回实体表

---

## 下一步衔接

这个 schema 文档的直接用途，不是收藏，而是马上指导你写：

- `app/database/models.py`
- `app/database/create_tables.py`
- `app/database/repository.py`

下一步应该先把第一批 7 张表真的写成 SQLAlchemy 模型。
