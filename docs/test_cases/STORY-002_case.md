# Test Cases: STORY-002

## TC-001: URL 编码 (AC1)
**Given** 用户输入搜索关键词 "果汁&饮料"
**When** JDScraper.search() 构造搜索 URL
**Then** URL 中 keyword 参数被 `urllib.parse.quote()` 正确编码，特殊字符不会破坏 URL 结构

## TC-002: N+1 查询优化 (AC2)
**Given** 搜索结果包含多个商品，每个商品有多条配料记录
**When** 用户访问 GET /results/{task_id}
**Then** 使用 `selectinload(Product.ingredients)` 预加载，数据库查询次数 <= 3

## TC-003: 路径安全 (AC3)
**Given** `download_images` 被调用，`product_id` 为 `../../etc`
**When** 方法执行 `product_id.isdigit()` 验证
**Then** 抛出 `ValueError`，不创建任何文件
