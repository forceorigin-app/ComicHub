#!/usr/bin/env python3
"""检查章节列表"""
from fetcher_selenium import ManhuaGuiFetcherSelenium

fetcher = ManhuaGuiFetcherSelenium(headless=True)
chapters = fetcher.get_chapters('https://m.manhuagui.com/comic/1128/')

print('前10个章节:')
for i, chapter in enumerate(chapters[:10]):
    print(f"{i+1}. {chapter['title']} (chapter_num: {chapter.get('chapter_num', 'N/A')})")

print(f'\n总章节数: {len(chapters)}')
print(f'\n第一章: {chapters[0]["title"]} (chapter_num: {chapters[0].get("chapter_num", "N/A")})')
print(f'第一章URL: {chapters[0]["url"]}')

fetcher.close()
