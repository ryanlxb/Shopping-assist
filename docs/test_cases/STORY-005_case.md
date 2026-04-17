# Test Cases: STORY-005

## TC-001: IngredientRule 数据模型 (AC1)
**Given** `IngredientRule` 模型已定义
**When** 创建 blacklist/whitelist/warning 规则并存入数据库
**Then** 规则能按 category 正确查询

## TC-002: 添加配料规则 (AC1)
**Given** 用户在配料规则页面
**When** POST /ingredients/rules 提交 name="山梨酸钾", category="blacklist"
**Then** 规则保存到数据库，重定向到规则页面

## TC-003: 删除配料规则 (AC1)
**Given** 数据库中存在规则
**When** POST /ingredients/rules/{id}/delete
**Then** 规则被删除，重定向到规则页面

## TC-004: 规则管理页面按分类分组 (AC1)
**Given** 数据库中有 blacklist/whitelist/warning 规则
**When** GET /ingredients/rules
**Then** 页面按三个分类分组展示：黑名单、白名单、警告

## TC-005: 结果页配料标记 (AC2)
**Given** 黑名单中有"山梨酸钾"，白名单中有"NFC"
**When** 搜索结果显示某商品配料
**Then** 命中黑名单的配料显示红色标记，命中白名单的显示绿色标记，警告显示黄色标记

## TC-006: 配料评分计算 (AC2)
**Given** 商品配料中有 2 个白名单命中和 1 个黑名单命中
**When** 计算配料评分
**Then** 评分 = 2 - 1 = 1

## TC-007: 排除黑名单快捷筛选 (AC3)
**Given** 搜索结果中有含黑名单配料的商品
**When** 访问 /results/{id}/filter?no_blacklist=true
**Then** 仅展示不含黑名单配料的商品

## TC-008: 默认规则自动预置 (AC1)
**Given** 数据库中无 IngredientRule 记录
**When** `auto_seed_rules()` 被调用
**Then** 从 ADDITIVE_DATABASE 中自动创建 caution/avoid 类型的规则
