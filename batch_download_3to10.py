#!/usr/bin/env python3
"""
ONE PIECE 批量下载器 - 第3-10话（修复版）
每30分钟同步一次进展
"""
import asyncio
import logging
from pathlib import Path
import os
import traceback
from datetime import datetime

from fetcher_selenium import ManhuaGuiFetcherSelenium
from telegram import Bot

# 配置
COMIC_URL = "https://m.manhuagui.com/comic/1128/"
SAVE_PATH = "/Users/force/data/comics"
TOKEN = "8308151445:AAEhS3oZ880gcA3-16-FfHMglzvZ2NalwK0"
CHAT_ID = "8260462836"
START_CHAPTER = 3
END_CHAPTER = 10
HEARTBEAT_INTERVAL = 1800  # 30分钟 = 1800秒

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def download_chapter(fetcher, chapter_num: int, chapter_url: str):
    """下载单个章节"""
    try:
        # 获取图片
        print(f"正在获取第{chapter_num}话的图片...")
        images = fetcher.get_images(chapter_url)

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
        for cookie in fetcher.driver.get_cookies():
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

        return True, size_mb

    except Exception as e:
        logger.error(f"下载第{chapter_num}话失败: {e}")
        traceback.print_exc()
        return False, 0


async def main():
    """主函数"""
    try:
        bot = Bot(token=TOKEN)
        chat_id = CHAT_ID

        # 初始化
        fetcher = ManhuaGuiFetcherSelenium(headless=True)

        # 获取章节列表
        print("正在获取章节列表...")
        all_chapters = fetcher.get_chapters(COMIC_URL)
        print(f"总章节数: {len(all_chapters)}")

        # 找到第3-10话
        chapters_to_download = []
        for chapter in all_chapters:
            chapter_num = int(chapter['chapter_num'])
            if START_CHAPTER <= chapter_num <= END_CHAPTER:
                chapters_to_download.append(chapter)

        # 按章节号排序
        chapters_to_download.sort(key=lambda x: int(x['chapter_num']))

        print(f"\n准备下载: {len(chapters_to_download)} 个章节")
        for chapter in chapters_to_download:
            print(f"  - 第{chapter['chapter_num']}话: {chapter['title']}")

        # 发送启动消息
        await bot.send_message(
            chat_id=chat_id,
            text=(
                f"🚀 ONE PIECE 批量下载已启动（修复版）\n\n"
                f"📚 下载范围: 第{START_CHAPTER}-{END_CHAPTER}话\n"
                f"📊 总章节数: {len(chapters_to_download)}\n"
                f"💾 保存路径: {SAVE_PATH}\n"
                f"⏰ 心跳间隔: 每30分钟同步进展\n\n"
                f"开始下载第{START_CHAPTER}话..."
            )
        )

        # 开始下载
        success_count = 0
        fail_count = 0
        total_size = 0

        for i, chapter in enumerate(chapters_to_download, 1):
            chapter_num = int(chapter['chapter_num'])

            # 下载章节
            success, size_mb = await download_chapter(fetcher, chapter_num, chapter['url'])

            if success:
                success_count += 1
                total_size += size_mb
            else:
                fail_count += 1

            # 短暂休息
            await asyncio.sleep(0.5)

        # 发送完成消息
        await bot.send_message(
            chat_id=chat_id,
            text=(
                f"✅ ONE PIECE 批量下载完成！\n\n"
                f"📚 下载范围: 第{START_CHAPTER}-{END_CHAPTER}话\n"
                f"📊 总章节: {len(chapters_to_download)}\n"
                f"✅ 成功: {success_count}\n"
                f"❌ 失败: {fail_count}\n"
                f"💾 磁盘占用: {total_size:.2f}MB\n\n"
                f"保存路径: {SAVE_PATH}/ONE PIECE航海王/"
            )
        )

        # 清理
        fetcher.close()

    except Exception as e:
        logger.error(f"下载失败: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
