# STORY-003: 平台适配器抽象层 — 统一爬虫接口

| Field | Value |
|-------|-------|
| ID | STORY-003 |
| Status | Draft |
| Priority | P2 |
| Release | 0.0.1 |

- **Priority Score**: 2.0 (Impact 4 / Effort 2)

## Background

当前 `JDScraper` 直接耦合在 `SearchService` 中。为了后续接入淘宝等其他平台（STORY-004），需要抽象出平台适配器接口，让搜索服务通过统一接口调用不同平台的爬虫。这是一个纯重构 Story，不改变现有功能行为。

## Requirements

### R1: 平台适配器协议 (MUST)
- 系统 MUST 定义 `PlatformScraper` 抽象基类/协议（Protocol）
- 协议 MUST 包含以下方法签名：
  - `async search(keyword: str, limit: int) -> list[dict]`
  - `async get_detail(product_url: str) -> dict`
  - `async download_images(image_urls: list[str], product_id: str) -> list[str]`
  - `async close()`
- 协议 MUST 定义 `platform_name: str` 属性

### R2: 京东爬虫适配 (MUST)
- 现有 `JDScraper` MUST 实现 `PlatformScraper` 协议
- 重构 MUST NOT 改变 `JDScraper` 的任何外部行为
- 所有现有测试 MUST 继续通过

### R3: 搜索服务重构 (MUST)
- `SearchService` MUST 接受 `PlatformScraper` 类型而非 `JDScraper` 具体类型
- `SearchService` MUST 将 `platform` 字段从硬编码 `"jd"` 改为从 scraper 的 `platform_name` 获取
- 系统 SHOULD 支持同时搜索多个平台（接受 scraper 列表）

### R4: 平台注册机制 (SHOULD)
- 系统 SHOULD 提供平台注册表（如 dict），允许按名称查找平台 scraper
- 系统 SHOULD 在配置中指定启用的平台列表

## Acceptance Criteria

### AC1: 协议兼容
- **Given** `JDScraper` 已实现 `PlatformScraper` 协议
- **When** 使用 `isinstance` 或 `runtime_checkable` 检查
- **Then** `JDScraper` 是 `PlatformScraper` 的实例

### AC2: 行为不变
- **Given** 重构完成
- **When** 运行全部现有测试
- **Then** 34 个测试全部通过，无回归

### AC3: 多平台扩展
- **Given** 存在一个 mock 的 `FakeScraper` 实现 `PlatformScraper`
- **When** `SearchService` 使用 `FakeScraper`
- **Then** 搜索流程正常执行，product 的 platform 字段为 `FakeScraper.platform_name`

## Out of Scope

- 不实现淘宝爬虫（STORY-004）
- 不改变现有 UI

## Security Scope
| Check | Applicable | Reason |
|-------|------------|--------|
| SEC-1 | Yes | 重构源代码 |
| SEC-2 | No | 无输入变更 |
| SEC-3 | No | 无查询变更 |
| SEC-4 | No | 无模板变更 |
| SEC-5 | N/A | 无认证 |
| SEC-6 | No | 无新端点 |
| SEC-7 | No | 无错误处理变更 |
| SEC-8 | No | 无新依赖 |
