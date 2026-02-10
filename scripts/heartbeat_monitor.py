"""
ONE PIECE 下载监控 - 10分钟心跳
每10分钟检查下载状态并发送汇总报告
"""
import asyncio
import logging
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

from telegram import Bot
from database import Database
from fetcher_selenium import ManhuaGuiFetcherSelenium

# 配置
TOKEN = "8308151445:AAEhS3oZ880gcA3-16-FfHMglzvZ2NalwK0"
CHAT_ID = "8260462836"
COMIC_URL = "https://m.manhuagui.com/comic/1128/"
SAVE_PATH = "/Users/force/data/comics"
STATE_FILE = "/Users/force/.openclaw/workspace/memory/heartbeat-state.json"
DOWNLOAD_STATE_FILE = "/Users/force/.openclaw/workspace/memory/download_state.json"
LOG_FILE = "/tmp/download_simple.log"

# 心跳间隔（10分钟）
HEARTBEAT_INTERVAL = 600

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HeartbeatMonitor:
    """心跳监控器"""
    
    def __init__(self):
        self.token = TOKEN
        self.chat_id = CHAT_ID
        self.bot = Bot(token=self.token)
        
        # 加载状态
        self.last_heartbeat = None
        self.download_state = {}
        self.sent_screenshots = set()
        
        self._load_state()
    
    def _load_state(self):
        """加载状态"""
        # 加载心跳状态
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, 'r') as f:
                    state = json.load(f)
                    self.last_heartbeat = state.get('lastCheck', None)
                    self.sent_screenshots = set(state.get('sentScreenshots', []))
                    logger.info(f"心跳状态已加载")
            except Exception as e:
                logger.error(f"加载心跳状态失败: {e}")
        
        # 加载下载状态
        if os.path.exists(DOWNLOAD_STATE_FILE):
            try:
                with open(DOWNLOAD_STATE_FILE, 'r') as f:
                    self.download_state = json.load(f)
                    logger.info(f"下载状态已加载: {self.download_state.get('current_chapter', 0)}/{self.download_state.get('total_chapters', 0)}")
            except Exception as e:
                logger.error(f"加载下载状态失败: {e}")
    
    def _save_state(self):
        """保存状态"""
        state = {
            'lastCheck': int(datetime.now().timestamp() * 1000),
            'sentScreenshots': list(self.sent_screenshots)
        }
        
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
    
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
    
    async def check_new_screenshots(self):
        """检查新截图"""
        screenshots = Path("/tmp").glob("terminal_screenshot_*.png")
        screenshots = sorted(screenshots, key=lambda p: p.stat().st_mtime, reverse=True)
        
        new_screenshots = []
        for screenshot in screenshots:
            if str(screenshot) not in self.sent_screenshots:
                new_screenshots.append(screenshot)
                self.sent_screenshots.add(str(screenshot))
        
        return new_screenshots
    
    async def check_download_status(self):
        """检查下载状态"""
        # 重新加载下载状态
        if os.path.exists(DOWNLOAD_STATE_FILE):
            try:
                with open(DOWNLOAD_STATE_FILE, 'r') as f:
                    self.download_state = json.load(f)
            except Exception as e:
                logger.error(f"重新加载下载状态失败: {e}")
        
        # 从日志中提取最近的活动
        recent_activity = []
        try:
            if os.path.exists(LOG_FILE):
                with open(LOG_FILE, 'r') as f:
                    lines = f.readlines()
                    # 获取最后100行
                    recent_lines = lines[-100:]
                    for line in recent_lines:
                        if '下载完成' in line or '下载失败' in line:
                            recent_activity.append(line.strip())
        except Exception as e:
            logger.error(f"读取日志失败: {e}")
        
        # 统计最近的成功和失败
        recent_success = len([line for line in recent_activity if '下载完成' in line])
        recent_failed = len([line for line in recent_activity if '下载失败' in line])
        
        return {
            'current_chapter': self.download_state.get('current_chapter', 0),
            'total_chapters': self.download_state.get('total_chapters', 626),
            'success_count': self.download_state.get('success_count', 0),
            'fail_count': self.download_state.get('fail_count', 0),
            'recent_success': recent_success,
            'recent_failed': recent_failed
        }
    
    async def send_heartbeat(self):
        """发送心跳报告"""
        now = datetime.now()
        
        # 检查新截图
        new_screenshots = await self.check_new_screenshots()
        
        # 检查下载状态
        download_status = await self.check_download_status()
        
        # 计算进度
        current = download_status['current_chapter']
        total = download_status['total_chapters']
        percent = (current / total) * 100 if total > 0 else 0
        
        # 计算上次心跳时间
        if self.last_heartbeat:
            last_time = datetime.fromtimestamp(self.last_heartbeat / 1000)
            elapsed = now - last_time
            elapsed_minutes = int(elapsed.total_seconds() / 60)
        else:
            elapsed_minutes = 0
        
        # 发送消息
        message = (
            f"📊 **ONE PIECE 下载心跳**\n\n"
            f"⏱️  上次心跳: {elapsed_minutes}分钟前\n\n"
            f"📚 **下载进度**\n"
            f"📖 当前章节: 第{download_status['current_chapter']}话\n"
            f"📊 完成进度: {percent:.1f}% ({current}/{total})\n"
            f"✅ 已成功: {download_status['success_count']}章\n"
            f"❌ 已失败: {download_status['fail_count']}章\n\n"
            f"📊 **最近10分钟**\n"
            f"✅ 新成功: {download_status['recent_success']}章\n"
            f"❌ 新失败: {download_status['recent_failed']}章\n"
        )
        
        await self.send_message(message)
        
        # 如果有新截图，发送最后3张
        if new_screenshots:
            message = f"📸 **终端截屏** ({len(new_screenshots)}张新)"
            await self.send_message(message)
            
            # 发送最后3张截图
            for screenshot in new_screenshots[-3:]:
                try:
                    with open(screenshot, 'rb') as photo:
                        await self.bot.send_photo(
                            chat_id=self.chat_id,
                            photo=photo,
                            caption=f"{screenshot.name}"
                        )
                        logger.info(f"截图已发送: {screenshot}")
                except Exception as e:
                    logger.error(f"发送截图失败: {screenshot}")
        
        # 保存状态
        self._save_state()
        self.last_heartbeat = now
    
    async def run(self):
        """运行心跳监控"""
        logger.info("心跳监控已启动")
        
        while True:
            try:
                await self.send_heartbeat()
                
                # 等待10分钟
                logger.info(f"等待 {HEARTBEAT_INTERVAL} 秒...")
                await asyncio.sleep(HEARTBEAT_INTERVAL)
                
            except KeyboardInterrupt:
                logger.info("心跳监控已停止")
                await self.send_message("⏸️ **心跳监控已停止**")
                break
            except Exception as e:
                logger.error(f"心跳错误: {e}")
                await asyncio.sleep(60)  # 出错后等待1分钟


async def main():
    """主函数"""
    monitor = HeartbeatMonitor()
    
    # 发送启动消息
    await monitor.send_message("❤️ **ONE PIECE 下载心跳监控已启动**\n\n"
                              "📊 每10分钟汇总一次进展\n"
                              "📸 发送最新终端截屏\n\n"
                              "🚀 下载器正在后台运行...")
    )
    
    # 等待2秒后开始
    await asyncio.sleep(2)
    
    # 启动心跳
    await monitor.run()


if __name__ == "__main__":
    asyncio.run(main())
