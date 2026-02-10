#!/usr/bin/env python3
"""
ONE PIECE 批量下载器 - 按时间顺序从前往后
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
HEARTBEAT_INTERVAL = 1800  # 30分钟 = 1800秒

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def download_chapter(fetcher, chapter: dict):
    """下载单个章节"""
    chapter_num = int(chapter['chapter_num'])
    chapter_title = chapter['title']
    chapter_url = chapter['url']

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
        print(f"   标题: {chapter_title}")
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

        # 按章节号排序
        chapters_sorted = sorted(all_chapters, key=lambda x: int(x['chapter_num']))

        # 找出已下载的章节
        downloaded = set()
        comic_base = Path(SAVE_PATH) / "ONE PIECE航海王"
        if comic_base.exists():
            # 获取所有章节号的集合
            available_chapter_nums = {int(ch['chapter_num']) for ch in chapters_sorted}
            
            # 遍历所有目录
            for chapter_dir in comic_base.iterdir():
                if chapter_dir.is_dir():
                    # 从目录名中提取所有数字
                    import re
                    numbers = re.findall(r'\d+', str(chapter_dir.name))
                    
                    # 尝试匹配章节号
                    for num in numbers:
                        num_int = int(num)
                        if num_int in available_chapter_nums:
                            downloaded.add(num_int)
                            break

        print(f"已下载的章节: {sorted(downloaded)}")

        # 筛选出未下载的章节
        chapters_to_download = [ch for ch in chapters_sorted if int(ch['chapter_num']) not in downloaded]

        print(f"\n准备下载: {len(chapters_to_download)} 个章节")

        if not chapters_to_download:
            print("所有章节都已下载！")
            await bot.send_message(
                chat_id=chat_id,
                text="✅ 所有章节都已下载完成！"
            )
            return

        # 显示前20个待下载章节
        print("\n前20个待下载章节:")
        for i, chapter in enumerate(chapters_to_download[:20], 1):
            print(f"  {i}. 第{chapter['chapter_num']}话: {chapter['title']}")
        if len(chapters_to_download) > 20:
            print(f"  ... 还有 {len(chapters_to_download)-20} 个章节")

        # 发送启动消息
        await bot.send_message(
            chat_id=chat_id,
            text=(
                f"🚀 ONE PIECE 批量下载已启动\n\n"
                f"📚 总章节数: {len(all_chapters)}\n"
                f"✅ 已下载: {len(downloaded)}\n"
                f"📥 待下载: {len(chapters_to_download)}\n"
                f"💾 保存路径: {SAVE_PATH}\n"
                f"⏰ 心跳间隔: 每30分钟同步进展\n\n"
                f"开始下载..."
            )
        )

        # 开始下载
        success_count = 0
        fail_count = 0
        total_size = 0
        last_heartbeat = datetime.now()

        for i, chapter in enumerate(chapters_to_download, 1):
            chapter_num = int(chapter['chapter_num'])

            # 检查是否需要发送心跳
            elapsed = datetime.now() - last_heartbeat
            if elapsed.total_seconds() >= HEARTBEAT_INTERVAL:
                # 发送心跳
                percent = (i / len(chapters_to_download)) * 100
                await bot.send_message(
                    chat_id=chat_id,
                    text=(
                        f"📊 ONE PIECE 下载进展\n\n"
                        f"进度: {i}/{len(chapters_to_download)} ({percent:.1f}%)\n"
                        f"当前: 第{chapter_num}话\n\n"
                        f"✅ 成功: {success_count}\n"
                        f"❌ 失败: {fail_count}\n"
                        f"💾 磁盘: {total_size:.2f}MB"
                    )
                )
                last_heartbeat = datetime.now()

            # 下载章节
            success, size_mb = await download_chapter(fetcher, chapter)

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
                f"📊 本次下载: {len(chapters_to_download)}话\n"
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
