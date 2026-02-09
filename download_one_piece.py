"""
ComicHub 批量下载 - ONE PIECE
"""
import asyncio
import logging
from pathlib import Path

from fetcher_selenium import ManhuaGuiFetcherSeleniumV8
from batch_download import BatchDownloader
from database import Database
from telegram import Bot
import os

# 配置
COMIC_URL = "https://m.manhuagui.com/comic/1128/"  # ONE PIECE
SAVE_PATH = "/Users/force/data/comics"
TOKEN = "8308151445:AAEhS3oZ880gcA3-16-FfHMglzvZ2NalwK0"
CHAT_ID = "8260462836"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def download_one_piece(start: int = 1, end: int = None):
    """
    下载 ONE PIECE 漫画
    
    Args:
        start: 起始章节号
        end: 结束章节号（None 表示全部）
    """
    bot = Bot(token=TOKEN)
    
    try:
        # 初始化
        fetcher = ManhuaGuiFetcherSeleniumV8(headless=True)
        db = Database()
        downloader = BatchDownloader(db=db, save_path=SAVE_PATH)
        
        # 获取漫画信息
        await bot.send_message(
            chat_id=CHAT_ID,
            text=f"🎬 **开始下载 ONE PIECE**\n\n"
                 f"📚 URL: {COMIC_URL}\n"
                 f"📖 章节: {start} - {'全部' if end is None else end}\n"
                 f"💾 保存路径: {SAVE_PATH}\n"
        )
        
        # 获取章节列表
        chapters = fetcher.get_chapters(COMIC_URL)
        total_chapters = len(chapters)
        
        if end is None:
            end = total_chapters
        
        # 过滤章节
        target_chapters = []
        for ch in chapters:
            try:
                ch_num = int(ch['chapter_num'])
                if start <= ch_num <= end:
                    target_chapters.append(ch)
            except:
                pass
        
        logger.info(f"目标章节: {len(target_chapters)} ({start}-{end})")
        
        # 发送开始消息
        await bot.send_message(
            chat_id=CHAT_ID,
            text=f"🚀 **开始下载！**\n\n"
                 f"📚 目标章节: {len(target_chapters)}\n"
                 f"📖 章节范围: 第{start}话 - 第{end}话\n"
                 f"⏱️  预计时间: 约 {len(target_chapters) * 30} - {len(target_chapters) * 60} 秒\n"
        )
        
        # 逐章下载
        success_count = 0
        fail_count = 0
        
        for i, chapter in enumerate(target_chapters, 1):
            ch_title = chapter['title']
            ch_url = chapter['url']
            
            # 下载章节
            try:
                await bot.send_message(
                    chat_id=CHAT_ID,
                    text=f"⬇️ [{i}/{len(target_chapters)}] 下载中...\n"
                         f"📖 {ch_title}\n"
                         f"🔗 {ch_url}"
                )
                
                # 调用下载器（同步）
                downloader.download_chapters(
                    comic_id=1,
                    chapters=[chapter],
                    use_proxy=False
                )
                
                success_count += 1
                
                # 发送完成消息
                await bot.send_message(
                    chat_id=CHAT_ID,
                    text=f"✅ [{i}/{len(target_chapters)}] 下载完成！\n"
                         f"📖 {ch_title}"
                )
                
                # 延迟
                await asyncio.sleep(2)
                
            except Exception as e:
                fail_count += 1
                logger.error(f"下载失败: {ch_title}, 错误: {e}")
                
                await bot.send_message(
                    chat_id=CHAT_ID,
                    text=f"❌ [{i}/{len(target_chapters)}] 下载失败！\n"
                         f"📖 {ch_title}\n"
                         f"⚠️ {str(e)[:200]}"
                )
        
        # 关闭
        fetcher.close()
        db.close()
        
        # 发送完成消息
        await bot.send_message(
            chat_id=CHAT_ID,
            text=f"🎉 **下载完成！**\n\n"
                 f"✅ 成功: {success_count}\n"
                 f"❌ 失败: {fail_count}\n"
                 f"📖 章节: {start} - {end}\n"
                 f"💾 保存路径: {SAVE_PATH}\n"
        )
        
    except Exception as e:
        logger.error(f"下载过程出错: {e}")
        
        await bot.send_message(
            chat_id=CHAT_ID,
            text=f"❌ **下载过程出错！**\n\n⚠️ {str(e)}"
        )


if __name__ == "__main__":
    import sys
    
    # 默认参数
    start_chapter = 1
    end_chapter = None  # None 表示全部
    
    # 解析命令行参数
    if len(sys.argv) > 1:
        start_chapter = int(sys.argv[1])
    if len(sys.argv) > 2:
        end_chapter = int(sys.argv[2])
    
    print(f"下载 ONE PIECE: 第{start_chapter}话 - {'全部' if end_chapter is None else f'第{end_chapter}话'}")
    print(f"预计时间: {626 if end_chapter is None else end_chapter - start_chapter + 1} * 30 - {626 if end_chapter is None else end_chapter - start_chapter + 1} * 60} 秒")
    
    # 询问确认
    response = input(f"\n确定开始下载吗？(y/n): ")
    if response.lower() != 'y':
        print("已取消")
        sys.exit(0)
    
    # 开始下载
    asyncio.run(download_one_piece(start_chapter, end_chapter))
