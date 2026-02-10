"""
测试 playwright fetcher（异步版）
"""
import asyncio
from telegram import Bot
from fetcher_playwright import ManhuaGuiFetcherPlaywright

TOKEN = "8308151445:AAEhS3oZ880gcA3-16-FfHMglzvZ2NalwK0"
CHAT_ID = "8260462836"

COMIC_URL = "https://m.manhuagui.com/comic/1128/"


async def test_playwright():
    """测试 playwright fetcher"""
    bot = Bot(token=TOKEN)
    
    try:
        await bot.send_message(
            chat_id=CHAT_ID,
            text="开始测试 playwright fetcher（异步版）..."
        )
        
        # 初始化 fetcher（异步）
        fetcher = ManhuaGuiFetcherPlaywright(headless=True)
        await fetcher._init_browser()
        
        await bot.send_message(
            chat_id=CHAT_ID,
            text="✅ 1. Playwright 浏览器初始化成功（异步版）"
        )
        
        # 测试获取章节列表（异步）
        await bot.send_message(
            chat_id=CHAT_ID,
            text="2. 开始获取章节列表（异步）..."
        )
        
        from datetime import datetime
        start = datetime.now()
        chapters = await fetcher.get_chapters(COMIC_URL)
        elapsed = datetime.now() - start
        
        await bot.send_message(
            chat_id=CHAT_ID,
            text=f"✅ 2. 章节列表获取成功（异步版）\n\n"
                 f"  章节数量: {len(chapters)}\n"
                 f"  用时: {elapsed.total_seconds():.1f}秒\n"
                 f"  模式: Playwright 异步\n\n"
                 f"🎉 Playwright fetcher 测试成功！\n"
                 f"💡 可以开始使用 playwright 版本的下载器了"
        )
        
        # 清理
        await fetcher.close()
        
    except Exception as e:
        await bot.send_message(
            chat_id=CHAT_ID,
            text=f"❌ 测试失败: {str(e)[:500]}"
        )
        import traceback
        traceback.print_exc()


asyncio.run(test_playwright())
