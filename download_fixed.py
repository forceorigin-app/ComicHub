"""
ONE PIECE 下载器 - 修复版（使用 fetcher_selenium_fixed）
每10分钟心跳汇总
"""
import asyncio
import logging
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

from fetcher_selenium_fixed import ManhuaGuiFetcherSeleniumV8
from database import Database
from telegram import Bot

# 配置
COMIC_URL = "https://m.manhuagui.com/comic/1128/"
SAVE_PATH = "/Users/force/data/comics"
TOKEN = "8308151445:AAEhS3oZ880gcA3-16-FfHMglzvZ2NalwK0"
CHAT_ID = "8260462836"
HEARTBEAT_INTERVAL = 600  # 10分钟 = 600秒
STATE_FILE = "/Users/force/.openclaw/workspace/memory/download_state.json"
LOG_FILE = "/tmp/download_fixed.log"

logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FixedHeartbeatDownloader:
    """修复版心跳下载器"""
    
    def __init__(self):
        self.comic_url = COMIC_URL
        self.save_path = SAVE_PATH
        self.token = TOKEN
        self.chat_id = CHAT_ID
        
        # 状态
        self.last_heartbeat = datetime.now()
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
    
    async def send_heartbeat(self):
        """发送心跳汇总"""
        now = datetime.now()
        elapsed = now - self.last_heartbeat
        elapsed_minutes = int(elapsed.total_seconds() / 60)
        
        total = len(self.chapters)
        progress = self.current_chapter
        percent = (progress / total) * 100 if total > 0 else 0
        
        # 发送汇总消息
        message = (
            f"ONE PIECE 下载进展（修复版）\n"
            f"上次心跳: {elapsed_minutes}分钟前\n\n"
            f"下载进度:\n"
            f"  当前章节: 第{self.current_chapter}话\n"
            f"  总章节: {total}\n"
            f"  完成率: {percent:.1f}%\n\n"
            f"下载统计:\n"
            f"  已完成: {self.success_count}章\n"
            f"  已失败: {self.fail_count}章\n"
        )
        
        await self.send_message(message)
        self.last_heartbeat = now
    
    def save_state(self):
        """保存下载状态"""
        state = {
            'last_sync': datetime.now().isoformat(),
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
                    self.download_count = state.get('download_count', 0)
                    self.success_count = state.get('success_count', 0)
                    self.fail_count = state.get('fail_count', 0)
                    self.current_chapter = state.get('current_chapter', 0)
                    
                    logger.warning(f"状态已加载: 当前第{self.current_chapter}话")
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
        url = chapter['url']
        
        try:
            # 不发任何通知
            
            # 使用修复版的 fetcher 获取图片
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
            
            # 不发完成通知
            
            # 每10章保存一次状态
            if self.success_count % 10 == 0:
                self.save_state()
            
            return True
            
        except Exception as e:
            self.fail_count += 1
            logger.error(f"下载失败: {title}, 错误: {e}")
            
            # 不发失败通知
            
            # 失败后继续
            await asyncio.sleep(3)
            return False
    
    async def run(self):
        """运行下载器（带心跳）"""
        try:
            # 初始化
            self.fetcher = ManhuaGuiFetcherSeleniumV8(headless=True)
            self.db = Database()
            
            # 获取章节列表
            chapters = self.fetcher.get_chapters(self.comic_url)
            self.chapters = chapters
            total = len(chapters)
            
            # 发送初始化消息
            await self.send_message(
                f"ONE PIECE 下载器已启动（修复版）\n\n"
                f"✅ 已修复代理问题\n"
                f"总章节: {total}\n"
                f"当前章节: 第1话\n"
                f"心跳间隔: 每10分钟汇总\n\n"
                f"开始下载第1话..."
            )
            
            logger.warning(f"初始化成功，共 {total} 个章节")
            
            # 开始下载
            for i, chapter in enumerate(self.chapters, 1):
                # 检查是否需要发送心跳
                elapsed = datetime.now() - self.last_heartbeat
                if elapsed.total_seconds() >= HEARTBEAT_INTERVAL:
                    await self.send_heartbeat()
                    self.save_state()
                
                # 下载章节
                success = await self.download_chapter(chapter)
                
                # 短暂休息
                await asyncio.sleep(1)
        
        except KeyboardInterrupt:
            logger.warning("下载被中断")
            await self.send_message(
                f"ONE PIECE 下载已停止\n\n"
                f"当前进度: 第{self.current_chapter}话\n"
                f"已完成: {self.success_count}章\n"
                f"失败: {self.fail_count}章\n"
            )
        
        finally:
            # 清理
            if self.fetcher:
                self.fetcher.close()
            if self.db:
                self.db.close()
            
            # 发送完成消息
            total = len(self.chapters)
            await self.send_message(
                f"ONE PIECE 下载完成\n\n"
                f"总章节: {total}\n"
                f"已完成: {self.success_count}\n"
                f"失败: {self.fail_count}\n"
                f"保存路径: {self.save_path}\n\n"
                f"✅ 代理问题已修复，下载应该更稳定"
            )


async def main():
    """主函数"""
    downloader = FixedHeartbeatDownloader()
    await downloader.run()


if __name__ == "__main__":
    asyncio.run(main())
