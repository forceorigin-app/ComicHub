#!/usr/bin/env python3
"""
查看 One Piece 早期章节列表（实际的前20话）
"""
from fetcher_selenium import ManhuaGuiFetcherSelenium

fetcher = ManhuaGuiFetcherSelenium(headless=True)
chapters = fetcher.get_chapters('https://m.manhuagui.com/comic/1128/')

# 按章节号排序
chapters_sorted = sorted(chapters, key=lambda x: int(x['chapter_num']))

print(f'总章节数: {len(chapters_sorted)}')
print(f'\n实际的前20个章节（按章节号排序）:')
for i, chapter in enumerate(chapters_sorted[:20], 1):
    print(f'{i:3d}. {chapter["title"]} (编号: {chapter["chapter_num"]})')

fetcher.close()
