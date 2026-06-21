# Phase 1 Scaffold Plan

## Goal

把 `world-cup-squad-advisor-lab/` 从“方向文档”推进到“可以启动、可以连库、可以建空表、可以起最小 Web 页”的状态。

这一阶段先不写真正的抓取器，也先不做 Agent 对话。重点是把后面所有能力依赖的骨架搭好。

完成标志：

1. `uv` 项目初始化完成
2. 依赖安装完成
3. `app/` 分层骨架建立
4. PostgreSQL 连接能通
5. 第一批核心表能创建
6. FastAPI 最小页面能启动

---

## 本阶段锁定的产品假设

当前先按这组假设执行，不再反复摇摆：

- 赛事范围：`men's FIFA World Cup 2026`
- 产品定位：`球队 / 球员决策辅助系统`
- MVP 用户场景：
  - 快速理解一支球队
  - 对比两支球队或几名球员
  - 根据条件生成 watchlist
- MVP 数据源策略：
  - 官方 grounding：`FIFA team / tournament pages`
  - 结构化 roster 主力来源：`Wikipedia squads page`

说明：

- 我刚核实过，`FIFA World Cup 2026™ Teams` 官方页当前可访问，且 FIFA 还有一篇关于已确认大名单的文章；同时 Wikipedia 也存在 `2026 FIFA World Cup squads` 页面，并且页面正文明确说明了本届赛事与 squad 列结构，适合作为 MVP 的结构化入口。来源见文末。

---

## 复用旧项目的边界

这次继续坚持一句话：

> 复用骨架，不复用旧业务语义。

### 可以直接借用的思路

- `app/database/connection.py`
- `app/database/create_tables.py`
- `Repository` 数据访问层
- `app/web/main.py` + `app/web/routes.py`
- service 层 orchestration 风格
- Pydantic 结构化输出模式

### 必须重写的部分

- 所有 `content_items / digests` 命名
- 抓取器接口和数据对象
- 摘要 prompt
- advisor 工具层
- Web 页面文案和展示模型

---

## 先建什么，不先建什么

### 这阶段要建

- Python 工程
- 数据库连接
- 模型定义
- 建表脚本
- 最小仓库层
- 最小 Web 应用壳子
- 源配置文件壳子

### 这阶段不要建

- 真正的 FIFA / Wikipedia 抓取逻辑
- AI 结构化提取
- 球员 / 球队报告生成
- Agent 多轮记忆
- 花哨前端

原因很简单：

现在最值钱的是先把“后面所有东西落脚在哪里”确定下来。

---

## 初始目录建议

```text
world-cup-squad-advisor-lab/
├─ app/
│  ├─ __init__.py
│  ├─ database/
│  │  ├─ connection.py
│  │  ├─ models.py
│  │  ├─ create_tables.py
│  │  └─ repository.py
│  ├─ domain/
│  │  ├─ __init__.py
│  │  └─ records.py
│  ├─ services/
│  │  ├─ __init__.py
│  │  ├─ seed_sources.py
│  │  └─ show_counts.py
│  ├─ agent/
│  │  └─ __init__.py
│  └─ web/
│     ├─ __init__.py
│     ├─ main.py
│     ├─ routes.py
│     ├─ viewmodels.py
│     ├─ templates/
│     │  ├─ base.html
│     │  └─ dashboard.html
│     └─ static/
│        └─ css/
│           └─ app.css
├─ config/
│  └─ sources.toml
├─ docker/
│  └─ docker-compose.yml
├─ docs/
│  ├─ ARCHITECTURE_PLAN.md
│  ├─ DB_SCHEMA_V1.md
│  └─ PHASE1_SCAFFOLD_PLAN.md
├─ .env.example
├─ main.py
├─ pyproject.toml
└─ PROJECT_BUILD_LOG.md
```

---

## Phase 1 具体执行顺序

## Step 1 - 初始化工程

你自己执行：

```powershell
cd C:\Users\Administrator\Documents\news-aggregation-project\world-cup-squad-advisor-lab
uv init .
```

然后把项目描述改成和本项目一致。

建议第一批依赖：

```powershell
uv add fastapi uvicorn sqlalchemy psycopg2-binary python-dotenv jinja2 pydantic requests beautifulsoup4 lxml
```

现在先不急着装 OpenAI SDK。它属于 Phase 4。

为什么：

- 这一步只搭骨架
- HTML 解析先用 `BeautifulSoup + lxml`
- 这样比一上来堆太多库更稳

---

## Step 2 - 建最小包结构

先把 `app/database`、`app/services`、`app/web`、`config`、`docker` 建起来。

