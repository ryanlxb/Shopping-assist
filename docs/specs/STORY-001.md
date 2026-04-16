# STORY-001: MVP 核心闭环 — 京东商品搜索与配料表智能提取

| Field | Value |
|-------|-------|
| ID | STORY-001 |
| Status | Draft |
| Priority | P1 |
| Release | 0.0.1 |

## Background

用户在京东/淘宝购买食品（果汁、酱油等）时，需要逐个点开商品详情页查看配料表，而配料表大多以图片形式存在，无法搜索和对比。这导致选购过程极其繁琐耗时。

本 Story 实现 MVP 核心闭环：用户输入搜索关键词 → 系统自动从京东获取商品列表 → 提取商品元数据（名称、价格、店铺、链接）→ 下载配料表图片 → 通过本地多模态 LLM 识别配料文本 → 将结果存入 SQLite → 在 Web 界面统一展示和筛选。

## Requirements

### R1: Web 应用框架
- 系统 MUST 基于 FastAPI + Jinja2 + TailwindCSS 构建 Web 应用
- 系统 MUST 提供搜索页面，用户输入关键词即可发起商品搜索
- 系统 MUST 提供结果列表页面，展示所有搜索到的商品及其配料信息
- 系统 SHOULD 支持按配料关键词筛选（如输入"NFC"过滤含该配料的商品）

### R2: 京东商品搜索
- 系统 MUST 使用 Playwright (stealth 模式) 模拟浏览器访问京东搜索页
- 系统 MUST 提取商品列表中的元数据：商品名称、价格、店铺名称、商品链接、缩略图链接
- 系统 MUST 支持提取搜索结果前 N 个商品（N 可配置，默认 30）
- 系统 MUST 实现反爬策略：
  - 随机延迟（3-8 秒）
  - User-Agent 轮换
  - 完整请求头伪装
  - Cookie 持久化
- 系统 SHOULD 在搜索被平台拒绝时，返回明确错误信息而非静默失败

### R3: 商品详情页解析
- 系统 MUST 进入每个商品的详情页，定位配料表区域
- 系统 MUST 尝试提取文本形式的配料表（如果存在）
- 系统 MUST 下载配料表图片（如果配料表以图片形式存在）
- 系统 SHOULD 识别并下载商品规格参数图片
- 系统 MUST 将图片保存到本地 `data/images/` 目录

### R4: 配料表 OCR 识别
- 系统 MUST 使用本地多模态 LLM（Qwen2.5-VL 通过 Ollama）识别配料表图片中的文本
- 系统 MUST 支持中文配料表识别
- 系统 MUST 返回结构化的配料列表（不仅是原始 OCR 文本）
- 系统 SHOULD 标记 OCR 识别置信度（高/中/低）
- 系统 MUST 在 OCR 服务不可用时，降级展示原始图片并标注"未识别"

### R5: 数据持久化
- 系统 MUST 使用 SQLite 作为数据库
- 系统 MUST 使用 SQLAlchemy 2.0 作为 ORM
- 系统 MUST 存储以下数据模型：
  - `SearchTask`: 搜索任务记录（关键词、时间、状态、结果数量）
  - `Product`: 商品信息（名称、价格、店铺、链接、平台、缩略图路径）
  - `Ingredient`: 配料信息（关联商品、配料名称、原始文本、OCR 来源图片路径、置信度）
- 系统 MUST 支持按搜索任务查询关联的商品和配料

### R6: 配料筛选与展示
- 系统 MUST 在结果页展示：商品名称、价格、店铺、配料列表、商品链接
- 系统 MUST 支持按配料关键词搜索（如"NFC"、"浓缩还原"、"山梨酸钾"）
- 系统 SHOULD 支持配料黑名单功能（用户可定义不想要的添加剂列表）
- 系统 SHOULD 高亮显示匹配的配料关键词
- 系统 MAY 支持按价格排序

### R7: 频率控制
- 系统 MUST 实现全局请求频率限制器
- 系统 MUST 支持配置每日最大搜索任务数（默认 1 次/天）
- 系统 MUST 在达到频率限制时，提示用户并阻止新搜索
- 系统 SHOULD 记录每次请求的时间戳用于频率统计

## Acceptance Criteria

### AC1: 搜索闭环
**Given** 用户在 Web 界面输入搜索关键词"NFC果汁"
**When** 点击搜索按钮
**Then** 系统后台启动京东搜索任务，页面显示"搜索进行中"

### AC2: 商品列表展示
**Given** 搜索任务完成
**When** 用户查看搜索结果
**Then** 页面展示商品列表，每个商品包含：名称、价格、店铺名、缩略图、商品链接

