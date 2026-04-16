# Lessons Learned

| Date | Lesson | Source |
|------|--------|--------|
| 2026-04-16 | Starlette 1.0 的 `TemplateResponse` 签名变了：第一参数是 `request`，第二参数是模板名。旧写法 `TemplateResponse("name", {"request": req})` 会导致 Jinja2 缓存 unhashable dict 错误 | STORY-001 |
| 2026-04-16 | SQLite in-memory DB 在 E2E 测试中需要 `StaticPool` + `check_same_thread=False`，否则不同线程拿到不同连接看不到表 | STORY-001 |
| 2026-04-16 | `Base.metadata.create_all(engine)` 前必须确保 models 已 import，否则 metadata 为空不创建任何表 | STORY-001 |
