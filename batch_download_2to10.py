#!/usr/bin/env python3
"""
ONE PIECE 批量下载器 - 第2-10话
每30分钟同步一次进展
"""
import asyncio
import logging
from pathlib import Path
import os
import traceback
from datetime import datetime, timedelta

from fetcher_selenium import ManhuaGuiFetcherSelenium
from telegram import Bot

# 配置
COMIC_URL = "https://m.manhuagui.com/comic/1128/"
SAVE_PATH = "/Users/force/data/comics"
TOKEN = "8308151445:AAEhS3oZ880gcA3-16-FfHMglzvZ2NalwK0"
CHAT_ID = "8260462836"
START_CHAPTER = 2
END_CHAPTER = 10
HEARTBEAT_INTERVAL = 1800  # 30分钟 = 1800秒

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BatchDownloader:
    """批量下载器"""

    def __init__(self):
        self.bot = Bot(token=TOKEN)
        self.chat_id = CHAT_ID
        self.start_chapter = START_CHAPTER
        self.end_chapter = END_CHAPTER

        # 统计
        self.total_chapters = END_CHAPTER - START_CHAPTER + 1
        self.current_chapter = START_CHAPTER
        self.downloaded_count = 0
        self.success_count = 0
        self.fail_count = 0

        # 进度
        self.last_heartbeat = datetime.now()
        self.chapters_to_download = []

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
        """发送心跳汇总（每30分钟）"""
        now = datetime.now()
        elapsed = now - self.last_heartbeat
        elapsed_minutes = int(elapsed.total_seconds() / 60)

        progress = self.downloaded_count
        percent = (progress / self.total_chapters) * 100

        # 计算已下载的磁盘大小
        total_size = 0
        for i in range(START_CHAPTER, self.current_chapter):
            chapter_path = Path(SAVE_PATH) / "ONE PIECE航海王" / f"第{i}话"
            if chapter_path.exists():
                for file in chapter_path.glob("*.*"):
                    total_size += file.stat().st_size
        size_mb = total_size / (1024 * 1024)

        # 发送汇总消息
        message = (
            f"ONE PIECE 下载进展\n"
            f"上次心跳: {elapsed_minutes}分钟前\n\n"
            f"📚 下载进度:\n"
            f"  当前章节: 第{self.current_chapter}话\n"
            f"  进度范围: 第{START_CHAPTER}-{END_CHAPTER}话\n"
            f"  完成率: {percent:.1f}% ({self.downloaded_count}/{self.total_chapters}话)\n\n"
            f"📊 下载统计:\n"
            f"  成功: {self.success_count}话\n"
            f"  失败: {self.fail_count}话\n"
            f"  磁盘占用: {size_mb:.2f}MB\n"
        )

        await self.send_message(message)
        self.last_heartbeat = now

    async def download_chapter(self, chapter_num: int, chapter_url: str):
        """下载单个章节"""
        try:
            # 获取图片
            print(f"正在获取第{chapter_num}话的图片...")
            images = self.fetcher.get_images(chapter_url)

            if not images:
                raise Exception("没有获取到图片")

            # 下载图片
            comic_path = Path(SAVE_PATH) / "ONE PIECE航海王" / f"第{chapter_num}话"
            comic_path.mkdir(parents=True, exist_ok=True)

            import requests
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
                'Referer': chapter_url,
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            })

            # 从 Selenium 获取 cookies
            for cookie in self.fetcher.driver.get_cookies():
                session.cookies.set(cookie['name'], cookie['value'])

            success_count = 0
            fail_count = 0

            for i, img_url in enumerate(images, 1):
                print(f"  下载 {i}/{len(images)}...", end='\r')
                try:
                    response = session.get(img_url, timeout=30, verify=False)
                    if response.status_code == 200:
                        img_path = comic_path / f"{i:03d}.jpg"
                        with open(img_path, 'wb') as f:
                            f.write(response.content)
                        success_count += 1
                    else:
                        fail_count += 1
                except Exception as e:
                    fail_count += 1
                    logger.error(f"图片下载失败: {e}")

            if success_count == 0:
                raise Exception(f"所有图片下载失败（失败: {fail_count}）")

            # 计算文件大小
            total_size = sum(f.stat().st_size for f in comic_path.glob("*.*"))
            size_mb = total_size / (1024 * 1024)

            print(f"\n✅ 第{chapter_num}话下载完成！")
            print(f"   图片: {success_count}/{len(images)}")
            print(f"   大小: {size_mb:.2f}MB")

            self.success_count += 1
            return True

        except Exception as e:
            logger.error(f"下载第{chapter_num}话失败: {e}")
            traceback.print_exc()
            self.fail_count += 1
            return False

    async def run(self):
        """运行下载器（带心跳）"""
        try:
            # 初始化
            self.fetcher = ManhuaGuiFetcherSelenium(headless=True)

            # 获取章节列表
            print("正在获取章节列表...")
            all_chapters = self.fetcher.get_chapters(COMIC_URL)
            print(f"总章节数: {len(all_chapters)}")

            # 找到第2-10话
            for chapter in all_chapters:
                chapter_num = int(chapter['chapter_num'])
                if START_CHAPTER <= chapter_num <= END_CHAPTER:
                    self.chapters_to_download.append(chapter)

            # 确保按章节号排序
            self.chapters_to_download.sort(key=lambda x: int(x['chapter_num']))

            print(f"准备下载: {len(self.chapters_to_download)} 个章节")
            for chapter in self.chapters_to_download:
                print(f"  - 第{chapter['chapter_num']}话: {chapter['title']}")

            # 发送启动消息
            await self.send_message(
                f"🚀 ONE PIECE 批量下载已启动\n\n"
                f"📚 下载范围: 第{START_CHAPTER}-{END_CHAPTER}话\n"
                f"📊 总章节数: {len(self.chapters_to_download)}\n"
                f"💾 保存路径: {SAVE_PATH}\n"
                f"⏰ 心跳间隔: 每30分钟同步进展\n\n"
                f"开始下载第{START_CHAPTER}话..."
            )

            # 开始下载
            for chapter in self.chapters_to_download:
                chapter_num = int(chapter['chapter_num'])
                self.current_chapter = chapter_num

                # 检查是否需要发送心跳
                elapsed = datetime.now() - self.last_heartbeat
                if elapsed.total_seconds() >= HEARTBEAT_INTERVAL:
                    await self.send_heartbeat()

                # 下载章节
                success = await self.download_chapter(chapter_num, chapter['url'])
                self.downloaded_count += 1

                # 短暂休息
                await asyncio.sleep(0.5)

            # 发送完成消息
            total_size = 0
            for i in range(START_CHAPTER, END_CHAPTER + 1):
                chapter_path = Path(SAVE_PATH) / "ONE PIECE航海王" / f"第{i}话"
                if chapter_path.exists():
                    for file in chapter_path.glob("*.*"):
                        total_size += file.stat().st_size
            size_mb = total_size / (1024 * 1024)

            await self.send_message(
                f"✅ ONE PIECE 批量下载完成！\n\n"
                f"📚 下载范围: 第{START_CHAPTER}-{END_CHAPTER}话\n"
                f"📊 总章节: {len(self.chapters_to_download)}\n"
                f"✅ 成功: {self.success_count}\n"
                f"❌ 失败: {self.fail_count}\n"
                f"💾 磁盘占用: {size_mb:.2f}MB\n\n"
                f"保存路径: {SAVE_PATH}/ONE PIECE航海王/"
            )

        except KeyboardInterrupt:
            logger.warning("下载被中断")
            await self.send_message(
                f"⚠️ ONE PIECE 下载已停止\n\n"
                f"当前进度: 第{self.current_chapter}话\n"
                f"已完成: {self.success_count}话\n"
                f"失败: {self.fail_count}话\n"
            )

        except Exception as e:
            logger.error(f"下载失败: {e}")
            traceback.print_exc()
            await self.send_message(
                f"❌ ONE PIECE 下载出错\n\n"
                f"错误: {str(e)[:300]}"
            )

        finally:
            # 清理
            if hasattr(self, 'fetcher') and self.fetcher:
                self.fetcher.close()


async def main():
    """主函数"""
    downloader = BatchDownloader()
    await downloader.run()


if __name__ == "__main__":
    asyncio.run(main())