### AC3: 配料表识别
**Given** 商品详情页中配料表为图片形式
**When** 系统处理该商品
**Then** 系统下载图片并通过 Qwen2.5-VL 识别为文本配料列表，存入数据库

### AC4: 配料筛选
**Given** 搜索结果中有多个商品
**When** 用户在筛选框输入"NFC"
**Then** 仅展示配料列表中包含"NFC"的商品

### AC5: OCR 降级
**Given** Ollama 服务未启动或不可用
**When** 系统尝试 OCR 识别
**Then** 显示原始配料图片，标注"OCR 服务不可用，展示原图"

### AC6: 反爬韧性
**Given** 系统正在爬取京东商品
**When** 请求被限速或拒绝
**Then** 系统记录错误日志，跳过该商品，继续处理下一个

### AC7: 频率限制
**Given** 今日已执行过搜索任务
**When** 用户再次发起搜索
**Then** 系统提示"今日搜索次数已达上限"，阻止新搜索

## Target Call Chain

```
用户请求 (Web UI)
  → FastAPI Router (POST /search)
    → SearchService.create_task(keyword)
      → JDScraper.search(keyword, limit=30)
        → Playwright (stealth) → 京东搜索页
        → HTMLParser.extract_product_list(page)
      → for each product:
          → JDScraper.get_detail(product_url)
            → HTMLParser.extract_ingredients(detail_page)
            → ImageDownloader.download(image_urls)
          → OCRService.recognize(image_path)
            → Ollama API → Qwen2.5-VL
            → IngredientParser.parse(ocr_text)
      → DBService.save_results(task, products, ingredients)
  → Template render → 结果页
```

## Non-Goals

- 不做自动下单、加购物车等写操作
- 不做用户认证/多用户系统
- 不做社交分享功能
- 不做多语言支持
- 不做淘宝/天猫平台（留作后续 Story）
- 不做历史价格追踪（留作后续 Story）
- 不做推荐算法（留作后续 Story）

## Implementation Steps

| Step | File | Action | Dependencies | Risk |
|------|------|--------|--------------|------|
| 1 | `pyproject.toml` | 初始化 Python 项目，声明依赖 | None | Low |
| 2 | `src/models.py` | 定义 SQLAlchemy 数据模型 | Step 1 | Low |
| 3 | `src/database.py` | 数据库连接与初始化 | Step 2 | Low |
| 4 | `src/scraper/jd.py` | 京东搜索与详情页爬取 | Step 1 | High |
| 5 | `src/scraper/parser.py` | HTML 解析与元数据提取 | Step 4 | Medium |
| 6 | `src/ocr/service.py` | Ollama OCR 服务封装 | Step 1 | Medium |
| 7 | `src/ocr/ingredient_parser.py` | 配料文本结构化解析 | Step 6 | Medium |
| 8 | `src/services/search.py` | 搜索服务编排层 | Step 4, 5, 6, 7 | Medium |
| 9 | `src/services/rate_limiter.py` | 频率限制器 | Step 3 | Low |
| 10 | `src/app.py` | FastAPI 应用入口与路由 | Step 8, 9 | Low |
| 11 | `src/templates/` | Jinja2 模板（搜索页、结果页） | Step 10 | Low |
| 12 | `tests/unit/test_parser.py` | HTML 解析单元测试 | Step 5 | Low |
| 13 | `tests/unit/test_ocr.py` | OCR 服务单元测试 | Step 6 | Low |

## Security Scope

| Check | Applicable | Reason |
|-------|------------|--------|
| SEC-1 | Yes | Python 源代码新建 |
| SEC-2 | Yes | Web 表单接收用户搜索关键词 |
| SEC-3 | Yes | SQLAlchemy ORM 操作数据库 |
| SEC-4 | Yes | Jinja2 模板渲染，需防范 XSS |
| SEC-5 | No | 无用户认证系统（个人工具） |
| SEC-6 | Yes | 新建 FastAPI 路由 |
| SEC-7 | Yes | 爬虫异常处理、OCR 服务异常处理 |
| SEC-8 | Yes | 新建 pyproject.toml，引入多个依赖 |

### 安全要点
- **SEC-2**: 搜索关键词 MUST 做输入验证和长度限制，防止注入
- **SEC-3**: 使用 SQLAlchemy ORM 参数化查询，避免 SQL 注入
- **SEC-4**: Jinja2 默认开启 autoescaping，MUST NOT 使用 `|safe` 除非确认安全
- **SEC-6**: API 路由 MUST 限制请求体大小
- **SEC-8**: 依赖 MUST 锁定版本（使用 `uv.lock` 或 `poetry.lock`）
