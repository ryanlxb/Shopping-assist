# STORY-005: 配料黑名单/白名单管理

| Field | Value |
|-------|-------|
| ID | STORY-005 |
| Status | Draft |
| Priority | P2 |
| Release | 0.0.1 |

- **Priority Score**: 2.5 (Impact 5 / Effort 2)

## Background

用户在查看商品配料时，需要根据自己的标准（如避免"山梨酸钾"、偏好"NFC"）来筛选商品。目前只能手动输入筛选关键词，无法持久化保存配料偏好。本 Story 添加配料规则管理功能，让用户定义黑名单（不想要的添加剂）和白名单（偏好的配料），系统自动在结果页标记和筛选。

## Requirements

### R1: 配料规则数据模型 (MUST)
- 系统 MUST 新增 `IngredientRule` 模型：`id, name, category, description, created_at`
- `category` 字段 MUST 支持三个值：`blacklist`（黑名单）、`whitelist`（白名单）、`warning`（警告）
- 系统 MUST 预置常见添加剂规则作为默认数据

### R2: 配料规则管理页面 (MUST)
- 系统 MUST 提供配料规则管理页面 `/ingredients/rules`
- 用户 MUST 能添加新规则（名称 + 分类 + 描述）
- 用户 MUST 能删除已有规则
- 系统 SHOULD 按分类（黑名单/白名单/警告）分组展示

### R3: 搜索结果配料标记 (MUST)
- 系统 MUST 在搜索结果页自动标记命中黑名单的配料（红色）
- 系统 MUST 在搜索结果页自动标记命中白名单的配料（绿色）
- 系统 SHOULD 展示命中警告的配料（黄色）
- 系统 SHOULD 计算每个商品的"配料评分"（白名单命中数 - 黑名单命中数）

### R4: 基于规则的快捷筛选 (SHOULD)
- 系统 SHOULD 在结果页提供"仅显示无黑名单配料的商品"快捷按钮
- 系统 MAY 支持"仅显示含白名单配料的商品"筛选

## Acceptance Criteria

### AC1: 添加配料规则
- **Given** 用户在配料规则页面
- **When** 输入"山梨酸钾"，选择"黑名单"，点击添加
- **Then** 规则保存到数据库，页面刷新后在黑名单分组中可见

### AC2: 结果页配料标记
- **Given** 黑名单中有"山梨酸钾"，白名单中有"NFC"
- **When** 搜索结果显示某商品配料包含"山梨酸钾"和"橙汁(NFC)"
- **Then** "山梨酸钾"以红色标记，"橙汁(NFC)"以绿色标记

### AC3: 快捷筛选
- **Given** 搜索结果中有 10 个商品，其中 3 个含有黑名单配料
- **When** 用户点击"仅显示无黑名单配料的商品"
- **Then** 页面仅展示 7 个不含黑名单配料的商品

## Out of Scope

- 不做配料知识库（如自动判定"山梨酸钾"是防腐剂）— 留给 STORY-006
- 不做导入/导出配料规则

## Security Scope
| Check | Applicable | Reason |
|-------|------------|--------|
| SEC-1 | No | 无密钥 |
| SEC-2 | Yes | 新增表单输入（配料规则名称） |
| SEC-3 | Yes | 新增数据模型和查询 |
| SEC-4 | Yes | 新增模板渲染配料名称 |
| SEC-5 | N/A | 无认证 |
| SEC-6 | Yes | 新增 API 路由 |
| SEC-7 | Yes | 新增操作的错误处理 |
| SEC-8 | No | 无新依赖 |
