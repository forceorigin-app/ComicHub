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


# 初始化日志
logger = setup_logging({})


class ComicFetcher:
    """漫画抓取器"""

    def __init__(self, config_path: str = "config.yaml"):
        """
        初始化抓取器

        Args:
            config_path: 配置文件路径
        """
        # 加载配置
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        # 初始化数据库
        self.db = Database(self.config)
        
        # 初始化抓取器
        self.fetcher = ManhuaGuiFetcher()
        
        # 配置参数
        self.save_path = Path(self.config['save_path'].replace('~', str(Path.home())))
        self.save_path.mkdir(parents=True, exist_ok=True)
        
        self.fetch_config = self.config['fetch']
        self.concurrent_downloads = self.fetch_config['concurrent_downloads']
        self.delay = self.fetch_config['delay']

    def cleanup(self):
        """清理资源"""
        self.db.close()

    def fetch_comic_by_url(self, comic_url: str):
        """
        根据 URL 抓取漫画

        Args:
            comic_url: 漫画 URL
        """
        logger.info(f"开始抓取漫画: {comic_url}")
        
        # 检查漫画是否已存在
        existing_comic = self.db.comic_exists(comic_url)
        if existing_comic:
            logger.info(f"漫画已存在，跳过: {comic_url}")
            return
        
        # 获取漫画信息
        comic_info = self.fetcher.get_comic_info(comic_url)
        if not comic_info:
            logger.error(f"获取漫画信息失败: {comic_url}")
            self.db.add_fetch_history(status="failed", error_msg="获取漫画信息失败")
            return
        
        # 添加漫画到数据库
        comic_id = self.db.add_comic(
            name=comic_info['name'],
            url=comic_info['url'],
            description=comic_info.get('description'),
            cover_image=comic_info.get('cover_image')
        )
        
        # 创建保存目录
        comic_dir = self.save_path / sanitize_filename(comic_info['name'])
        comic_dir.mkdir(exist_ok=True)
        
        # 获取章节列表
        chapters = self.fetcher.get_chapters(comic_url)
        if not chapters:
            logger.warning(f"未找到章节: {comic_url}")
            self.db.add_fetch_history(comic_id=comic_id, status="failed", error_msg="未找到章节")
            return
        
        # 获取已抓取的章节
        fetched_chapters = self.db.get_fetched_chapters(comic_id)
        
        # 遍历章节
        for chapter in tqdm(chapters, desc=f"抓取 {comic_info['name']}"):
            chapter_num = chapter['chapter_num']
            chapter_title = chapter['title']
            chapter_url = chapter['url']
            
            # 检查章节是否已抓取
            existing_chapter = self.db.chapter_exists(chapter_url)
            chapter_id = existing_chapter if existing_chapter else None
            
            if not chapter_id:
                # 添加章节到数据库
                chapter_id = self.db.add_chapter(
                    comic_id=comic_id,
                    chapter_num=chapter_num,
                    title=chapter_title,
                    url=chapter_url
                )
            
            # 获取图片列表
            images = self.fetcher.get_images(chapter_url)
            if not images:
                logger.warning(f"未找到图片: {chapter_url}")
                continue
            
            # 创建章节目录
            chapter_dir = comic_dir / f"第{chapter_num}话"
            chapter_dir.mkdir(exist_ok=True)
            
            # 下载图片
            for i, image_url in enumerate(images, 1):
                file_path = chapter_dir / f"{i:03d}.jpg"
                
                # 检查图片是否已下载
                if self.db.image_exists(chapter_id, i):
                    # 更新文件路径
                    if Path(file_path).exists():
                        pass  # 已存在
                    else:
                        # 重新下载
                        self.fetcher.download_image(image_url, file_path)
                else:
                    # 下载图片
                    success = self.fetcher.download_image(image_url, file_path)
                    if success:
                        self.db.add_image(
                            chapter_id=chapter_id,
                            page_num=i,
                            url=image_url,
                            file_path=str(file_path)
                        )
                
                # 延迟
                time.sleep(self.delay)
            
            # 记录抓取历史
            self.db.add_fetch_history(comic_id=comic_id, chapter_id=chapter_id)
            logger.info(f"章节抓取完成: {chapter_num}")
        
        # 更新 info.txt
        comic_data = self.db.get_comic(comic_id=comic_id)
        if comic_data:
            chapters_data = self.db.get_chapters(comic_id=comic_id)
            save_info_txt(
                comic_name=sanitize_filename(comic_info['name']),
                comic_info={
                    **comic_data,
                    'chapter_count': len(chapters_data),
                    'fetched_chapters': [c['chapter_num'] for c in chapters_data]
                },
                save_path=str(self.save_path)
            )
        
        logger.info(f"漫画抓取完成: {comic_info['name']}")

    def search_and_fetch(self, keyword: str):
        """
        搜索并抓取漫画

        Args:
            keyword: 搜索关键词
        """
        logger.info(f"搜索漫画: {keyword}")
        
        # 搜索漫画
        comics = self.fetcher.search_comics(keyword)
        if not comics:
            logger.warning(f"未找到匹配的漫画: {keyword}")
            return
        
        # 显示搜索结果
        print(f"\n找到 {len(comics)} 部漫画:")
        for i, comic in enumerate(comics, 1):
            print(f"{i}. {comic['name']} - {comic['url']}")
        
        # 选择要抓取的漫画
        try:
            choice = int(input("\n请输入要抓取的漫画编号 (0 取消): "))
            if choice == 0 or choice > len(comics):
                return
        except ValueError:
            print("输入无效")
            return
        
        # 抓取选中的漫画
        selected_comic = comics[choice - 1]
        self.fetch_comic_by_url(selected_comic['url'])

    def fetch_fullsite(self):
        """
        全站抓取
        """
        logger.info("开始全站抓取")
        print("警告: 全站抓取可能需要很长时间")
        confirm = input("确认继续? (yes/no): ")
        if confirm.lower() != 'yes':
            return
        
        # 获取首页漫画列表
        # 这里简化处理，实际需要分页获取
        print("全站抓取功能开发中...")
        
    def list_comics(self):
        """
        列出所有漫画
        """
        comics = self.db.list_comics()
        if not comics:
            print("暂无漫画")
            return
        
        print(f"\n共有 {len(comics)} 部漫画:")
        for comic in comics:
            print(f"- {comic['name']} ({comic['url']})")

    def show_comic_info(self, comic_name: str):
        """
        显示漫画详情
        """
        comic = self.db.get_comic(name=comic_name)
        if not comic:
            print(f"未找到漫画: {comic_name}")
            return
        
        chapters = self.db.get_chapters(comic_id=comic['id'])
        total_images = 0
        for chapter in chapters:
            images = self.db.get_chapter_images(chapter_id=chapter['id'])
            total_images += len(images)
        
        print(f"\n漫画信息:")
        print(f"  名称: {comic['name']}")
        print(f"  URL: {comic['url']}")
        print(f"  描述: {comic.get('description', 'N/A')}")
        print(f"  章节数: {len(chapters)}")
        print(f"  图片总数: {total_images}")


