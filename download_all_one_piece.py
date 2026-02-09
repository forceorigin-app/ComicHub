"""
ComicHub 智能批量下载器 - ONE PIECE
功能：按顺序下载 + 进展同步 + 断点续传
"""
import asyncio
import logging
from pathlib import Path
from datetime import datetime, timedelta
import json
import os
import sys

from fetcher_selenium import ManhuaGuiFetcherSelenium
from batch_download import BatchDownloader
from database import Database
from telegram import Bot

# 配置
COMIC_URL = "https://m.manhuagui.com/comic/1128/"
SAVE_PATH = "/Users/force/data/comics"
TOKEN = "8308151445:AAEhS3oZ880gcA3-16-FfHMglzvZ2NalwK0"
CHAT_ID = "8260462836"
SYNC_INTERVAL = 1800  # 30分钟 = 1800秒
STATE_FILE = "/Users/force/.openclaw/workspace/memory/download_state.json"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OnePieceDownloader:
    """ONE PIECE 智能下载器"""
    
    def __init__(self):
        self.comic_url = COMIC_URL
        self.save_path = SAVE_PATH
        self.token = TOKEN
        self.chat_id = CHAT_ID
        
        # 状态
        self.last_sync = datetime.now()
        self.download_count = 0
        self.success_count = 0
        self.fail_count = 0
        self.current_chapter = 0
        
        # 组件
        self.bot = Bot(token=self.token)
        self.fetcher = None
        self.db = None
        self.downloader = None
        self.chapters = []
        
    async def initialize(self):
        """初始化下载器"""
        try:
            self.fetcher = ManhuaGuiFetcherSelenium(headless=True)
            self.db = Database()
            self.downloader = BatchDownloader(db=self.db, save_path=self.save_path)
            
            # 获取章节列表
            self.chapters = self.fetcher.get_chapters(self.comic_url)
            total = len(self.chapters)
            
            await self.send_message(
                f"🎬 **ONE PIECE 下载器已初始化**\n\n"
                f"📚 总章节: {total}\n"
                f"📖 当前章节: 第1话\n"
                f"💾 保存路径: {self.save_path}\n"
                f"⏱️  同步间隔: 30分钟\n\n"
                f"🚀 **开始下载第1话...**"
            )
            
            logger.info(f"初始化成功，共 {total} 个章节")
            return True
            
        except Exception as e:
            logger.error(f"初始化失败: {e}")
            await self.send_message(f"❌ **初始化失败**: {str(e)}")
            return False
    
    async def send_message(self, text):
        """发送消息到 Telegram"""
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=text,
                parse_mode='Markdown'
            )
            logger.info(f"消息已发送")
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
    
    async def send_photo(self, image_path, caption=""):
        """发送图片到 Telegram"""
        try:
            with open(image_path, 'rb') as photo:
                await self.bot.send_photo(
                    chat_id=self.chat_id,
                    photo=photo,
                    caption=caption
                )
            logger.info(f"图片已发送: {image_path}")
        except Exception as e:
            logger.error(f"发送图片失败: {image_path}: {e}")
    
    async def send_progress(self):
        """发送进展报告"""
        elapsed = datetime.now() - self.last_sync
        elapsed_minutes = int(elapsed.total_seconds() / 60)
        
        total = len(self.chapters)
        progress = self.current_chapter
        percent = (progress / total) * 100
        
        msg = (
            f"📊 **ONE PIECE 下载进展**\n\n"
            f"⏱️  上次同步: {elapsed_minutes}分钟前\n\n"
            f"📚 总章节: {total}\n"
            f"📖 当前进度: 第{self.current_chapter}话 ({percent:.1f}%)\n"
            f"✅ 已完成: {self.success_count}\n"
            f"❌ 失败: {self.fail_count}\n"
            f"📊 完成率: {percent:.1f}%\n\n"
            f"🚀 **继续下载第{self.current_chapter + 1}话...**"
        )
        
        await self.send_message(msg)
        self.last_sync = datetime.now()
    
    def save_state(self):
        """保存下载状态"""
        state = {
            'last_sync': self.last_sync.isoformat(),
            'download_count': self.download_count,
            'success_count': self.success_count,
            'fail_count': self.fail_count,
            'current_chapter': self.current_chapter,
            'total_chapters': len(self.chapters)
        }
        
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
    
    def load_state(self):
        """加载下载状态"""
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, 'r') as f:
                    state = json.load(f)
                    self.last_sync = datetime.fromisoformat(state.get('last_sync', datetime.now().isoformat()))
                    self.download_count = state.get('download_count', 0)
                    self.success_count = state.get('success_count', 0)
                    self.fail_count = state.get('fail_count', 0)
                    self.current_chapter = state.get('current_chapter', 0)
                    
                    logger.info(f"状态已加载: 当前第{self.current_chapter}话")
                    return True
            except Exception as e:
                logger.error(f"加载状态失败: {e}")
        return False
    
    async def download_chapter(self, chapter):
        """下载单个章节"""
        self.current_chapter += 1
        self.download_count += 1
        
        title = chapter['title']
        chapter_num = chapter['chapter_num']
        
        try:
            # 发送开始消息
            await self.send_message(
                f"⬇️ [{self.current_chapter}/{len(self.chapters)}] 下载中...\n"
                f"📖 {title}\n"
                f"🔗 {chapter['url']}"
            )
            
            # 下载章节
            self.downloader.download_chapters(
                comic_id=1,
                chapters=[chapter],
                use_proxy=False
            )
            
            self.success_count += 1
            
            # 发送完成消息
            comic_path = self.save_path / "ONE PIECE航海王" / f"第{chapter_num}话"
            image_count = len(list(comic_path.glob("*.jpg")))
            
            await self.send_message(
                f"✅ [{self.current_chapter}/{len(self.chapters)}] 下载完成！\n"
                f"📖 {title}\n"
                f"🖼️ 图片数量: {image_count}张"
            )
            
            # 检查是否需要同步
            elapsed = datetime.now() - self.last_sync
            if elapsed.total_seconds() >= SYNC_INTERVAL:
                await self.send_progress()
                self.save_state()
            
            return True
            
        except Exception as e:
            self.fail_count += 1
            logger.error(f"下载失败: {title}, 错误: {e}")
            
            await self.send_message(
                f"❌ [{self.current_chapter}/{len(self.chapters)}] 下载失败！\n"
                f"📖 {title}\n"
                f"⚠️ {str(e)[:200]}"
            )
            
            # 等待后继续
            await asyncio.sleep(5)
            return False
    
    async def run(self):
        """运行下载器"""
        # 初始化
        if not await self.initialize():
            return
        
        # 查找中断的章节
        start_index = 0
        if self.load_state():
            start_index = self.current_chapter
        
        await self.send_message(
            f"🔄 **恢复下载**\n"
            f"从第{start_index + 1}话开始继续..."
        )
        
        # 开始下载
        try:
            for i in range(start_index, len(self.chapters)):
                chapter = self.chapters[i]
                
                # 下载章节
                success = await self.download_chapter(chapter)
                
                if not success:
                    # 失败后继续
                    continue
                
                # 保存状态
                self.save_state()
                
                # 短暂休息
                await asyncio.sleep(2)
        
        except KeyboardInterrupt:
            logger.info("下载被中断")
            await self.send_message(
                f"⏸️ **下载已暂停**\n\n"
                f"📊 当前进度: 第{self.current_chapter}话\n"
                f"✅ 已完成: {self.success_count}\n"
                f"❌ 失败: {self.fail_count}\n\n"
                f"💾 状态已保存，可以随时继续"
            )
        
        finally:
            # 清理
            if self.fetcher:
                self.fetcher.close()
            if self.db:
                self.db.close()
            
            await self.send_message(
                f"🎉 **ONE PIECE 下载完成！**\n\n"
                f"📚 总章节: {len(self.chapters)}\n"
                f"✅ 成功: {self.success_count}\n"
                f"❌ 失败: {self.fail_count}\n"
                f"💾 保存路径: {self.save_path}"
            )


async def main():
    """主函数"""
    downloader = OnePieceDownloader()
    await downloader.run()


if __name__ == "__main__":
    asyncio.run(main())
