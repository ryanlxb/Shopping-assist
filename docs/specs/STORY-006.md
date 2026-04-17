# STORY-006: 配料安全评级

| Field | Value |
|-------|-------|
| ID | STORY-006 |
| Status | Done |
| Priority | P2 |
| Release | 0.1.0 |

- **Priority Score**: 1.33 (Impact 4 / Effort 3)

## Background

用户在查看配料列表时，面对大量化学名称（如"山梨酸钾"、"安赛蜜"）无法判断其安全性。本 Story 内置一个包含 30+ 常见食品添加剂的知识库，自动标注每个添加剂的类型（防腐剂/甜味剂/着色剂等）、安全等级（安全/警告/避免）和简要说明，帮助用户快速识别配料风险。

## Requirements

### R1: 添加剂知识库 (MUST)
- 系统 MUST 内置 `ADDITIVE_DATABASE` 字典，包含至少 30 种常见食品添加剂
- 每个条目 MUST 包含字段：`category`（safe/caution/avoid）、`type`（添加剂类型）、`desc`（简要说明）
- 知识库 MUST 覆盖防腐剂、甜味剂、着色剂、增稠剂、抗氧化剂等主要类别

### R2: 添加剂查询接口 (MUST)
- 系统 MUST 提供 `lookup_additive(name)` 函数
- 查询 MUST 支持精确匹配（如 "山梨酸钾"）
- 查询 MUST 支持部分匹配/子串匹配（如 "NFC" 匹配含 NFC 的条目）
- 未匹配时 MUST 返回 None

### R3: 自动种子规则 (MUST)
- 系统 MUST 在首次启动时将知识库条目自动写入 `IngredientRule` 表
- 如果表中已有规则，MUST 跳过种子操作，避免重复
- 知识库 category 到规则 category 的映射：safe→whitelist、caution→warning、avoid→blacklist

### R4: 结果页集成 (MUST)
- 搜索结果页 MUST 在每个配料标签旁展示知识库信息（类型 + 描述）
- 系统 SHOULD 使用 tooltip 方式展示详细描述，避免页面过于拥挤

## Acceptance Criteria

### AC1: 精确匹配查询
- **Given** 知识库包含 "山梨酸钾" 条目
- **When** 调用 `lookup_additive("山梨酸钾")`
- **Then** 返回 category="caution", type="防腐剂"

### AC2: 部分匹配查询
- **Given** 知识库包含 "NFC" 条目
- **When** 调用 `lookup_additive("橙汁(NFC)")`
- **Then** 匹配成功，返回 category="safe"

### AC3: 未知配料查询
- **Given** "水" 不在知识库中
- **When** 调用 `lookup_additive("水")`
- **Then** 返回 None

## Out of Scope

- 不做用户自定义知识库条目（由 STORY-005 的规则管理覆盖）
- 不做外部知识库 API 对接
- 不做配料间交互作用分析

## Security Scope
| Check | Applicable | Reason |
|-------|------------|--------|
| SEC-1 | No | 无密钥 |
| SEC-2 | No | 无新表单输入 |
| SEC-3 | Yes | 知识库数据自动写入 DB |
| SEC-4 | Yes | 模板渲染知识库描述 |
| SEC-5 | N/A | 无认证 |
| SEC-6 | No | 无新 API 路由 |
| SEC-7 | Yes | 种子操作错误处理 |
| SEC-8 | No | 无新依赖 |
