#!/usr/bin/env python
"""测试页码命名功能"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from comichub.core.fetcher import ManhuaGuiFetcherSelenium

def main():
    # 测试 URL 提取方法
    print("=" * 60)
    print("测试 URL 页码提取功能")
    print("=" * 60)

    fetcher = ManhuaGuiFetcherSelenium(headless=True)

    test_urls = [
        'https://m.manhuagui.com/comic/1128/9771.html#p=2',
        'https://m.manhuagui.com/comic/1128/9771.html#p=15',
        'https://m.manhuagui.com/comic/1128/9771.html',
        'https://m.manhuagui.com/comic/1128/9771.html?p=3',
    ]

    for url in test_urls:
        page_num = fetcher._extract_page_number_from_url(url)
        print(f'{url}')
        print(f'  -> 页码: {page_num}')

    print("\n" + "=" * 60)
    print("测试获取章节图片")
    print("=" * 60)

    test_url = 'https://m.manhuagui.com/comic/1128/9771.html'
    print(f"测试 URL: {test_url}\n")

    result = fetcher.get_images(test_url)

    print(f"\n总页数: {result['total_count']}")
    print(f"获取到图片数: {len(result['images'])}")

    if result['images']:
        print(f"\n前 5 张图片信息:")
        for i, img_info in enumerate(result['images'][:5], 1):
            print(f"  {i}. 页码: {img_info['page']:3d}, URL: {img_info['url'][:60]}...")

        if len(result['images']) > 5:
            print(f"\n最后 3 张图片信息:")
            for i, img_info in enumerate(result['images'][-3:], len(result['images']) - 2):
                print(f"  {i}. 页码: {img_info['page']:3d}, URL: {img_info['url'][:60]}...")

    # 测试文件名生成
    print("\n" + "=" * 60)
    print("测试文件名生成（补零）")
    print("=" * 60)

    total_count = result['total_count']
    zero_pad_width = len(str(total_count))

    print(f"总页数: {total_count}")
    print(f"补零位数: {zero_pad_width}")
    print(f"\n示例文件名:")

    for i, img_info in enumerate(result['images'][:10], 1):
        page_num = img_info['page']
        filename = f"{page_num:0{zero_pad_width}d}.jpg"
        print(f"  页码 {page_num:3d} -> {filename}")

    fetcher.close()
    print("\n测试完成!")

if __name__ == "__main__":
    main()
