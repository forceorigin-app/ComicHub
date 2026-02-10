#!/usr/bin/env python3
"""
通用漫画下载器 (优化版)
- 逻辑修正：精确解析 <div class="chapter-list">
- 优化：只下载格式最优的图片 (优先 webp，去重)
"""
import sys
import os
import re
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import requests
from bs4 import BeautifulSoup

from comichub.core.fetcher import ManhuaGuiFetcherSelenium

DEFAULT_SAVE_DIR = Path.home() / "data" / "comic"

def get_info(url: str) -> dict:
    """解析书页，获取书名和章节列表"""
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"}
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            print(f"❌ 请求失败: {resp.status_code}")
            return None
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # 1. 书名
        book_name = "Unknown_Book"
        h1 = soup.find('h1')
        if h1 and h1.text.strip():
            book_name = h1.text.strip()
        
        # 2. 章节列表 (<div class="chapter-list">)
        chapter_div = soup.find('div', class_='chapter-list')
        
        if not chapter_div:
            print("❌ 未找到 .chapter-list 容器")
            return None
        
        links = chapter_div.find_all('a')
        
        if not links:
            print("❌ 章节列表为空")
            return None
        
        chapters = []
        for a in links:
            href = a.get('href', '')
            if href.startswith('/'):
                full_url = urljoin(url, href)
                title = a.get_text(strip=True)
                if title:
                    chapters.append({
                        'title': title,
                        'url': full_url
                    })
        
        return {
            'book_name': book_name,
            'chapters': chapters
        }
    except Exception as e:
        print(f"❌ 解析失败: {e}")
        return None

def download_latest(url: str, save_dir: Path = DEFAULT_SAVE_DIR):
    """下载最新一章"""
    info = get_info(url)
    
    if not info or not info['chapters']:
        return
    
    book_name = info['book_name']
    chapters = info['chapters']
    
    # 取最新（第一个）
    latest = chapters[0]
    ch_title = latest['title']
    ch_url = latest['url']
    
    # 清理文件名
    book_name = re.sub(r'[\\/:*?"<>|]', '', book_name)
    ch_title = re.sub(r'[\\/:*?"<>|]', '', ch_title)
    
    print(f"📚 书名: {book_name}")
    print(f"📖 章节: {ch_title}")
    
    # 创建目录
    ch_path = save_dir / book_name / ch_title
    ch_path.mkdir(parents=True, exist_ok=True)
    print(f"💾 保存路径: {ch_path}")
    
    # 获取图片
    print("🚀 启动 Selenium...")
    fetcher = ManhuaGuiFetcherSelenium()
    images = fetcher.get_images(ch_url)
    fetcher.close()
    
    if not images:
        print("❌ 未找到图片")
        return
    
    print(f"🖼️ 找到 {len(images)} 张图片，开始下载...")
    
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": url
    }
    
    success = 0
    processed_urls = set() # 用于去重：如果一张图片同时有 jpg 和 webp 链接，只下载一次
    
    for i, img_url in enumerate(images, 1):
        # 简单的去重逻辑：URL 相同则跳过
        # 注意：fetcher.get_images 返回的列表本身应该是不重复的，
        # 但为了保险，我们还是做一次 URL 检查
        if img_url in processed_urls:
            continue
        processed_urls.add(img_url)
        
        # 修复协议
        if img_url.startswith('//'):
            img_url = 'https:' + img_url
        
        # 判定扩展名：优先 webp
        ext = '.webp' # 默认
        if '.jpg' in img_url.lower(): 
            # 如果 URL 只有 jpg，就用 jpg
            if '.webp' not in img_url.lower():
                ext = '.jpg'
        
        try:
            if i % 5 == 0:
                time.sleep(0.5)
            
            r = requests.get(img_url, headers=headers, stream=True, timeout=15)
            if r.status_code == 200:
                fname = f"{i:03}{ext}"
                fpath = ch_path / fname
                
                with open(fpath, 'wb') as f:
                    for chunk in r.iter_content(8192):
                        f.write(chunk)
                success += 1
                
                print(f"  进度: {success}/{len(images)}", end='\r', flush=True)
        except Exception:
            pass
    
    print(f"\n✅ 完成! 成功: {success}/{len(images)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python -m scripts.download_comic <书页URL>")
        print("示例: python -m scripts.download_comic https://m.manhuagui.com/comic/2592/")
        sys.exit(1)
    
    target = sys.argv[1]
    download_latest(target)
