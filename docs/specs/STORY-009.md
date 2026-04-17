# STORY-009: 商品收藏与对比清单

| Field | Value |
|-------|-------|
| ID | STORY-009 |
| Status | Done |
| Priority | P3 |
| Release | 0.1.0 |

- **Priority Score**: 1.5 (Impact 3 / Effort 2)

## Background

用户在浏览搜索结果时，希望将感兴趣的商品收藏起来，事后统一对比配料和价格，做出最优选购决策。本 Story 提供商品收藏和收藏列表对比功能。

## Requirements

### R1: Favorite 数据模型 (MUST)
- 系统 MUST 新增 `Favorite` 模型：`id, product_id, note, created_at`
- `product_id` MUST 外键关联 `Product` 表
- 同一商品 MUST 不能重复收藏（幂等性）

### R2: 收藏操作 (MUST)
- 系统 MUST 提供 `POST /favorites/{product_id}` 添加收藏
- 系统 MUST 提供 `POST /favorites/{product_id}/delete` 取消收藏
- 添加/删除后 MUST 重定向到 `/favorites`

### R3: 收藏列表页面 (MUST)
- 系统 MUST 提供 `GET /favorites` 页面
- 页面 MUST 展示所有收藏商品的名称、价格、平台、配料评分
- 页面 MUST 支持按价格升序/降序和配料评分降序排序
- 页面 MUST 展示每个商品的配料分类标签（颜色标记）

### R4: 对比信息 (SHOULD)
- 页面 SHOULD 展示所有收藏商品的价格范围和价差
- 页面 SHOULD 在每个商品卡片上展示平台来源标识

## Acceptance Criteria

### AC1: 添加收藏
- **Given** 用户在搜索结果页看到商品
- **When** 点击收藏（`POST /favorites/{product_id}`）
- **Then** 商品添加到收藏列表，重定向到 `/favorites`

### AC2: 重复收藏幂等
- **Given** 商品已被收藏
- **When** 再次 `POST /favorites/{product_id}`
- **Then** 不创建重复记录，正常重定向

### AC3: 取消收藏
- **Given** 用户已收藏商品
- **When** 点击取消收藏（`POST /favorites/{product_id}/delete`）
- **Then** 收藏记录被删除，重定向到 `/favorites`

## Out of Scope

- 不做收藏分组/标签
- 不做收藏导出
- 不做收藏数量上限

## Security Scope
| Check | Applicable | Reason |
|-------|------------|--------|
| SEC-1 | No | 无密钥 |
| SEC-2 | No | product_id 来自 URL path |
| SEC-3 | Yes | 新增数据模型和查询 |
| SEC-4 | Yes | 渲染收藏商品信息 |
| SEC-5 | N/A | 无认证 |
| SEC-6 | Yes | 新增 API 路由 |
| SEC-7 | Yes | 商品/收藏不存在的处理 |
| SEC-8 | No | 无新依赖 |