@click.group()
def cli():
    """ComicHub 漫画抓取工具"""
    pass


@cli.command()
@click.option('--mode', type=click.Choice(['url', 'search', 'fullsite']), required=True)
@click.option('--url', help='漫画 URL (mode=url 时必填)')
@click.option('--keyword', help='搜索关键词 (mode=search 时必填)')
def fetch(mode: str, url: str, keyword: str):
    """
    抓取漫画

    Examples:
        # 指定 URL 抓取
        python comic_fetcher.py --mode url --url https://m.manhuagui.com/comic/1128/

        # 搜索并抓取
        python comic_fetcher.py --mode search --keyword 海贼王

        # 全站抓取
        python comic_fetcher.py --mode fullsite
    """
    fetcher = ComicFetcher()
    
    try:
        if mode == 'url':
            if not url:
                print("错误: --url 参数必填")
                sys.exit(1)
            fetcher.fetch_comic_by_url(url)
        
        elif mode == 'search':
            if not keyword:
                print("错误: --keyword 参数必填")
                sys.exit(1)
            fetcher.search_and_fetch(keyword)
        
        elif mode == 'fullsite':
            fetcher.fetch_fullsite()
        
        else:
            print(f"未知的模式: {mode}")
            sys.exit(1)
    
    finally:
        fetcher.cleanup()


@cli.command()
def list():
    """列出所有漫画"""
    fetcher = ComicFetcher()
    try:
        fetcher.list_comics()
    finally:
        fetcher.cleanup()


@cli.command()
@click.option('--name', required=True, help='漫画名称')
def info(name: str):
    """查看漫画详情"""
    fetcher = ComicFetcher()
    try:
        fetcher.show_comic_info(name)
    finally:
        fetcher.cleanup()


if __name__ == '__main__':
    cli()
