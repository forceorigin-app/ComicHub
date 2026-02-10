#!/usr/bin/env python3
"""
ONE PIECE 下载器 - 修复版（添加正确的请求头）
解决 403 Forbidden 问题
"""
import asyncio
import logging
from pathlib import Path
import os
import traceback

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
    """下载真正的第一话（添加正确的请求头）"""
    try:
        # 初始化
        fetcher = ManhuaGuiFetcherSelenium(headless=True)
        
        # 获取章节列表（倒序：最新在前）
        chapters = fetcher.get_chapters(COMIC_URL)
        
        # 真正的第一话是列表最后一个
        first_chapter = chapters[-1]
        
        print(f"总章节数: {len(chapters)}")
        print(f"第一章节: {first_chapter['title']}")
        print(f"第一话URL: {first_chapter['url']}")
        
        # 获取图片
        print(f"\n正在获取图片列表...")
        images = fetcher.get_images(first_chapter['url'])
        
        if not images:
            print("❌ 没有获取到图片")
            return False
        
        print(f"获取到 {len(images)} 张图片")
        
        # 下载图片（使用 requests + 正确的 headers）
        comic_path = Path(SAVE_PATH) / "ONE PIECE航海王" / f"第1话"
        comic_path.mkdir(parents=True, exist_ok=True)
        
        import requests
        
        # 创建会话并设置 headers
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
            'Referer': first_chapter['url'],
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })
        
        # 从 Selenium 获取 cookies
        for cookie in fetcher.driver.get_cookies():
            session.cookies.set(cookie['name'], cookie['value'])
        
        print(f"已设置 {len(session.cookies)} 个 cookies")
        
        success_count = 0
        fail_count = 0
        
        for i, img_url in enumerate(images, 1):
            print(f"下载 {i}/{len(images)}...", end='\r')
            try:
                response = session.get(img_url, timeout=30, verify=False)
                
                if response.status_code == 200:
                    img_path = comic_path / f"{i:03d}.jpg"
                    with open(img_path, 'wb') as f:
                        f.write(response.content)
                    success_count += 1
                else:
                    print(f"\n错误: 第{i}张图片下载失败，状态码: {response.status_code}")
                    fail_count += 1
            except Exception as e:
                print(f"\n错误: 第{i}张图片下载异常: {e}")
                fail_count += 1
                traceback.print_exc()
        
        print(f"\n✅ 下载完成！")
        print(f"保存路径: {comic_path}")
        print(f"图片总数: {len(images)}")
        print(f"成功: {success_count}")
        print(f"失败: {fail_count}")
        
        # 列出下载的文件
        files = sorted(comic_path.glob("*.jpg"))
        print(f"\n下载的文件 ({len(files)}):")
        for file in files[:10]:  # 只显示前10个
            size_kb = file.stat().st_size / 1024
            print(f"  {file.name}: {size_kb:.2f}KB")
        
        if len(files) > 10:
            print(f"  ... 还有 {len(files)-10} 个文件")
        
        # 计算总大小
        if success_count > 0:
            total_size = sum(f.stat().st_size for f in files)
            size_mb = total_size / (1024 * 1024)
            print(f"\n文件总大小: {size_mb:.2f}MB")
            
            if success_count == len(images):
                print(f"\n✅ 完美！所有图片都已下载！")
            else:
                print(f"\n⚠️  有 {fail_count} 张图片下载失败")
        else:
            print(f"\n❌ 没有成功下载任何图片")
        
        # 清理
        fetcher.close()
        
        return success_count > 0
        
    except Exception as e:
        logger.error(f"下载失败: {e}")
        traceback.print_exc()
        return False


async def main():
    """主函数"""
    result = await download_first_chapter()
    if result:
        print("\n✅ 下载成功！")
    else:
        print("\n❌ 下载失败！")


if __name__ == "__main__":
    asyncio.run(main())
