"""
ONE PIECE 静默下载器 - 无打扰模式
只在最终完成时发一条通知
"""
import asyncio
import logging
from pathlib import Path
from datetime import datetime
import json
import os

from fetcher_selenium import ManhuaGuiFetcherSelenium
from database import Database
from telegram import Bot

# 配置
COMIC_URL = "https://m.manhuagui.com/comic/1128/"
SAVE_PATH = "/Users/force/data/comics"
TOKEN = "8308151445:AAEhS3oZ880gcA3-16-FfHMglzvZ2NalwK0"
CHAT_ID = "8260462836"
STATE_FILE = "/Users/force/.openclaw/workspace/memory/download_state.json"

logging.basicConfig(
    level=logging.WARNING,  # 只显示警告，不显示 INFO
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SilentDownloader:
    """静默下载器 - 无打扰模式"""
    
    def __init__(self):
        self.comic_url = COMIC_URL
        self.save_path = SAVE_PATH
        self.token = TOKEN
        self.chat_id = CHAT_ID
        
        # 状态
        self.download_count = 0
        self.success_count = 0
        self.fail_count = 0
        self.current_chapter = 0
        
        # 组件
        self.bot = Bot(token=self.token)
        self.fetcher = None
        self.db = None
        self.chapters = []
    
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
    
    def load_state(self):
        """加载下载状态"""
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, 'r') as f:
                    state = json.load(f)
                    self.download_count = state.get('download_count', 0)
                    self.success_count = state.get('success_count', 0)
                    self.fail_count = state.get('fail_count', 0)
                    self.current_chapter = state.get('current_chapter', 0)
                    
                    logger.warning(f"状态已加载: 当前第{self.current_chapter}话，已完成{self.success_count}章")
                    return True
            except Exception as e:
                logger.error(f"加载状态失败: {e}")
        return False
    
    def save_state(self):
        """保存下载状态"""
        state = {
            'last_sync': datetime.now().isoformat(),
            'download_count': self.download_count,
            'success_count': self.success_count,
            'fail_count': self.fail_count,
            'current_chapter': self.current_chapter,
            'total_chapters': len(self.chapters) if self.chapters else 0
        }
        
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
    
    async def download_chapter(self, chapter):
        """下载单个章节（静默）"""
        self.current_chapter += 1
        self.download_count += 1
        
        title = chapter['title']
        chapter_num = chapter['chapter_num']
        url = chapter['url']
        
        try:
            # 不发通知
            
            # 使用 fetcher 获取图片
            images = self.fetcher.get_images(url)
            
            if not images:
                raise Exception("没有获取到图片")
            
            # 下载图片
            comic_path = Path(self.save_path) / "ONE PIECE航海王" / f"第{chapter_num}话"
            comic_path.mkdir(parents=True, exist_ok=True)
            
            import requests
            session = requests.Session()
            
            for i, img_url in enumerate(images, 1):
                # 不发进度通知
                
                # 下载图片
                response = session.get(img_url, timeout=30, verify=False)
                if response.status_code == 200:
                    img_path = comic_path / f"{i:03d}.jpg"
                    with open(img_path, 'wb') as f:
                        f.write(response.content)
                    
                    # 短暂延迟
                    await asyncio.sleep(0.3)
            
            self.success_count += 1
            
            # 保存状态（每10章保存一次）
            if self.success_count % 10 == 0:
                self.save_state()
            
            # 不发完成通知
            
            return True
            
        except Exception as e:
            self.fail_count += 1
            logger.error(f"下载失败: {title}, 错误: {e}")
            
            # 不发失败通知
            
            # 失败后继续
            await asyncio.sleep(3)
            return False
    
    async def run(self):
        """运行下载器"""
        try:
            # 初始化
            self.fetcher = ManhuaGuiFetcherSelenium(headless=True)
            self.db = Database()
            
            # 获取章节列表
            chapters = self.fetcher.get_chapters(self.comic_url)
            self.chapters = chapters
            total = len(chapters)
            
            # 加载状态
            self.load_state()
            
            # 发送启动消息（唯一的一条）
            start_chapter = self.current_chapter + 1
            await self.send_message(
                f"ONE PIECE 静默下载模式已启动\n\n"
                f"当前进度: 第{start_chapter}话 ({start_chapter}/{total})\n"
                f"已下载: 第{self.current_chapter}话\n"
                f"模式: 完成时才会通知\n\n"
                f"预计完成: 明天早上"
            )
            
            logger.warning(f"开始下载: 从第{start_chapter}话到第{total}话")
            
            # 开始下载（不发任何中间通知）
            for i, chapter in enumerate(self.chapters[self.current_chapter:], 1):
                # 下载章节
                success = await self.download_chapter(chapter)
                
                # 保存状态（每20章保存一次）
                if i % 20 == 0:
                    self.save_state()
                
                # 短暂休息
                await asyncio.sleep(1)
        
        except KeyboardInterrupt:
            logger.warning("下载被中断")
            # 发送中断消息
            await self.send_message(
                f"下载已暂停\n\n"
                f"当前进度: 第{self.current_chapter}话\n"
                f"已完成: {self.success_count}章\n"
                f"状态已保存"
            )
        
        finally:
            # 清理
            if self.fetcher:
                self.fetcher.close()
            if self.db:
                self.db.close()
            
            # 发送完成消息（只有完成或中断时发）
            total = len(self.chapters)
            await self.send_message(
                f"ONE PIECE 下载完成\n\n"
                f"总章节: {total}\n"
                f"已完成: {self.success_count}\n"
                f"失败: {self.fail_count}\n"
                f"保存路径: {self.save_path}\n\n"
                f"模式: 已停止，可以随时继续"
            )


async def main():
    """主函数"""
    downloader = SilentDownloader()
    await downloader.run()


if __name__ == "__main__":
    asyncio.run(main())
