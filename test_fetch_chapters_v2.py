#!/usr/bin/env python3
"""测试获取章节列表 - 带详细日志"""
import logging
from fetcher_selenium import ManhuaGuiFetcherSelenium

# 设置详细日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

print('='*60)
print('测试获取章节列表')
print('='*60)

print('\n1. 初始化 fetcher...')
try:
    fetcher = ManhuaGuiFetcherSelenium(headless=True)
    print('✅ Fetcher 初始化成功')
except Exception as e:
    print(f'❌ Fetcher 初始化失败: {e}')
    import traceback
    traceback.print_exc()
    exit(1)

print('\n2. 等待3秒（避免被检测）...')
import time
time.sleep(3)

print('\n3. 获取章节列表...')
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
    print('\n4. 前3个章节:')
    for i, ch in enumerate(chapters[:3], 1):
        print(f'  {i}. {ch["title"]} (编号: {ch["chapter_num"]})')
else:
    print('\n❌ 没有获取到章节！')

fetcher.close()
print('\n' + '='*60)
print('测试完成')
print('='*60)
