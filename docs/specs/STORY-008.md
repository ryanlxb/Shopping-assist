# STORY-008: 历史价格追踪与趋势图

| Field | Value |
|-------|-------|
| ID | STORY-008 |
| Status | Done |
| Priority | P3 |
| Release | 0.1.0 |

- **Priority Score**: 1.0 (Impact 3 / Effort 3)

## Background

用户希望了解关注商品的价格变化趋势，判断当前价格是否合理、是否有降价趋势。本 Story 自动记录每次搜索时的商品价格，并提供价格历史查看页面。

## Requirements

### R1: PriceHistory 数据模型 (MUST)
- 系统 MUST 新增 `PriceHistory` 模型：`id, product_id, price, platform, recorded_at`
- `product_id` MUST 外键关联 `Product` 表
- `recorded_at` MUST 自动记录创建时间

### R2: 自动价格记录 (MUST)
- `SearchService.execute_search()` MUST 在保存商品时同时创建 `PriceHistory` 记录
- 仅当商品有价格数据时 MUST 记录（`price is not None`）

### R3: 价格历史页面 (MUST)
- 系统 MUST 提供 `GET /price-history/{product_id}` 页面
- 页面 MUST 展示该商品的所有历史价格记录（时间、价格、平台）
- 页面 MUST 展示统计信息：最低价、最高价、记录条数
- 商品不存在时 MUST 重定向到首页并提示错误

### R4: 价格趋势数据 (SHOULD)
- 系统 SHOULD 将价格历史数据序列化为 JSON 供前端图表使用
- 前端 SHOULD 使用图表展示价格变化趋势（折线图）

## Acceptance Criteria

### AC1: 自动记录价格
- **Given** SearchService 搜索到一个价格为 ¥12.90 的京东商品
- **When** 商品保存到数据库
- **Then** 同时创建一条 PriceHistory 记录（price=12.90, platform="jd"）

### AC2: 价格历史页面
- **Given** 商品有 3 条历史价格记录
- **When** 访问 `GET /price-history/{product_id}`
- **Then** 页面展示 3 条记录的表格，以及最低价、最高价、记录条数统计

### AC3: 商品不存在
- **Given** 数据库中不存在 product_id=99999
- **When** 访问 `GET /price-history/99999`
- **Then** 重定向到首页并显示错误提示

## Out of Scope

- 不做自动定时价格抓取（仅在用户搜索时记录）
- 不做价格预警通知
- 不做跨平台同款商品价格合并

## Security Scope
| Check | Applicable | Reason |
|-------|------------|--------|
| SEC-1 | No | 无密钥 |
| SEC-2 | No | 无新表单输入 |
| SEC-3 | Yes | 新增数据模型和查询 |
| SEC-4 | Yes | 渲染价格数据和 JSON |
| SEC-5 | N/A | 无认证 |
| SEC-6 | Yes | 新增 API 路由 |
| SEC-7 | Yes | 商品不存在的错误处理 |
| SEC-8 | No | 无新依赖 |
