#!/usr/bin/env python3
"""
检查第2-10话是否存在
"""
from fetcher_selenium import ManhuaGuiFetcherSelenium

fetcher = ManhuaGuiFetcherSelenium(headless=True)
chapters = fetcher.get_chapters('https://m.manhuagui.com/comic/1128/')

print('检查第2-10话是否存在:')
chapters_dict = {int(ch['chapter_num']): ch for ch in chapters}

for i in range(2, 11):
    if i in chapters_dict:
        chapter = chapters_dict[i]
        print(f'  第{i}话: ✅ {chapter["title"]}')
    else:
        print(f'  第{i}话: ❌ 不存在')

fetcher.close()
