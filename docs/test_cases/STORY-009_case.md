# Test Cases: STORY-009

> 注意：STORY-009 的 Spec 为空模板，需求从 PRD 推断。
> PRD 描述："商品收藏与对比清单"
> PRD 路由：POST /favorites/{product_id}, DELETE /favorites/{product_id}, GET /favorites, GET /compare

## TC-001: Favorite 数据模型
**Given** Favorite 模型已定义
**When** 创建收藏记录
**Then** 记录包含 product_id, note, created_at 字段，product_id 唯一约束

## TC-002: 添加收藏
**Given** 用户在搜索结果页
**When** POST /favorites/{product_id}
**Then** 商品被添加到收藏，重定向到 /favorites

## TC-003: 取消收藏
**Given** 用户已收藏商品
**When** POST /favorites/{product_id}/delete
**Then** 收藏记录被删除，重定向到 /favorites

## TC-004: 收藏列表页
**Given** 用户有收藏商品
**When** GET /favorites
**Then** 页面展示收藏列表，支持按价格和评分排序

## TC-005: 收藏对比
**Given** 用户收藏了多个商品
**When** GET /favorites
**Then** 页面显示价格范围和价差信息，配料评分对比