这一层的学习重点不是“文件多”，而是理解分层：

- `database/` 管“怎么存、怎么查”
- `services/` 管“怎么串流程”
- `web/` 管“怎么给页面”
- `config/` 管“哪些源被启用”

---

## Step 3 - 先做数据库连接

先只做这些内容：

- `get_database_url()`
- `engine`
- `SessionLocal`
- `get_session()`

环境变量建议：

```text
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=world_cup_squad_advisor_lab
```

这里先沿用你已经熟悉的模式，不要在新项目第一天切换到更复杂的配置管理。

---

## Step 4 - 建第一批表

这一步先建“数据落点”，不建业务逻辑。

第一批表建议：

- `data_sources`
- `crawl_runs`
- `raw_documents`
- `tournaments`
- `teams`
- `players`
- `squad_memberships`

`player_reports` 和 `team_reports` 先写进设计文档，但可以在 Phase 4 再真正落库。

为什么这样切：

- 你当前真正要先证明的是“抓到东西以后，往哪里放”
- report 表太早建，会让理解成本一下变高

---

## Step 5 - 建表脚本

目标非常朴素：

```powershell
uv run python -m app.database.create_tables
```

跑完之后，你能回答：

- 是哪几个模型类参与了建表
- `Base.metadata.create_all(bind=engine)` 为什么知道要建哪些表
- 为什么 PostgreSQL 和 SQLite 打印出的 SQL 方言会不同

---

## Step 6 - 做最小 Repository

这阶段不要把 repository 写成“大而全工具箱”。

只保留最值得有的最小方法：

- `upsert_data_source(...)`
- `create_crawl_run(...)`
- `save_raw_document(...)`
- `upsert_tournament(...)`
- `upsert_team(...)`
- `upsert_player(...)`
- `upsert_squad_membership(...)`
- `get_team_count()`
- `get_player_count()`

你会发现，这和旧项目一样，repository 的价值不是“高级”，而是让 service 不直接操作 session 细节。

---

## Step 7 - 起最小 Web 壳子

第一版 Web 不追求好看，只追求可见：

- `/` 展示项目名
- 显示 teams / players / raw_documents 数量
- 显示“当前还没有抓取数据”也没关系

这样后面每做完一段后端，都能立刻在页面里看到结果。

---

## Step 8 - 准备源配置壳子

第一版 `config/sources.toml` 先只写 2 个源：

- `fifa_teams`
- `wikipedia_world_cup_squads`

建议字段：

- `id`
- `name`
- `source_type`
- `base_url`
- `enabled`
- `notes`

此时还不需要把每个球队 target 全写进去。

---

## 学习重点

本阶段你要掌握的不是“足球业务”，而是这 4 个基础概念：

1. 为什么先存 `raw_documents`，再变成 `teams / players`
2. 为什么 `squad_memberships` 必须单独成表
3. 为什么 Web 页面先只读数据库，不直接去抓网页
4. 为什么这次的核心对象不再是 `content -> digest`

如果这 4 个点清楚，后面 Phase 2 和 Phase 3 会顺很多。

---

## Git 检查点建议

建议仍然维持你之前的节奏：

### Checkpoint A

完成：

- `uv init`
- `pyproject.toml`
- 目录骨架

建议 commit：

```text
init world-cup squad advisor lab scaffold
```

### Checkpoint B

完成：

- `connection.py`
- `models.py`
- `create_tables.py`

建议 commit：

```text
add initial database schema for squad advisor
```

### Checkpoint C

完成：

- `repository.py`
- `web/main.py`
- `web/routes.py`
- 最小模板

建议 commit：

```text
add minimal dashboard shell for squad advisor
```

---

## Phase 1 完成后的理解门槛

进入下一阶段前，你至少要能自己回答：

1. 这个项目里什么是原始证据，什么是结构化实体？
2. 为什么 `players` 和 `teams` 不能直接替代 `raw_documents`？
3. `squad_memberships` 的输入是什么，输出是什么？
4. `repository` 解决的到底是什么问题？
5. 如果现在完全没有爬虫，Web 首页为什么仍然值得先搭出来？

---

## 下一阶段预告

Phase 2 不会先做“全量抓取”，而会先做一个最稳的小闭环：

> 选一个 Wikipedia squad 页面目标，抓 1 页，保存 1 条 raw document，再从这 1 条里抽出 1 支球队和若干球员。

这样成本最小，学习信号最强。

---

## References

- FIFA official teams directory: https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/teams
- FIFA World Cup 2026 official tournament page: https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026
- Wikipedia squads page: https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_squads
