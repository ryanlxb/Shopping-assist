# Test Cases: STORY-004

## TC-001: TBScraper 协议兼容 (AC2)
**Given** `TBScraper` 已实现 `PlatformScraper` 协议
**When** `isinstance(TBScraper(), PlatformScraper)` 检查
**Then** 返回 True，`platform_name` 为 "tb"

## TC-002: 平台注册 (AC3)
**Given** `TBScraper` 已通过 `@register_platform("tb")` 注册
**When** 调用 `get_scraper("tb")`
**Then** 返回 `TBScraper` 实例

## TC-003: 天猫搜索 HTML 解析 (AC1)
**Given** 天猫搜索结果 HTML（mock）
**When** `parse_tb_product_list(html)` 解析
**Then** 正确提取商品名称、价格、链接、店铺名、缩略图

## TC-004: 天猫详情页解析 (AC1)
**Given** 天猫详情页 HTML（mock）包含配料表文本
**When** `parse_tb_product_detail(html)` 解析
**Then** 提取 `ingredient_text` 为配料文本

## TC-005: 搜索表单平台选择 (AC4)
**Given** 用户在搜索首页
**When** 查看搜索表单 HTML
**Then** 存在 `<select name="platform">` 下拉框，包含 "jd"（京东）和 "tb"（天猫）选项

## TC-006: 结果页平台标识 (AC5)
**Given** 搜索结果中有商品 `platform="jd"` 和 `platform="tb"`
**When** 查看结果页 HTML
**Then** 京东商品显示红色标签"京东"，天猫商品显示橙色标签"天猫"
