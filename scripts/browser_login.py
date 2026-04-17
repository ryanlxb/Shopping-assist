"""Open persistent browser for manual login. Login state auto-saves to profile.

Usage:
    python scripts/browser_login.py tb    # Login to Taobao
    python scripts/browser_login.py jd    # Login to JD
    python scripts/browser_login.py all   # Login to both
"""

import asyncio
import sys
from pathlib import Path

from playwright.async_api import async_playwright

PROFILE_DIR = Path("data/browser_profile")

PLATFORMS = {
    "tb": ("淘宝", "https://login.taobao.com/"),
    "jd": ("京东", "https://passport.jd.com/new/login.aspx"),
}


async def login(platform: str):
    name, url = PLATFORMS[platform]

    print(f"\n{'='*50}")
    print(f"  {name} 登录 — 请在弹出的浏览器中完成登录")
    print(f"{'='*50}\n")

    PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    pw = await async_playwright().start()
    ctx = await pw.chromium.launch_persistent_context(
        user_data_dir=str(PROFILE_DIR),
        headless=False,
        viewport={"width": 1280, "height": 900},
        locale="zh-CN",
        args=["--disable-blink-features=AutomationControlled"],
    )

    page = ctx.pages[0] if ctx.pages else await ctx.new_page()
    await page.goto(url, wait_until="domcontentloaded")

    print(f"浏览器已打开 {name} 登录页面。")
    print("请手动完成登录（扫码/密码/短信均可）。")
    print()
    input(">>> 登录完成后，回到终端按 回车 继续...")

    current_url = page.url
    print(f"\n当前 URL: {current_url}")

    if "login" in current_url.lower() or "passport" in current_url.lower():
        print(f"⚠ 看起来还在登录页面，确认登录成功了吗？")
        input(">>> 如果已登录，按回车继续；否则 Ctrl+C 退出重试...")

    print(f"✅ {name} 登录状态已保存到 {PROFILE_DIR}")

    await ctx.close()
    await pw.stop()


async def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "all"

    if target in ("tb", "all"):
        await login("tb")
    if target in ("jd", "all"):
        await login("jd")

    print(f"\n🎉 登录完成！现在运行验证:")
    print(f"   python scripts/verify_search.py all")


if __name__ == "__main__":
    asyncio.run(main())
