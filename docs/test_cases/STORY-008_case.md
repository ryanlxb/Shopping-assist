# Test Cases: STORY-008

> 注意：STORY-008 的 Spec 为空模板，需求从 PRD 推断。
> PRD 描述："历史价格追踪与趋势图"
> PRD 列出的路由：GET /price-history/{product_id}
> PRD 数据模型：PriceHistory(id, product_id, price, platform, recorded_at)

## TC-001: PriceHistory 数据模型
**Given** PriceHistory 模型已定义
**When** 创建价格记录
**Then** 记录包含 product_id, price, platform, recorded_at 字段

## TC-002: 搜索时自动记录价格
**Given** SearchService 执行搜索
**When** 商品有价格数据
**Then** 自动创建 PriceHistory 记录

## TC-003: 价格历史页面
**Given** 商品有多条价格记录
**When** 访问 GET /price-history/{product_id}
**Then** 页面显示价格历史表格和统计信息（最低、最高、记录条数）
