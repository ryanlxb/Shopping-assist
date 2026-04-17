# Test Cases: STORY-010

> 注意：STORY-010 的 Spec 为空模板，需求从 PRD 推断。
> PRD 描述："搜索结果排序（按价格/配料评分/综合）"
> PRD 路由：GET /results/{id}/sort（实际合并到 /results/{id}/filter?sort=xxx）

## TC-001: 按价格升序排序
**Given** 搜索结果有多个不同价格的商品
**When** 访问 /results/{id}/filter?sort=price_asc
**Then** 商品按价格从低到高排列

## TC-002: 按价格降序排序
**Given** 搜索结果有多个不同价格的商品
**When** 访问 /results/{id}/filter?sort=price_desc
**Then** 商品按价格从高到低排列

## TC-003: 按配料评分排序
**Given** 搜索结果有不同配料评分的商品
**When** 访问 /results/{id}/filter?sort=score_desc
**Then** 商品按配料评分从高到低排列

## TC-004: 排序与筛选组合
**Given** 搜索结果有多个商品
**When** 同时使用筛选和排序 /results/{id}/filter?q=NFC&sort=price_asc
**Then** 先筛选出含 NFC 的商品，再按价格升序排列
