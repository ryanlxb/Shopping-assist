# STORY-007: 跨平台商品比价视图

| Field | Value |
|-------|-------|
| ID | STORY-007 |
| Status | Done |
| Priority | P2 |
| Release | 0.1.0 |

- **Priority Score**: 1.33 (Impact 4 / Effort 3)

## Background

用户在京东和淘宝搜索同类商品后，希望能直观对比不同平台的价格和配料差异。本 Story 通过收藏页面提供跨平台比价能力，展示价格范围、价差和配料评分对比。

## Requirements

### R1: 收藏页比价信息展示 (MUST)
- 收藏页面 MUST 展示所有收藏商品的价格范围（最低价 ~ 最高价）
- 收藏页面 MUST 展示价差金额
- 收藏页面 MUST 展示每个商品的平台来源标识（京东/淘宝）

### R2: 比价排序 (MUST)
- 收藏页面 MUST 支持按价格升序排列
- 收藏页面 MUST 支持按价格降序排列
- 收藏页面 MUST 支持按配料评分降序排列

### R3: 配料评分对比 (SHOULD)
- 收藏页面 SHOULD 展示每个商品的配料评分
- 收藏页面 SHOULD 展示配料分类标签（黑名单/白名单/警告颜色标记）

## Acceptance Criteria

### AC1: 跨平台比价展示
- **Given** 用户收藏了 1 个京东商品（¥12.90）和 1 个淘宝商品（¥9.90）
- **When** 访问 `/favorites`
- **Then** 页面展示价格范围 ¥9.90 ~ ¥12.90，价差 ¥3.00，且商品带平台标识

### AC2: 按价格排序比价
- **Given** 用户收藏了多个不同平台的商品
- **When** 选择按价格升序排序
- **Then** 商品按价格从低到高排列，便于对比最优价格

## Out of Scope

- 不做独立的 `/compare` 路由（比价功能集成在收藏页中）
- 不做自动同款商品匹配（用户手动选择收藏商品进行对比）
- 不做实时价格刷新

## Security Scope
| Check | Applicable | Reason |
|-------|------------|--------|
| SEC-1 | No | 无密钥 |
| SEC-2 | No | 无新表单输入 |
| SEC-3 | Yes | 查询收藏 + 商品数据 |
| SEC-4 | Yes | 渲染价格和配料 |
| SEC-5 | N/A | 无认证 |
| SEC-6 | No | 复用 /favorites 路由 |
| SEC-7 | Yes | 空收藏列表处理 |
| SEC-8 | No | 无新依赖 |
