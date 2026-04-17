# STORY-010: 搜索结果排序

| Field | Value |
|-------|-------|
| ID | STORY-010 |
| Status | Done |
| Priority | P3 |
| Release | 0.1.0 |

- **Priority Score**: 1.5 (Impact 3 / Effort 2)

## Background

用户搜索到大量商品后，需要按不同维度排序以快速定位目标商品。本 Story 在现有筛选路由基础上增加排序功能，支持按价格和配料评分排序。

## Requirements

### R1: 排序参数 (MUST)
- `GET /results/{id}/filter` MUST 接受 `sort` 查询参数
- `sort` 值 MUST 支持：`price_asc`（价格升序）、`price_desc`（价格降序）、`score_desc`（配料评分降序）
- 无效 sort 值 MUST 回退为默认排序（不排序）

### R2: 排序逻辑 (MUST)
- 价格排序 MUST 将无价格商品排到最后（升序时）或最前（降序时）
- 配料评分 MUST 使用白名单命中数 - 黑名单命中数作为排序依据

### R3: 排序与筛选组合 (MUST)
- 排序 MUST 能与关键词筛选（`q` 参数）和黑名单排除（`no_blacklist` 参数）组合使用
- 执行顺序 MUST 为：先筛选，再排序

### R4: UI 排序控件 (SHOULD)
- 结果页 SHOULD 提供排序下拉选择控件
- 选择排序后 SHOULD 保持当前筛选条件不变

## Acceptance Criteria

### AC1: 按价格升序排序
- **Given** 搜索结果有 3 个商品，价格分别为 ¥15、¥8、¥12
- **When** 访问 `/results/{id}/filter?sort=price_asc`
- **Then** 商品按 ¥8、¥12、¥15 排列

### AC2: 按配料评分排序
- **Given** 搜索结果有商品评分分别为 3、-1、5
- **When** 访问 `/results/{id}/filter?sort=score_desc`
- **Then** 商品按评分 5、3、-1 排列

### AC3: 排序与筛选组合
- **Given** 搜索结果有 10 个商品，其中 3 个含 "NFC"
- **When** 访问 `/results/{id}/filter?q=NFC&sort=price_asc`
- **Then** 先筛选出 3 个含 NFC 的商品，再按价格升序排列

## Out of Scope

- 不做多字段组合排序
- 不做自定义排序字段
- 不做排序持久化

## Security Scope
| Check | Applicable | Reason |
|-------|------------|--------|
| SEC-1 | No | 无密钥 |
| SEC-2 | Yes | sort 参数需白名单校验 |
| SEC-3 | No | 无新数据模型 |
| SEC-4 | No | 无新渲染内容 |
| SEC-5 | N/A | 无认证 |
| SEC-6 | No | 复用现有路由 |
| SEC-7 | Yes | 无效 sort 值处理 |
| SEC-8 | No | 无新依赖 |
