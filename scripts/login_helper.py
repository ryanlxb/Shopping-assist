"""Interactive login helper — opens browser for manual login, saves cookies."""

import asyncio
import json
import sys
from pathlib import Path

from playwright.async_api import async_playwright

COOKIE_DIRS = Path("data/cookies")
PLATFORMS = {
    "tb": {
        "name": "淘宝",
        "login_url": "https://login.taobao.com/",
        "check_url": "https://s.taobao.com/search?q=test",
        "cookie_path": COOKIE_DIRS / "tb_cookies.json",
    },
    "jd": {
        "name": "京东",
        "login_url": "https://passport.jd.com/new/login.aspx",
        "check_url": "https://search.jd.com/Search?keyword=test&enc=utf-8",
        "cookie_path": COOKIE_DIRS / "jd_cookies.json",
    },
}


async def interactive_login(platform_key: str):
    cfg = PLATFORMS[platform_key]
    print(f"\n{'='*50}")
    print(f"  {cfg['name']} 登录助手")
    print(f"{'='*50}")
    print(f"即将打开 {cfg['name']} 登录页面，请手动完成登录。")
    print("登录成功后，脚本会自动检测并保存 cookie。\n")

    pw = await async_playwright().start()
    browser = await pw.chromium.launch(headless=False)
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
        viewport={"width": 1920, "height": 1080},
        locale="zh-CN",
    )
    try:
        from playwright_stealth import Stealth
        stealth = Stealth(navigator_platform_override="MacIntel")
        await stealth.apply_stealth_async(context)
    except ImportError:
        pass

    page = await context.new_page()
    await page.goto(cfg["login_url"], wait_until="domcontentloaded")

    print("⏳ 等待登录完成...（最多等待 4 分钟）")
    for attempt in range(120):
        await asyncio.sleep(2)
        current_url = page.url
        if "login" not in current_url.lower() and "passport" not in current_url.lower():
            break
        if attempt % 15 == 14:
            print("   仍在等待登录...")

    await asyncio.sleep(3)

    # Navigate to search to verify login works
    await page.goto(cfg["check_url"], wait_until="domcontentloaded")
    await asyncio.sleep(5)

    final_url = page.url
    if "login" in final_url.lower() or "passport" in final_url.lower():
        print(f"\n❌ 登录似乎未完成 (当前 URL: {final_url})")
        print("   请重试。")
    else:
        COOKIE_DIRS.mkdir(parents=True, exist_ok=True)
        cookies = await context.cookies()
        cfg["cookie_path"].write_text(json.dumps(cookies, ensure_ascii=False))
        print(f"\n✅ {cfg['name']} 登录成功！Cookie 已保存到 {cfg['cookie_path']}")
        print(f"   保存了 {len(cookies)} 个 cookie")

    await context.close()
    await browser.close()
    await pw.stop()


async def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "all"

    if target in ("tb", "all"):
        await interactive_login("tb")
    if target in ("jd", "all"):
        await interactive_login("jd")

    print("\n🎉 完成！现在可以正常使用搜索功能了。")


if __name__ == "__main__":
    asyncio.run(main())
