#!/usr/bin/env python3
"""
漫画抓取工具 ComicHub
主程序入口
"""

import sys
import yaml
import click
import time
from pathlib import Path
from typing import Optional
from tqdm import tqdm

from db import Database
from fetcher import ManhuaGuiFetcher
from util import setup_logging, ensure_dir, save_info_txt, sanitize_filename

# 加载配置
with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# 初始化日志
logger = setup_logging(config)


class ComicFetcher:
    """漫画抓取器"""

    def __init__(self, config_path: str = "config.yaml"):
        self.config = config
        self.db = None
        try:
            self.db = Database(self.config)
            logger.info("数据库初始化成功")
        except Exception as e:
            logger.warning(f"数据库初始化失败: {e}")
        
        self.fetcher = ManhuaGuiFetcher()
        self.save_path = Path(self.config['save_path'].replace('~', str(Path.home())))
        self.save_path.mkdir(parents=True, exist_ok=True)
        
        self.fetch_config = self.config.get('fetch', {})
        self.concurrent_downloads = self.fetch_config.get('concurrent_downloads', 5)
        self.delay = self.fetch_config.get('delay', 1)
        self.use_db = (self.db is not None)

    def cleanup(self):
        if self.db:
            try:
                self.db.close()
            except:
                pass


@click.group()
def cli():
    """ComicHub 漫画抓取工具"""
    pass


@cli.command()
@click.option('--url', '-u', help='漫画 URL')
def url(url: str):
    """根据 URL 抓取漫画"""
    if not url:
        print("错误: --url 参数必填")
        sys.exit(1)
    
    fetcher = ComicFetcher()
    try:
        fetcher.fetch_comic_by_url(url)
    finally:
        fetcher.cleanup()


@cli.command()
@click.option('--keyword', '-k', help='搜索关键词')
def search(keyword: str):
    """搜索并抓取漫画"""
    if not keyword:
        print("错误: --keyword 参数必填")
        sys.exit(1)
    
    fetcher = ComicFetcher()
    try:
        fetcher.search_and_fetch(keyword)
    finally:
        fetcher.cleanup()


@cli.command()
@click.option('--pages', '-p', default=1, help='抓取页数')
def fullsite(pages: int):
    """全站抓取"""
    print(f"警告: 全站抓取可能需要很长时间")
    print(f"抓取页数: {pages}")
    print("全站抓取功能开发中...")


@cli.command()
def list():
    """列出所有漫画"""
    fetcher = ComicFetcher()
    try:
        if fetcher.use_db:
            fetcher.list_comics()
        else:
            print("数据库未连接，无法列出漫画")
    except Exception as e:
        print(f"无法连接数据库: {e}")
    finally:
        fetcher.cleanup()


@cli.command()
@click.option('--name', '-n', required=True, help='漫画名称')
def info(name: str):
    """查看漫画详情"""
    fetcher = ComicFetcher()
    try:
        if fetcher.use_db:
            fetcher.show_comic_info(name)
        else:
            print("数据库未连接，无法查看漫画详情")
    finally:
        fetcher.cleanup()


@cli.command()
@click.option('--comic-url', '-c', help='测试的漫画URL')
def test(comic_url):
    """测试功能"""
    if not comic_url:
        comic_url = "https://m.manhuagui.com/comic/1128/"
    
    print("测试网络连接和搜索功能...")
    
    try:
        fetcher = ManhuaGuiFetcher()
        
        print("\n1. 测试基础连接...")
        response = fetcher._request(fetcher.base_url)
        if response:
            print(f"   连接成功: {fetcher.base_url}")
            print(f"   状态码: {response.status_code}")
        else:
            print(f"   连接失败: {fetcher.base_url}")
            return
        
        print("\n2. 测试搜索功能...")
        test_keywords = ['海贼王', '火影', '死神']
        found_any = False
        
        for keyword in test_keywords:
            print(f"   搜索: {keyword}...")
            results = fetcher.search_comics(keyword)
            
            if results:
                print(f"      搜索到 {len(results)} 部漫画")
                print(f"      前3个结果:")
                for r in results[:3]:
                    print(f"        - {r['name']}")
                found_any = True
                break
            else:
                print(f"      未找到")
        
        if not found_any:
            print("\n   所有搜索都失败了")
            print("   提示: 可能是网站反爬虫机制")
        
        print(f"\n3. 测试获取漫画信息...")
        comic_info = fetcher.get_comic_info(comic_url)
        
        if comic_info:
            print(f"   名称: {comic_info.get('name', 'N/A')}")
            print(f"   ID: {comic_info.get('id', 'N/A')}")
            print(f"   URL: {comic_info.get('url', 'N/A')}")
            
            print("\n4. 测试获取章节...")
            chapters = fetcher.get_chapters(comic_url)
            print(f"   章节数: {len(chapters)}")
            
            if chapters:
                print("   前3个章节:")
                for c in chapters[:3]:
                    print(f"      - {c['chapter_num']}")
                
                print(f"\n5. 测试获取图片 (章节: {chapters[0]['chapter_num']})...")
                images = fetcher.get_images(chapters[0]['url'])
                print(f"   图片数: {len(images)}")
        
        print("\n测试完成")
        
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    cli()
