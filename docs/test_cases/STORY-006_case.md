# Test Cases: STORY-006

> 注意：STORY-006 的 Spec 为空模板，需求从 PRD 推断。
> PRD 描述："配料安全评级（自动标记常见添加剂风险等级）"

## TC-001: 配料知识库查询 - 精确匹配
**Given** 内置添加剂知识库 ADDITIVE_DATABASE
**When** 调用 `lookup_additive("山梨酸钾")`
**Then** 返回 category="caution", type="防腐剂"

## TC-002: 配料知识库查询 - 部分匹配
**Given** 内置添加剂知识库
**When** 调用 `lookup_additive("橙汁(NFC)")`
**Then** 匹配 "NFC"，返回 category="safe"

## TC-003: 配料知识库查询 - 未知配料
**Given** 内置添加剂知识库
**When** 调用 `lookup_additive("水")`
**Then** 返回 None

## TC-004: 配料分类集成到结果页
**Given** 搜索结果页渲染商品配料
**When** 配料匹配知识库条目
**Then** 在配料标签旁显示添加剂类型信息（如"防腐剂"）和描述提示
