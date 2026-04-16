# Test Cases: STORY-001

## TC-001: 搜索闭环 (AC1)
**Given** 用户在 Web 界面输入搜索关键词 "NFC果汁"
**When** 提交 POST /search 表单
**Then** 系统创建 SearchTask 记录（status="running"），并重定向到结果页

## TC-002: 商品列表展示 (AC2)
**Given** 搜索任务已完成，数据库中有关联商品
**When** 用户访问 GET /results/{task_id}
**Then** 页面展示商品列表，每个商品包含：名称、价格、店铺名、缩略图、商品链接

## TC-003: 配料表识别 (AC3)
**Given** 商品详情页中配料表为图片形式
**When** 系统调用 OCR 服务处理图片
**Then** OCR 返回识别文本，配料列表被结构化存入 Ingredient 表

## TC-004: 配料筛选 (AC4)
**Given** 搜索结果中有多个商品，部分含有 "NFC" 配料
**When** 用户访问 GET /results/{task_id}/filter?q=NFC
**Then** 仅返回配料列表中包含 "NFC" 的商品

## TC-005: OCR 降级 (AC5)
**Given** Ollama 服务未启动（连接失败）
**When** OCRService.recognize() 被调用
**Then** 返回 {"text": None, "confidence": None, "error": "..."}，页面展示原图

## TC-006: 反爬韧性 (AC6)
**Given** Playwright 访问京东时遭遇异常
**When** JDScraper.get_detail() 执行
**Then** 返回默认空结果 {"ingredient_text": None, "image_urls": []}，不中断整体搜索流程

## TC-007: 频率限制 (AC7)
**Given** 今日已有 1 条 SearchTask 记录（max_daily=1）
**When** RateLimiter.can_search() 被调用
**Then** 返回 False，POST /search 重定向到 /?error=rate_limit
