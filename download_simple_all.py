"""
ONE PIECE 简化下载器
使用原版 fetcher_selenium，明确 use_proxy=False
"""
import asyncio
import logging
from pathlib import Path
from datetime import datetime

from fetcher_selenium import create_fetcher_selenium
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


async def download_all():
    """下载全部章节"""
    bot = Bot(token=TOKEN)
    
    try:
        # 初始化
        fetcher = create_fetcher_selenium(use_proxy=False, headless=True)
        db = Database()
        
        # 发送开始消息
        await bot.send_message(
            chat_id=CHAT_ID,
            text="ONE PIECE 下载器启动\n"
                 "模式: 直连 (use_proxy=False)\n"
                 "开始获取章节列表..."
        )
        
        # 获取章节列表
        chapters = fetcher.get_chapters(COMIC_URL)
        total = len(chapters)
        
        await bot.send_message(
            chat_id=CHAT_ID,
            text=f"获取到 {total} 个章节\n开始下载第1话..."
        )
        
        # 开始下载
        success = 0
        for i, chapter in enumerate(chapters, 1):
            chapter_num = chapter['chapter_num']
            title = chapter['title']
            url = chapter['url']
            
            try:
                # 获取图片
                images = fetcher.get_images(url)
                
                if not images:
                    await bot.send_message(
                        chat_id=CHAT_ID,
                        text=f"第{i}话下载失败: {title}\n没有获取到图片"
                    )
                    continue
                
                # 下载图片
                comic_path = Path(SAVE_PATH) / "ONE PIECE航海王" / f"第{chapter_num}话"
                comic_path.mkdir(parents=True, exist_ok=True)
                
                import requests
                session = requests.Session()
                
                for j, img_url in enumerate(images, 1):
                    response = session.get(img_url, timeout=30, verify=False)
                    if response.status_code == 200:
                        img_path = comic_path / f"{j:03d}.jpg"
                        with open(img_path, 'wb') as f:
                            f.write(response.content)
                    
                    await asyncio.sleep(0.2)
                
                success += 1
                
                # 每10章报告一次
                if success % 10 == 0:
                    await bot.send_message(
                        chat_id=CHAT_ID,
                        text=f"进度: {success}/{total} ({success/total*100:.1f}%)\n当前: 第{i}话 {title}"
                    )
                
            except Exception as e:
                await bot.send_message(
                    chat_id=CHAT_ID,
                    text=f"第{i}话下载失败: {title}\n错误: {str(e)[:200]}"
                )
        
        # 完成
        await bot.send_message(
            chat_id=CHAT_ID,
            text=f"ONE PIECE 下载完成！\n"
                 f"总章节: {total}\n"
                 f"已完成: {success}\n"
                 f"失败: {total - success}"
        )
        
        # 清理
        fetcher.close()
        db.close()
        
    except Exception as e:
        await bot.send_message(
            chat_id=CHAT_ID,
            text=f"下载器失败: {str(e)}"
        )
        logger.error(f"下载失败: {e}")
        import traceback
        traceback.print_exc()


asyncio.run(download_all())
