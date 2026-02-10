#!/usr/bin/env python3
"""
ONE PIECE 下载器 - 下载真正的第一话
"""
import asyncio
import logging
from pathlib import Path
import os

from fetcher_selenium import ManhuaGuiFetcherSelenium

# 配置
COMIC_URL = "https://m.manhuagui.com/comic/1128/"
SAVE_PATH = "/Users/force/data/comics"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def download_first_chapter():
    """下载真正的第一话（列表最后一个）"""
    try:
        # 初始化
        fetcher = ManhuaGuiFetcherSelenium(headless=True)
        
        # 获取章节列表（倒序：最新在前）
        chapters = fetcher.get_chapters(COMIC_URL)
        
        # 真正的第一话是列表最后一个
        first_chapter = chapters[-1]
        
        print(f"总章节数: {len(chapters)}")
        print(f"最新章节: {chapters[0]['title']}")
        print(f"第一章节: {first_chapter['title']}")
        print(f"第一话编号: {first_chapter.get('chapter_num', 'N/A')}")
        print(f"第一话URL: {first_chapter['url']}")
        
        # 获取图片
        print(f"\n正在获取 {first_chapter['title']} 的图片...")
        images = fetcher.get_images(first_chapter['url'])
        
        if not images:
            print("❌ 没有获取到图片")
            return False
        
        print(f"获取到 {len(images)} 张图片")
        
        # 下载图片
        comic_path = Path(SAVE_PATH) / "ONE PIECE航海王" / f"第1话"
        comic_path.mkdir(parents=True, exist_ok=True)
        
        import requests
        session = requests.Session()
        
        for i, img_url in enumerate(images, 1):
            print(f"下载 {i}/{len(images)}...", end='\r')
            response = session.get(img_url, timeout=30, verify=False)
            if response.status_code == 200:
                img_path = comic_path / f"{i:03d}.jpg"
                with open(img_path, 'wb') as f:
                    f.write(response.content)
        
        print(f"\n✅ 下载完成！")
        print(f"保存路径: {comic_path}")
        print(f"图片数量: {len(images)}")
        
        # 计算总大小
        total_size = sum(os.path.getsize(comic_path / f"{j:03d}.jpg") for j in range(1, len(images)+1))
        size_mb = total_size / (1024 * 1024)
        print(f"文件大小: {size_mb:.2f}MB")
        
        # 清理
        fetcher.close()
        
        return True
        
    except Exception as e:
        logger.error(f"下载失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主函数"""
    await download_first_chapter()


if __name__ == "__main__":
    asyncio.run(main())
