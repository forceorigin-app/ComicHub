"""
ONE PIECE 简化版下载器 - 带重试机制
使用原版 fetcher_selenium (直连模式）
失败后自动重试 3 次
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
HEARTBEAT_INTERVAL = 600  # 10分钟
STATE_FILE = "/Users/force/.openclaw/workspace/memory/download_state_simple.json"
LOG_FILE = "/tmp/download_simple_clean.log"
MAX_RETRIES = 3  # 失败后重试 3 次

logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RetryDownloader:
    """带重试机制的下载器"""
    
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
        self.retries_left = MAX_RETRIES  # 剩余重试次数
        
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
            logger.info("消息已发送")
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
        retry_status = f"（剩余重试: {self.retries_left}）" if self.retries_left < MAX_RETRIES else ""
        message = (
            f"ONE PIECE 下载进展\n"
            f"上次心跳: {elapsed_minutes}分钟前\n\n"
            f"下载进度:\n"
            f"  当前章节: 第{self.current_chapter}话\n"
            f"  总章节: {total}\n"
            f"  完成率: {percent:.1f}%\n\n"
            f"下载统计:\n"
            f"  已完成: {self.success_count}章\n"
            f"  已失败: {self.fail_count}章\n"
            f"  重试状态: {retry_status}\n"
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
            'total_chapters': len(self.chapters),
            'retries_left': self.retries_left
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
                    self.retries_left = state.get('retries_left', MAX_RETRIES)
                    
                    logger.warning(f"状态已加载: 当前第{self.current_chapter}话")
                    return True
            except Exception as e:
                logger.error(f"加载状态失败: {e}")
        return False
    
    async def download_chapter(self, chapter):
        """下载单个章节（带重试机制）"""
        self.current_chapter += 1
        self.download_count += 1
        
        title = chapter['title']
        chapter_num = chapter['chapter_num']
        url = chapter['url']
        
        # 重试循环
        for attempt in range(1, MAX_RETRIES + 1):
            try:
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
                    # 下载图片
                    response = session.get(img_url, timeout=30, verify=False)
                    if response.status_code == 200:
                        img_path = comic_path / f"{i:03d}.jpg"
                        with open(img_path, 'wb') as f:
                            f.write(response.content)
                        
                        # 短暂延迟
                        await asyncio.sleep(0.2)
                
                self.success_count += 1
                self.retries_left = MAX_RETRIES  # 重置重试次数
                
                # 每10章保存一次状态
                if self.success_count % 10 == 0:
                    self.save_state()
                
                return True
                
            except Exception as e:
                # 重试失败
                logger.error(f"尝试 {attempt}/{MAX_RETRIES} 失败: {title}, 错误: {e}")
                
                if attempt < MAX_RETRIES:
                    # 等待后重试
                    await asyncio.sleep(3)
                    self.retries_left = MAX_RETRIES - attempt
                else:
                    # 全部重试失败
                    self.fail_count += 1
                    self.retries_left = MAX_RETRIES
                    
                    # 记录失败
                    logger.error(f"章节 {chapter_num} 下载失败（{MAX_RETRIES} 次重试后跳过）")
                    
                    # 保存状态
                    self.save_state()
                    
                    # 检查连续失败
                    if self.fail_count >= 10:
                        logger.error("连续失败过多，停止下载")
                        return False
        
        return False
    
    async def run(self):
        """运行下载器（带重试 + 心跳）"""
        try:
            # 初始化
            self.fetcher = ManhuaGuiFetcherSelenium(headless=True, use_proxy=False)
            self.db = Database()
            
            # 获取章节列表
            chapters = self.fetcher.get_chapters(self.comic_url)
            self.chapters = chapters
            total = len(chapters)
            
            # 加载状态
            self.load_state()
            
            # 计算从第几章开始
            start_chapter = self.current_chapter + 1
            
            # 发送初始化消息
            await self.send_message(
                f"ONE PIECE 下载器已启动（带重试机制）\n\n"
                f"总章节: {total}\n"
                f"当前章节: 第{start_chapter}话\n"
                f"重试次数: {MAX_RETRIES}次\n"
                f"心跳间隔: 每10分钟汇总\n\n"
                f"开始下载第{start_chapter}话..."
            )
            
            logger.warning(f"初始化成功，共 {total} 个章节")
            
            # 开始下载
            for i, chapter in enumerate(self.chapters[self.current_chapter:], 1):
                # 检查是否需要发送心跳
                elapsed = datetime.now() - self.last_heartbeat
                if elapsed.total_seconds() >= HEARTBEAT_INTERVAL:
                    await self.send_heartbeat()
                    self.save_state()
                
                # 下载章节（带重试）
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
                f"保存路径: {self.save_path}"
            )


async def main():
    """主函数"""
    downloader = RetryDownloader()
    await downloader.run()


if __name__ == "__main__":
    asyncio.run(main())
