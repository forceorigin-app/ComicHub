#!/usr/bin/env python3
"""
查看 One Piece 完整章节列表（前50话）
"""
from fetcher_selenium import ManhuaGuiFetcherSelenium

fetcher = ManhuaGuiFetcherSelenium(headless=True)
chapters = fetcher.get_chapters('https://m.manhuagui.com/comic/1128/')

# 按章节号排序
chapters_sorted = sorted(chapters, key=lambda x: int(x['chapter_num']))

print(f'总章节数: {len(chapters_sorted)}')
print(f'\n前50个章节:')
for i, chapter in enumerate(chapters_sorted[:50], 1):
    print(f'{i:3d}. {chapter["title"]} (编号: {chapter["chapter_num"]})')

fetcher.close()
