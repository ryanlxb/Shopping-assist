# STORY-004: 淘宝/天猫平台接入

| Field | Value |
|-------|-------|
| ID | STORY-004 |
| Status | Draft |
| Priority | P2 |
| Release | 0.0.1 |

- **Priority Score**: 1.25 (Impact 5 / Effort 4)
- **Dependencies**: STORY-003 (PlatformScraper Protocol — 已完成)

## Background

STORY-001 实现了京东平台的商品搜索与配料表提取。STORY-003 抽象了 PlatformScraper 协议。本 Story 在此基础上接入淘宝/天猫平台，实现第二个平台的商品搜索和配料表提取，使用户能同时获取两个主流电商平台的数据。

淘宝的反爬策略比京东更严格（登录墙、滑块验证），因此本 Story 优先实现天猫（tmall.com）搜索，其反爬门槛略低于淘宝主站。

## Requirements

### R1: TBScraper 实现 PlatformScraper 协议 (MUST)
- 系统 MUST 新建 `src/scraper/tb.py`，实现 `TBScraper` 类
- `TBScraper` MUST 实现 `PlatformScraper` 协议的所有方法
- `TBScraper.platform_name` MUST 为 `"tb"`
- `TBScraper` MUST 通过 `@register_platform("tb")` 注册到平台注册表

### R2: 天猫商品搜索 (MUST)
- 系统 MUST 使用 Playwright (stealth 模式) 访问天猫搜索页
- 搜索 URL 格式: `https://list.tmall.com/search_product.htm?q={keyword}`
- 系统 MUST 提取商品列表中的元数据：商品名称、价格、店铺名称、商品链接、缩略图
- 系统 MUST 实现与京东相同的反爬策略（随机延迟、UA 轮换、Cookie 持久化）
- Cookie 保存路径: `data/cookies/tb_cookies.json`

### R3: 天猫详情页解析 (MUST)
- 系统 MUST 进入商品详情页，尝试提取配料表文本或图片
- 天猫详情页结构与京东不同，MUST 有独立的解析逻辑
- 系统 MUST 在 `src/scraper/tb_parser.py` 中实现天猫 HTML 解析

### R4: 搜索服务平台选择 (MUST)
- `POST /search` 路由 MUST 支持平台选择参数（默认京东）
- 搜索表单 MUST 提供平台下拉选择（京东 / 天猫）
- `SearchService` MUST 根据平台参数使用对应的 scraper

### R5: 结果页平台标识 (MUST)
- 搜索结果页 MUST 展示每个商品的来源平台（京东/天猫）
- 系统 SHOULD 为不同平台使用不同颜色标识

## Acceptance Criteria

### AC1: 天猫搜索
- **Given** 用户在搜索页选择"天猫"平台
- **When** 输入关键词"NFC果汁"并搜索
- **Then** 系统从天猫获取商品列表，结果保存到数据库，platform 字段为 "tb"

### AC2: TBScraper 协议兼容
- **Given** `TBScraper` 已实现
- **When** 使用 `isinstance` 检查
- **Then** `TBScraper` 是 `PlatformScraper` 的实例

### AC3: 平台注册
- **Given** `TBScraper` 已注册
- **When** 调用 `get_scraper("tb")`
- **Then** 返回 `TBScraper` 实例

### AC4: 搜索表单平台选择
- **Given** 用户在搜索首页
- **When** 查看搜索表单
- **Then** 存在平台选择下拉框，包含"京东"和"天猫"选项

### AC5: 结果页平台标识
- **Given** 搜索结果包含天猫商品
- **When** 查看结果页
- **Then** 每个商品旁显示平台标签（"京东"或"天猫"）

## Out of Scope

- 不做淘宝主站搜索（仅天猫）
- 不做跨平台同时搜索（一次搜索只选一个平台）
- 不做登录态管理（不需要登录淘宝账号）

## Security Scope
| Check | Applicable | Reason |
|-------|------------|--------|
| SEC-1 | Yes | 新增源代码 |
| SEC-2 | Yes | 新增平台选择表单字段 |
| SEC-3 | Yes | 新增数据写入 |
| SEC-4 | Yes | 新增模板渲染 |
| SEC-5 | N/A | 无认证 |
| SEC-6 | Yes | 修改现有路由参数 |
| SEC-7 | Yes | 新增爬虫异常处理 |
| SEC-8 | No | 无新依赖 |
