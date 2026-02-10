#!/usr/bin/env python3
"""
ONE PIECE 下载器 - 修复版（使用 Selenium 下载图片）
解决 403 Forbidden 问题
"""
import asyncio
import logging
from pathlib import Path
import os
import base64
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
    """下载真正的第一话（使用 Selenium 下载图片）"""
    try:
        # 初始化
        fetcher = ManhuaGuiFetcherSelenium(headless=True)
        
        # 获取章节列表（倒序：最新在前）
        chapters = fetcher.get_chapters(COMIC_URL)
        
        # 真正的第一话是列表最后一个
        first_chapter = chapters[-1]
        
        print(f"总章节数: {len(chapters)}")
        print(f"第一章节: {first_chapter['title']}")
        print(f"第一话编号: {first_chapter.get('chapter_num', 'N/A')}")
        print(f"第一话URL: {first_chapter['url']}")
        
        # 访问章节页面
        print(f"\n正在访问章节页面...")
        fetcher._request(first_chapter['url'], wait_time=5)
        
        # 获取图片
        print(f"正在获取图片列表...")
        images = fetcher.get_images(first_chapter['url'])
        
        if not images:
            print("❌ 没有获取到图片")
            return False
        
        print(f"获取到 {len(images)} 张图片")
        print(f"前3个图片URL:")
        for i, img_url in enumerate(images[:3]):
            print(f"  {i+1}. {img_url}")
        
        # 下载图片（使用 Selenium）
        comic_path = Path(SAVE_PATH) / "ONE PIECE航海王" / f"第1话"
        comic_path.mkdir(parents=True, exist_ok=True)
        
        success_count = 0
        fail_count = 0
        
        for i, img_url in enumerate(images, 1):
            print(f"下载 {i}/{len(images)}...", end='\r')
            try:
                # 使用 Selenium 下载图片（避免 403 错误）
                fetcher.driver.get(img_url)
                time.sleep(0.5)
                
                # 获取图片数据（base64 编码的 PNG）
                # 或者使用 fetch API
                script = f"""
                var callback = arguments[arguments.length - 1];
                fetch('{img_url}')
                    .then(response => response.blob())
                    .then(blob => {
                        var reader = new FileReader();
                        reader.onloadend = function() {{
                            callback(reader.result);
                        }}
                        reader.readAsDataURL(blob);
                    })
                    .catch(error => callback(null));
                """
                
                import time
                time.sleep(0.3)
                
                # 使用更简单的方法：直接从网页获取图片
                img_element = fetcher.driver.find_element("css selector", f"img[src*='{img_url.split('/')[-1]}']")
                
                # 截图方式（备选）
                img_element.screenshot(comic_path / f"{i:03d}.png")
                success_count += 1
                
            except Exception as e:
                print(f"\n错误: 第{i}张图片下载异常: {e}")
                fail_count += 1
                
                # 备选方案：使用 fetcher 的方法
                try:
                    script = f"""
                    var xhr = new XMLHttpRequest();
                    xhr.open('GET', '{img_url}', true);
                    xhr.responseType = 'blob';
                    xhr.onload = function() {{
                        if (xhr.status === 200) {{
                            var reader = new FileReader();
                            reader.onloadend = function() {{
                                window.imageData = reader.result;
                            }}
                            reader.readAsDataURL(xhr.response);
                        }}
                    }};
                    xhr.send();
                    """
                    
                    fetcher.driver.execute_script(script)
                    time.sleep(1)
                    
                    # 获取图片数据
                    img_data = fetcher.driver.execute_script("return window.imageData;")
                    
                    if img_data:
                        # 解码 base64
                        header, encoded = img_data.split(",", 1)
                        data = base64.b64decode(encoded)
                        
                        img_path = comic_path / f"{i:03d}.jpg"
                        with open(img_path, 'wb') as f:
                            f.write(data)
                        success_count += 1
                        fail_count -= 1
                except Exception as e2:
                    print(f"  备选方案也失败: {e2}")
                    traceback.print_exc()
        
        print(f"\n✅ 下载完成！")
        print(f"保存路径: {comic_path}")
        print(f"图片总数: {len(images)}")
        print(f"成功: {success_count}")
        print(f"失败: {fail_count}")
        
        # 列出下载的文件
        files = sorted(comic_path.glob("*.*"))
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
                print(f"\n⚠️  有部分图片下载失败")
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
    import time
    result = await download_first_chapter()
    if result:
        print("\n✅ 下载成功！")
    else:
        print("\n❌ 下载失败！")


if __name__ == "__main__":
    asyncio.run(main())
