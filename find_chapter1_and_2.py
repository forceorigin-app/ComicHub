#!/usr/bin/env python3
"""
查找第1话和第2话在列表中的位置
"""
from fetcher_selenium import ManhuaGuiFetcherSelenium

fetcher = ManhuaGuiFetcherSelenium(headless=True)
chapters = fetcher.get_chapters('https://m.manhuagui.com/comic/1128/')

print(f'总章节数: {len(chapters)}')

# 查找第1话和第2话
for i, chapter in enumerate(chapters, 1):
    chapter_num = int(chapter['chapter_num'])
    if chapter_num <= 10:
        print(f'{i:4d}. {chapter["title"]} (编号: {chapter["chapter_num"]})')

print('\n查找最小的10个章节号:')
# 找出所有章节号
chapter_nums = [int(ch['chapter_num']) for ch in chapters]
smallest_nums = sorted(set(chapter_nums))[:20]
print(f'最小的20个章节号: {smallest_nums}')

# 找到这些章节
print('\n对应章节:')
for num in smallest_nums:
    for chapter in chapters:
        if int(chapter['chapter_num']) == num:
            print(f'  第{num}话: {chapter["title"]}')
            break

fetcher.close()
