"""
ComicHub ONE PIECE 简化下载器
按顺序下载 + 30分钟同步
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
SYNC_INTERVAL = 1800  # 30分钟

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SimpleDownloader:
    """简化下载器"""
    
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
    
    async def send_progress(self):
        """发送进展报告"""
        elapsed = datetime.now() - self.last_sync
        elapsed_minutes = int(elapsed.total_seconds() / 60)
        
        total = len(self.chapters)
        progress = self.current_chapter
        percent = (progress / total) * 100 if total > 0 else 0
        
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
        
        state_file = "/tmp/download_state.json"
        os.makedirs(os.path.dirname(state_file), exist_ok=True)
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def load_state(self):
        """加载下载状态"""
        state_file = "/tmp/download_state.json"
        if os.path.exists(state_file):
            try:
                with open(state_file, 'r') as f:
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
        """下载单个章节（简化版）"""
        self.current_chapter += 1
        self.download_count += 1
        
        title = chapter['title']
        chapter_num = chapter['chapter_num']
        url = chapter['url']
        
        try:
            # 发送开始消息
            await self.send_message(
                f"⬇️ [{self.current_chapter}/{len(self.chapters)}] 下载中...\n\n"
                f"📖 {title}\n"
                f"🔗 {url}"
            )
            
            # 使用 fetcher 获取图片
            images = self.fetcher.get_images(url)
            
            if not images:
                raise Exception("没有获取到图片")
            
            # 下载图片（简单实现）
            comic_path = Path(self.save_path) / "ONE PIECE航海王" / f"第{chapter_num}话"
            comic_path.mkdir(parents=True, exist_ok=True)
            
            import requests
            session = requests.Session()
            
            for i, img_url in enumerate(images, 1):
                try:
                    # 发送进展
                    if i % 5 == 0:
                        await self.send_message(
                            f"📊 [{self.current_chapter}/{len(self.chapters)}] {title}\n"
                            f"🖼️  下载中... {i}/{len(images)} 张"
                        )
                    
                    # 下载图片
                    response = session.get(img_url, timeout=30, verify=False)
                    if response.status_code == 200:
                        img_path = comic_path / f"{i:03d}.jpg"
                        with open(img_path, 'wb') as f:
                            f.write(response.content)
                        
                        # 延迟
                        await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"下载图片失败: {i}, 错误: {e}")
            
            self.success_count += 1
            
            # 发送完成消息
            await self.send_message(
                f"✅ [{self.current_chapter}/{len(self.chapters)}] 下载完成！\n\n"
                f"📖 {title}\n"
                f"🖼️  图片数量: {len(images)}张"
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
                f"❌ [{self.current_chapter}/{len(self.chapters)}] 下载失败！\n\n"
                f"📖 {title}\n"
                f"⚠️  {str(e)[:200]}"
            )
            
            # 失败后继续
            await asyncio.sleep(5)
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
            
            # 发送初始化消息
            await self.send_message(
                f"🎬 **ONE PIECE 下载器已初始化**\n\n"
                f"📚 总章节: {total}\n"
                f"📖 当前章节: 第1话\n"
                f"💾 保存路径: {self.save_path}\n"
                f"⏱️  同步间隔: 30分钟\n\n"
                f"🚀 **开始下载第1话...**"
            )
            
            logger.info(f"初始化成功，共 {total} 个章节")
            
            # 开始下载
            for i, chapter in enumerate(self.chapters, 1):
                # 下载章节
                success = await self.download_chapter(chapter)
                
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
            
            # 发送完成消息
            total = len(self.chapters)
            await self.send_message(
                f"🎉 **ONE PIECE 下载完成！**\n\n"
                f"📚 总章节: {total}\n"
                f"✅ 成功: {self.success_count}\n"
                f"❌ 失败: {self.fail_count}\n"
                f"💾 保存路径: {self.save_path}"
            )


async def main():
    """主函数"""
    downloader = SimpleDownloader()
    await downloader.run()


if __name__ == "__main__":
    asyncio.run(main())
