"""
测试 fetcher_selenium 重写版
验证是否真的直连，不再使用代理
"""
import asyncio
from telegram import Bot
from fetcher_selenium import create_fetcher_selenium
from database import Database

TOKEN = "8308151445:AAEhS3oZ880gcA3-16-FfHMglzvZ2NalwK0"
CHAT_ID = "8260462836"


async def test_fetcher():
    """测试 fetcher 是否直连"""
    bot = Bot(token=TOKEN)
    
    await bot.send_message(
        chat_id=CHAT_ID,
        text="开始测试 fetcher_selenium 重写版..."
    )
    
    try:
        # 初始化
        await bot.send_message(
            chat_id=CHAT_ID,
            text="1. 初始化 fetcher..."
        )
        
        fetcher = create_fetcher_selenium(use_proxy=False, headless=True)
        
        await bot.send_message(
            chat_id=CHAT_ID,
            text="✅ 1. fetcher 初始化成功（直连模式）"
        )
        
        # 测试获取章节列表
        await bot.send_message(
            chat_id=CHAT_ID,
            text="2. 获取章节列表..."
        )
        
        from datetime import datetime
        
        start = datetime.now()
        chapters = fetcher.get_chapters("https://m.manhuagui.com/comic/1128/")
        elapsed = datetime.now() - start
        
        await bot.send_message(
            chat_id=CHAT_ID,
            text=f"✅ 2. 章节列表获取成功\n\n"
                 f"  章节数量: {len(chapters)}\n"
                 f"  用时: {elapsed.total_seconds():.1f}秒\n"
                 f"  模式: 直连（无代理）"
        )
        
        # 测试获取第1话图片
        await bot.send_message(
            chat_id=CHAT_ID,
            text="3. 获取第1话图片..."
        )
        
        # 找到第1话
        chapter_1 = None
        for chapter in chapters:
            if chapter['chapter_num'] == '1':
                chapter_1 = chapter
                break
        
        if chapter_1:
            await bot.send_message(
                chat_id=CHAT_ID,
                text=f"  章节: {chapter_1['title']}\n"
                     f"  URL: {chapter_1['url']}"
            )
            
            start = datetime.now()
            images = fetcher.get_images(chapter_1['url'])
            elapsed = datetime.now() - start
            
            await bot.send_message(
                chat_id=CHAT_ID,
                text=f"✅ 3. 图片获取成功\n\n"
                     f"  图片数量: {len(images)}\n"
                     f"  用时: {elapsed.total_seconds():.1f}秒\n"
                     f"  模式: 直连（无代理）\n\n"
                     f"🎉 fetcher_selenium 重写版测试成功！"
            )
            
            # 清理
            fetcher.close()
            
        else:
            await bot.send_message(
                chat_id=CHAT_ID,
                text="❌ 未找到第1话"
            )
            
    except Exception as e:
        await bot.send_message(
            chat_id=CHAT_ID,
            text=f"❌ 测试失败: {str(e)[:500]}"
        )
        import traceback
        traceback.print_exc()


asyncio.run(test_fetcher())
