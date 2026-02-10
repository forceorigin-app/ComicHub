"""
ONE PIECE 手动下载器
使用方式：python3 manual_download.py <章节号>
"""
import asyncio
import logging
from pathlib import Path
from datetime import datetime
import sys
import os

from fetcher_selenium import ManhuaGuiFetcherSelenium
from database import Database
from telegram import Bot

# 配置
COMIC_URL = "https://m.manhuagui.com/comic/1128/"
SAVE_PATH = "/Users/force/data/comics"
TOKEN = "8308151445:AAEhS3oZ880gcA3-16-FfHMglzvZ2NalwK0"
CHAT_ID = "8260462836"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def download_chapter(chapter_num: str):
    """下载指定章节"""
    bot = Bot(token=TOKEN)
    
    try:
        await bot.send_message(
            chat_id=CHAT_ID,
            text=f"🎬 开始下载第{chapter_num}话..."
        )
        
        # 初始化
        fetcher = ManhuaGuiFetcherSelenium(headless=True)
        
        # 获取章节列表
        chapters = fetcher.get_chapters(COMIC_URL)
        
        # 找到指定章节
        target_chapter = None
        for chapter in chapters:
            if chapter['chapter_num'] == chapter_num:
                target_chapter = chapter
                break
        
        if not target_chapter:
            await bot.send_message(
                chat_id=CHAT_ID,
                text=f"❌ 未找到第{chapter_num}话\n\n可用章节：第1话 - 第{len(chapters)}话"
            )
            return
        
        # 获取图片
        await bot.send_message(
            chat_id=CHAT_ID,
            text=f"⬇️ 正在获取第{chapter_num}话的图片..."
        )
        
        images = fetcher.get_images(target_chapter['url'])
        
        if not images:
            await bot.send_message(
                chat_id=CHAT_ID,
                text=f"❌ 下载失败：没有获取到图片"
            )
            return
        
        # 下载图片
        comic_path = Path(SAVE_PATH) / "ONE PIECE航海王" / f"第{chapter_num}话"
        comic_path.mkdir(parents=True, exist_ok=True)
        
        import requests
        session = requests.Session()
        
        for i, img_url in enumerate(images, 1):
            # 下载
            response = session.get(img_url, timeout=30, verify=False)
            if response.status_code == 200:
                img_path = comic_path / f"{i:03d}.jpg"
                with open(img_path, 'wb') as f:
                    f.write(response.content)
                
                # 每张图片发送一次通知
                if i % 5 == 0:
                    await bot.send_message(
                        chat_id=CHAT_ID,
                        text=f"📊 进度: {i}/{len(images)} 张图片"
                    )
        
        # 发送完成消息
        total_size = sum(os.path.getsize(comic_path / f"{j:03d}.jpg") for j in range(1, len(images)+1))
        size_mb = total_size / (1024 * 1024)
        
        await bot.send_message(
            chat_id=CHAT_ID,
            text=f"✅ **第{chapter_num}话下载完成！**\n\n"
                 f"🖼️  图片数量: {len(images)}张\n"
                 f"💾 文件大小: {size_mb:.2f}MB\n"
                 f"📁 保存路径: {comic_path}"
        )
        
        # 清理
        fetcher.close()
        
        return True
        
    except Exception as e:
        logger.error(f"下载失败: {e}")
        import traceback
        traceback.print_exc()
        
        await bot.send_message(
            chat_id=CHAT_ID,
            text=f"❌ **下载失败！**\n\n"
                 f"⚠️ {str(e)[:300]}"
        )
        
        return False


async def main():
    """主函数"""
    if len(sys.argv) < 2:
        await download_chapter("1172")  # 默认下载第1172话
    else:
        chapter_num = sys.argv[1]
        await download_chapter(chapter_num)


if __name__ == "__main__":
    asyncio.run(main())
