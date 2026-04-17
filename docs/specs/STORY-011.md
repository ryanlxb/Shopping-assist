# STORY-011: 基于配料偏好的商品推荐

| Field | Value |
|-------|-------|
| ID | STORY-011 |
| Status | Done |
| Priority | P3 |
| Release | 0.1.0 |

- **Priority Score**: 0.75 (Impact 3 / Effort 4)

## Background

用户希望在首页就能看到配料质量最好的商品推荐，而不是每次都要搜索再筛选。本 Story 基于历史搜索数据和配料评分，在首页展示配料评分最高的商品。

## Requirements

### R1: 推荐算法 (MUST)
- 系统 MUST 从数据库取最近商品（上限 100 条），计算每个商品的配料评分
- 配料评分 MUST 使用公式：白名单命中数 - 黑名单命中数
- 系统 MUST 仅推荐评分 > 0 的商品
- 推荐列表 MUST 按评分降序排列，默认返回前 6 个

### R2: 首页推荐展示 (MUST)
- 首页 MUST 包含"推荐商品"区域
- 每个推荐商品 MUST 展示：名称、价格、平台标识、配料评分
- 无推荐数据时（无商品或全部评分 ≤ 0）MUST 不显示推荐区域

### R3: 推荐数据传递 (MUST)
- `GET /` 路由 MUST 调用推荐函数并将结果传递给模板
- 推荐计算 MUST 复用现有的配料规则加载和分类逻辑

## Acceptance Criteria

### AC1: 有推荐数据
- **Given** 数据库有商品，其中 3 个配料评分 > 0
- **When** 用户访问首页 `GET /`
- **Then** 推荐区域展示这 3 个商品，按评分降序排列

### AC2: 无推荐数据
- **Given** 数据库无商品数据
- **When** 用户访问首页 `GET /`
- **Then** 不显示推荐区域

### AC3: 仅推荐正评分商品
- **Given** 数据库有 5 个商品，其中 2 个评分 > 0，3 个评分 ≤ 0
- **When** `_get_recommendations()` 被调用
- **Then** 仅返回 2 个评分 > 0 的商品

## Out of Scope

- 不做个性化推荐
- 不做推荐缓存
- 不做推荐解释

## Security Scope
| Check | Applicable | Reason |
|-------|------------|--------|
| SEC-1 | No | 无密钥 |
| SEC-2 | No | 无新表单输入 |
| SEC-3 | Yes | 查询商品 + 配料数据 |
| SEC-4 | Yes | 渲染推荐商品信息 |
| SEC-5 | N/A | 无认证 |
| SEC-6 | No | 复用 GET / 路由 |
| SEC-7 | Yes | 空数据处理 |
| SEC-8 | No | 无新依赖 |
