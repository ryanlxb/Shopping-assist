# Test Cases: STORY-003

## TC-001: PlatformScraper 协议定义 (AC1)
**Given** `PlatformScraper` 协议已定义于 `src/scraper/platform.py`
**When** 使用 `@runtime_checkable` 检查
**Then** 协议包含 `platform_name`、`search()`、`get_detail()`、`download_images()`、`close()` 方法签名

## TC-002: JDScraper 协议兼容 (AC1)
**Given** `JDScraper` 已实现 `PlatformScraper` 协议
**When** `isinstance(JDScraper(), PlatformScraper)` 检查
**Then** 返回 True

## TC-003: 行为不变 / 回归测试 (AC2)
**Given** 重构完成
**When** 运行全部现有测试
**Then** 所有测试通过，无回归

## TC-004: SearchService 使用协议类型 (AC3)
**Given** `SearchService` 接受 `PlatformScraper` 类型
**When** 传入一个 mock 的 FakeScraper 实现
**Then** 搜索流程正常执行，product 的 platform 字段来自 scraper 的 `platform_name`

## TC-005: 平台注册表 (AC3)
**Given** 注册表 `PLATFORM_REGISTRY` 存在
**When** 调用 `get_scraper("jd")`
**Then** 返回 `JDScraper` 实例
**When** 调用 `get_scraper("unknown_platform")`
**Then** 抛出 `KeyError`
