#!/usr/bin/env python3
"""检查可下载的章节"""
from fetcher_selenium import ManhuaGuiFetcherSelenium
import logging

logging.basicConfig(level=logging.INFO)

fetcher = ManhuaGuiFetcherSelenium(headless=True)
chapters = fetcher.get_chapters('https://m.manhuagui.com/comic/1128/')

# 按章节号排序
chapters_sorted = sorted(chapters, key=lambda x: int(x['chapter_num']))

# 检查第3话是否存在
chapter_3_exists = any(int(ch['chapter_num']) == 3 for ch in chapters)
print(f"第3话是否存在: {'✅ 是' if chapter_3_exists else '❌ 否'}")

# 获取所有可用的章节号（按顺序）
available_nums = [int(ch['chapter_num']) for ch in chapters_sorted]

# 找出第一个大于2的章节号
next_chapter = None
for num in available_nums:
    if num > 2:
        next_chapter = num
        break

print(f"\n第2话之后第一个可用的章节: 第{next_chapter}话")

# 找出所有未下载的章节（按顺序）
import os
from pathlib import Path

downloaded = set()
comic_base = Path('/Users/force/data/comics/ONE PIECE航海王')
if comic_base.exists():
    for chapter_dir in comic_base.glob("第*话"):
        match = str(chapter_dir).split('/')[-1].replace('第', '').replace('话', '')
        if match.isdigit():
            downloaded.add(int(match))

print(f"\n已下载的章节: {sorted(downloaded)}")

# 找出未下载的章节
to_download = [num for num in available_nums if num not in downloaded]

print(f"\n可下载的章节: {len(to_download)} 个")

# 显示前20个
print("\n前20个待下载章节:")
for i, chapter in enumerate(chapters_sorted[:50], 1):
    chapter_num = int(chapter['chapter_num'])
    if chapter_num not in downloaded:
        print(f"  {chapter_num:4d}. {chapter['title']}")

if len(to_download) > 20:
    print(f"  ... 还有 {len(to_download)-20} 个章节")

fetcher.close()
