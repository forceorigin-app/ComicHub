#!/usr/bin/env python3
"""测试获取章节列表"""
from fetcher_selenium import ManhuaGuiFetcherSelenium

print('初始化 fetcher...')
try:
    fetcher = ManhuaGuiFetcherSelenium(headless=True)
    print('✅ Fetcher 初始化成功')
except Exception as e:
    print(f'❌ Fetcher 初始化失败: {e}')
    import traceback
    traceback.print_exc()
    exit(1)

print('\n获取章节列表...')
try:
    chapters = fetcher.get_chapters('https://m.manhuagui.com/comic/1128/')
    print(f'✅ 章节列表获取成功')
    print(f'章节数: {len(chapters)}')
except Exception as e:
    print(f'❌ 章节列表获取失败: {e}')
    import traceback
    traceback.print_exc()
    fetcher.close()
    exit(1)

if len(chapters) > 0:
    print('\n前5个章节:')
    for i, ch in enumerate(chapters[:5], 1):
        print(f'{i}. {ch["title"]} (编号: {ch["chapter_num"]})')
else:
    print('❌ 没有获取到章节！')

fetcher.close()
print('\n测试完成')
