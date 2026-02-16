#!/usr/bin/env python3
"""
全能下载器 (修正版)
- 获取所有章节 (从第一章开始)
- 断点续传
- 每 30 分钟同步进度
"""
import sys
import os
import re
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from comichub.core.fetcher import ManhuaGuiFetcherSelenium

# Config
BOT_TOKEN = "8308151445:AAEhS3oZ880gcA3-16-FfHMglzvZ2NalwK0"
CHAT_ID = "8260462836"
SAVE_DIR = Path.home() / "data" / "comic"
PROGRESS_LOG = "download_progress.log"

def send_msg(text):
    """Send Telegram message"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={'chat_id': CHAT_ID, 'text': text})

def log_progress(msg):
    """Write to log file"""
    with open(PROGRESS_LOG, 'a') as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {msg}\n")

def get_all_chapters(book_url: str) -> tuple:
    """Get book name and all chapters (reversed to start from Ch 1)"""
    print(f"正在获取 {book_url} 的章节列表...")
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(book_url, headers=headers, timeout=10)
    
    if resp.status_code != 200:
        raise Exception("请求书页失败")
    
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    # Book Name
    book_name = "Unknown"
    h1 = soup.find('h1')
    if h1:
        book_name = h1.text.strip()
    book_name = re.sub(r'[\\/:*?"<>|]', '', book_name)
    
    # Chapter List
    chapter_div = soup.find('div', class_='chapter-list')
    if not chapter_div:
        raise Exception("未找到章节列表容器")
    
    links = chapter_div.find_all('a')
    if not links:
        raise Exception("章节列表为空")
    
    chapters = []
    for a in links:
        href = a.get('href', '')
        if href.startswith('/'):
            full_url = urljoin(book_url, href)
            title = a.get_text(strip=True)
            if title:
                chapters.append({
                    'title': title,
                    'url': full_url
                })
    
    # Reverse: links[0] is latest, so reverse() starts from Ch 1
    chapters.reverse()
    return book_name, chapters

def run_download(book_url: str):
    """Main download loop"""
    try:
        book_name, chapters = get_all_chapters(book_url)
        total = len(chapters)
        
        print(f"📚 书名: {book_name}")
        print(f"📖 总章节: {total}")
        
        send_msg(f"🚀 开始下载：{book_name}\n共 {total} 章。")
        
        last_report_time = time.time()
        REPORT_INTERVAL = 30 * 60 # 30 minutes
        REPORT_CHAPTER_INTERVAL = 5 # Report every 5 chapters (fail-safe)
        
        count = 0
        
        for i, chap in enumerate(chapters):
            count += 1
            
            ch_title = chap['title']
            ch_url = chap['url']
            
            # Clean filename
            ch_title_clean = re.sub(r'[\\/:*?"<>|]', '', ch_title)
            ch_path = SAVE_DIR / book_name / ch_title_clean
            
            # Check existence (Resume)
            if ch_path.exists() and list(ch_path.glob('*')):
                msg = f"⏭ 跳过: [{count}/{total}] {ch_title} (已存在)"
                print(msg)
                log_progress(msg)
                continue
            
            # Download
            msg = f"⬇️ 下载中: [{count}/{total}] {ch_title}"
            print(msg)
            log_progress(msg)
            
            try:
                # Selenium
                fetcher = ManhuaGuiFetcherSelenium()
                images = fetcher.get_images(ch_url)
                
                if not images:
                    log_progress(f"⚠️ [{count}/{total}] {ch_title}: 未找到图片")
                    fetcher.close()
                    continue
                
                # Save
                ch_path.mkdir(parents=True, exist_ok=True)
                
                headers = {
                    "User-Agent": "Mozilla/5.0",
                    "Referer": book_url
                }
                
                img_count = 0
                for img_url in images:
                    if img_url.startswith('//'):
                        img_url = 'https:' + img_url
                    
                    ext = '.webp'
                    if 'jpg' in img_url.lower(): ext = '.jpg'
                    elif 'png' in img_url.lower(): ext = '.png'
                    
                    fname = f"{img_count+1:03}{ext}"
                    fpath = ch_path / fname
                    
                    try:
                        r = requests.get(img_url, headers=headers, stream=True, timeout=15)
                        if r.status_code == 200:
                            with open(fpath, 'wb') as f:
                                for chunk in r.iter_content(8192):
                                    f.write(chunk)
                            img_count += 1
                    except:
                        pass # Ignore single image error
                
                msg = f"✅ 完成: [{count}/{total}] {ch_title} ({img_count} 张)"
                print(msg)
                log_progress(msg)
                
                fetcher.close()
                
                # Check report time
                current_time = time.time()
                if (current_time - last_report_time > REPORT_INTERVAL) or (count % REPORT_CHAPTER_INTERVAL == 0):
                    # Send progress
                    next_title = chapters[i+1]['title'] if i+1 < total else 'None'
                    report = f"📊 进度报告: {book_name}\n当前: [{count}/{total}] {ch_title}\n下一: {next_title}"
                    send_msg(report)
                    last_report_time = current_time
                    
            except Exception as e:
                error_msg = f"❌ 错误: [{count}/{total}] {ch_title} - {e}"
                print(error_msg)
                log_progress(error_msg)
                try:
                    send_msg(error_msg)
                except:
                    pass
        
        # Finished
        final_msg = f"🎉 全部下载完成!\n书名: {book_name}\n总数: {total}"
        print(final_msg)
        log_progress(final_msg)
        send_msg(final_msg)
        
    except Exception as e:
        fatal_msg = f"💥 脚本崩溃: {e}"
        print(fatal_msg)
        log_progress(fatal_msg)
        send_msg(fatal_msg)

if __name__ == "__main__":
    # Default target
    TARGET_URL = "https://m.manhuagui.com/comic/2592/"
    
    # Support CLI arg
    if len(sys.argv) > 1:
        TARGET_URL = sys.argv[1]
    
    run_download(TARGET_URL)
