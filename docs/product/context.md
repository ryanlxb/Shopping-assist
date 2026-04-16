# Project Context (Auto-generated)
> Last updated: 2026-04-16T00:00:00+08:00 by /project-done

## Sprint Status
In Progress: 0 | Backlog: 0 | Done: 1

## Current Stories
None — all stories completed.

## Recent Completions
- **STORY-001**: MVP 核心闭环 — 京东商品搜索与配料表智能提取 (commit e8c4ae2)

## Active Branches
- `main` (initial commit)

## Key Decisions
- 技术栈：Python 3.11+ / FastAPI / Jinja2 + TailwindCSS / SQLite / SQLAlchemy 2.0
- 爬虫方案：Playwright stealth 模式，低频访问（1次/天）
- OCR 方案：Qwen2.5-VL via Ollama 本地运行
- MVP 聚焦京东平台，淘宝留作后续迭代
- Starlette 1.0 的 TemplateResponse 签名：request 为第一个位置参数

## Next Recommended Action
`/project-design` — 规划下一阶段功能（淘宝平台支持、历史价格追踪、推荐算法等）
