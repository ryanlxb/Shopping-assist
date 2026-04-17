# Project Context (Auto-generated)
> Last updated: 2026-04-17T00:00:00+08:00 by manual

## Sprint Status
In Progress: 0 | Backlog: 0 | Done: 11

## Current Stories
None — 全部 Story 已完成。v0.1.0 已发布。

## Recent Completions
- **STORY-011**: 基于配料偏好的商品推荐
- **STORY-008**: 历史价格追踪与趋势图
- **STORY-007**: 跨平台商品比价视图

## Active Branches
- `main` (tag: v0.1.0)

## Key Decisions
- 技术栈：Python 3.11+ / FastAPI / Jinja2 + TailwindCSS / SQLite / SQLAlchemy 2.0
- PlatformScraper Protocol 多平台扩展架构
- 配料知识库内置 30+ 常见添加剂安全评级
- 配料评分 = 白名单命中数 - 黑名单命中数
- Docker 部署：SQLite + 图片通过 volume 挂载持久化 (/app/data)
- 所有配置通过 SA_ 前缀环境变量覆盖

## Next Recommended Action
v0.1.0 已发布。建议：
- `docker compose up -d` 启动本地部署
- 真实场景验收，收集使用反馈
- 规划 v0.2.0 需求
