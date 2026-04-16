# STORY-002: 修复 P1 — URL 编码 + N+1 查询 + 路径安全

| Field | Value |
|-------|-------|
| ID | STORY-002 |
| Status | Draft |
| Priority | P1 |
| Release | 0.0.1 |

- **Priority Score**: 4.0 (Impact 4 / Effort 1)

## Background

STORY-001 的 QA Check 阶段发现了 2 个 P1 和 1 个 P2 问题，需要立即修复。

## Requirements

### R1: URL 编码 (MUST)
- `src/scraper/jd.py:82` 中的 `keyword` 参数 MUST 使用 `urllib.parse.quote()` 进行 URL 编码后再拼接到搜索 URL
- 含有 `&`、`#`、`=` 等特殊字符的关键词 MUST 能正确搜索

### R2: N+1 查询优化 (MUST)
- `src/app.py` 的 `results` 和 `filter_results` 路由 MUST 使用 `selectinload(Product.ingredients)` 替代循环查询
- 结果页加载 SHOULD 只需 2 次 DB 查询（SearchTask + Products with Ingredients）

### R3: 路径安全 (MUST)
- `src/scraper/jd.py:152` 的 `download_images` 方法 MUST 验证 `product_id` 参数为纯数字
- 非数字输入 MUST 抛出 `ValueError`

### R4: 代码去重 (SHOULD)
- `results` 和 `filter_results` 路由的 product+ingredient 加载逻辑 SHOULD 抽取为共享函数

## Acceptance Criteria

### AC1: 特殊字符搜索
- **Given** 用户输入搜索关键词 "果汁&饮料"
- **When** 系统构造京东搜索 URL
- **Then** URL 中 keyword 参数被正确编码为 `%E6%9E%9C%E6%B1%81%26%E9%A5%AE%E6%96%99`

### AC2: 查询优化
- **Given** 搜索结果包含 10 个商品，每个商品有 5 条配料记录
- **When** 用户访问结果页
- **Then** 数据库查询次数 <= 3（不再是 1 + 10 次）

### AC3: 路径安全
- **Given** `download_images` 被调用，`product_id` 为 `../../etc`
- **When** 方法执行
- **Then** 抛出 `ValueError`，不创建任何文件

## Out of Scope

- 不修改测试文件中的 P3 级问题（未使用导入等）
- 不重构其他模块

## Security Scope
| Check | Applicable | Reason |
|-------|------------|--------|
| SEC-1 | No | 无新增密钥 |
| SEC-2 | Yes | 修复 URL 编码问题 |
| SEC-3 | Yes | 优化查询方式 |
| SEC-4 | No | 无模板变更 |
| SEC-5 | N/A | 无认证系统 |
| SEC-6 | No | 无新端点 |
| SEC-7 | No | 无错误处理变更 |
| SEC-8 | No | 无新依赖 |
