#!/usr/bin/env python3
"""
ComicHub CLI - 主入口程序
提供三种抓取模式：
1. 全站抓取模式
2. 指定 URL 抓取模式
3. 基于搜索漫画名的结果逐个抓取
"""

import sys
import logging
from pathlib import Path
from typing import Optional, List
import click

from config_loader import get_config
from database import Database
from fetcher_selenium import ManhuaGuiFetcherSelenium
from batch_download import BatchDownloader
from info_txt_generator import InfoTxtGenerator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ComicHubCLI:
    """ComicHub 命令行接口"""

    def __init__(self, config_path: str = "config.yaml"):
        """
        初始化 CLI

        Args:
            config_path: 配置文件路径
        """
        self.config_loader = get_config(config_path)
        self.save_path = self.config_loader.get_save_path()

        # 初始化数据库
        try:
            self.db = Database(config_path)
            logger.info("数据库初始化成功")
        except Exception as e:
            logger.warning(f"数据库初始化失败: {e}")
            self.db = None

        # 初始化抓取器
        self.fetcher = ManhuaGuiFetcherSelenium(headless=True)

    def search_and_fetch(self, keyword: str, limit: int = 1,
                        start_chapter: Optional[int] = None,
                        end_chapter: Optional[int] = None) -> dict:
        """
        模式 1: 基于搜索漫画名的结果逐个抓取

        Args:
            keyword: 搜索关键词
            limit: 下载前 N 部漫画
            start_chapter: 起始章节号
            end_chapter: 结束章节号

        Returns:
            抓取统计信息
        """
        logger.info(f"搜索并抓取漫画: {keyword}")

        stats = {
            'keyword': keyword,
            'found_comics': 0,
            'downloaded_comics': 0,
            'comics': []
        }

        try:
            # 搜索漫画
            comics = self.fetcher.search_comics(keyword)
            stats['found_comics'] = len(comics)

            if not comics:
                logger.warning(f"未找到匹配的漫画: {keyword}")
                return stats

            logger.info(f"找到 {len(comics)} 部漫画")

            # 限制下载数量
            comics_to_download = comics[:limit]
            logger.info(f"将下载前 {len(comics_to_download)} 部漫画")

            # 逐个下载
            for i, comic in enumerate(comics_to_download, 1):
                comic_name = comic['name']
                comic_url = comic['url']

                logger.info(f"\n[{i}/{len(comics_to_download)}] 下载: {comic_name}")

                comic_stats = self.fetch_comic_by_url(
                    comic_url=comic_url,
                    start_chapter=start_chapter,
                    end_chapter=end_chapter
                )

                stats['downloaded_comics'] += 1 if comic_stats['total_chapters'] > 0 else 0
                stats['comics'].append(comic_stats)

        except Exception as e:
            logger.error(f"搜索并抓取失败: {e}")
            import traceback
            traceback.print_exc()

        return stats

    def fetch_comic_by_url(self, comic_url: str,
                          start_chapter: Optional[int] = None,
                          end_chapter: Optional[int] = None) -> dict:
        """
        模式 2: 指定 URL 抓取模式

        Args:
            comic_url: 漫画 URL
            start_chapter: 起始章节号
            end_chapter: 结束章节号

        Returns:
            抓取统计信息
        """
        logger.info(f"抓取漫画: {comic_url}")

        try:
            downloader = BatchDownloader()
            stats = downloader.download_comic(comic_url, start_chapter, end_chapter)
            downloader.close()
            return stats
        except Exception as e:
            logger.error(f"抓取漫画失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                'comic_name': '',
                'total_chapters': 0,
                'downloaded_chapters': 0,
                'total_images': 0,
                'downloaded_images': 0,
                'failed_images': 0
            }

    def fullsite_fetch(self, pages: int = 1) -> dict:
        """
        模式 3: 全站抓取模式

        Args:
            pages: 抓取页数

        Returns:
            抓取统计信息
        """
        logger.warning("全站抓取模式：这将抓取所有漫画，可能需要很长时间")

        stats = {
            'total_pages': pages,
            'downloaded_comics': 0,
            'total_images': 0
        }

        try:
            # 这里实现全站抓取逻辑
            # 由于全站抓取比较复杂，这里只实现基本框架
            logger.info("全站抓取功能开发中...")

        except Exception as e:
            logger.error(f"全站抓取失败: {e}")

        return stats

    def list_comics(self):
        """列出所有已保存的漫画"""
        if not self.db:
            print("数据库未连接，无法列出漫画")
            return

        try:
            comics = self.db.list_comics()

            if not comics:
                print("数据库中没有漫画")
                return

            print(f"\n找到 {len(comics)} 部漫画:\n")

            for i, comic in enumerate(comics, 1):
                print(f"{i}. {comic['name']}")
                print(f"   URL: {comic['url']}")
                if comic.get('author'):
                    print(f"   作者: {comic['author']}")
                if comic.get('status'):
                    print(f"   状态: {comic['status']}")
                print(f"   创建时间: {comic['created_at']}")
                print()

        except Exception as e:
            logger.error(f"列出漫画失败: {e}")

    def show_comic_info(self, comic_name: str):
        """查看漫画详情"""
        if not self.db:
            print("数据库未连接，无法查看漫画详情")
            return

        try:
            comic = self.db.get_comic(name=comic_name)

            if not comic:
                print(f"未找到漫画: {comic_name}")
                return

            print(f"\n{'='*60}")
            print(f"漫画: {comic['name']}")
            print(f"{'='*60}")
            print(f"URL: {comic['url']}")
            print(f"创建时间: {comic['created_at']}")
            print(f"更新时间: {comic['updated_at']}")

            if comic.get('description'):
                print(f"描述: {comic['description']}")
            if comic.get('author'):
                print(f"作者: {comic['author']}")
            if comic.get('status'):
                print(f"状态: {comic['status']}")
            if comic.get('cover_image'):
                print(f"封面: {comic['cover_image']}")

            # 获取章节信息
            chapters = self.db.get_chapters(comic['id'])
            stats = self.db.get_comic_stats(comic['id'])

            print(f"\n章节统计:")
            print(f"  总章节: {stats['total_chapters']}")
            print(f"  已下载: {stats['downloaded_chapters']}")
            print(f"  总图片: {stats['total_images']}")
            print(f"  已下载: {stats['downloaded_images']}")

            if chapters:
                print(f"\n最新 10 个章节:")
                for chapter in chapters[-10:]:
                    mark = "✓" if chapter['downloaded'] else " "
                    print(f"  [{mark}] 第{chapter['chapter_num']}话 - {chapter['title']}")

            print(f"{'='*60}\n")

        except Exception as e:
            logger.error(f"查看漫画详情失败: {e}")

    def cleanup(self):
        """清理资源"""
        if self.fetcher:
            self.fetcher.close()
        if self.db:
            self.db.close()


# CLI 命令定义
@click.group()
@click.version_option(version='1.0.0')
def cli():
    """ComicHub 漫画抓取工具"""
    pass


@cli.command()
@click.option('--keyword', '-k', required=True, help='搜索关键词')
@click.option('--limit', '-l', default=1, help='下载前 N 部漫画（默认: 1）')
@click.option('--start-chapter', '-s', type=int, help='起始章节号')
@click.option('--end-chapter', '-e', type=int, help='结束章节号')
def search(keyword: str, limit: int, start_chapter: Optional[int], end_chapter: Optional[int]):
    """模式 1: 基于搜索漫画名的结果逐个抓取"""
    print(f"\n{'='*60}")
    print("模式 1: 搜索并抓取")
    print(f"{'='*60}")
    print(f"关键词: {keyword}")
    print(f"下载数量: {limit}")
    if start_chapter or end_chapter:
        print(f"章节范围: {start_chapter or '开始'} - {end_chapter or '结束'}")
    print()

    app = ComicHubCLI()
    try:
        stats = app.search_and_fetch(keyword, limit, start_chapter, end_chapter)

        print(f"\n{'='*60}")
        print("抓取完成")
        print(f"{'='*60}")
        print(f"找到漫画: {stats['found_comics']}")
        print(f"下载完成: {stats['downloaded_comics']}")

        for comic_stats in stats['comics']:
            print(f"\n  - {comic_stats['comic_name']}")
            print(f"    章节: {comic_stats['downloaded_chapters']}/{comic_stats['total_chapters']}")
            print(f"    图片: {comic_stats['downloaded_images']}/{comic_stats['total_images']}")

    finally:
        app.cleanup()


@cli.command()
@click.option('--url', '-u', required=True, help='漫画 URL')
@click.option('--start-chapter', '-s', type=int, help='起始章节号')
@click.option('--end-chapter', '-e', type=int, help='结束章节号')
def url(url: str, start_chapter: Optional[int], end_chapter: Optional[int]):
    """模式 2: 指定 URL 抓取"""
    print(f"\n{'='*60}")
    print("模式 2: 指定 URL 抓取")
    print(f"{'='*60}")
    print(f"URL: {url}")
    if start_chapter or end_chapter:
        print(f"章节范围: {start_chapter or '开始'} - {end_chapter or '结束'}")
    print()

    app = ComicHubCLI()
    try:
        stats = app.fetch_comic_by_url(url, start_chapter, end_chapter)

        print(f"\n{'='*60}")
        print("抓取完成")
        print(f"{'='*60}")
        print(f"漫画: {stats['comic_name']}")
        print(f"章节: {stats['downloaded_chapters']}/{stats['total_chapters']}")
        print(f"图片: {stats['downloaded_images']}/{stats['total_images']}")

        if stats['failed_images'] > 0:
            print(f"失败: {stats['failed_images']} 张图片")

    finally:
        app.cleanup()


@cli.command()
@click.option('--pages', '-p', default=1, help='抓取页数（默认: 1）')
def fullsite(pages: int):
    """模式 3: 全站抓取"""
    print(f"\n{'='*60}")
    print("模式 3: 全站抓取")
    print(f"{'='*60}")
    print(f"页数: {pages}")
    print()

    confirm = input("⚠️  全站抓取可能需要很长时间，确认继续？[y/N]: ")
    if confirm.lower() != 'y':
        print("已取消")
        return

    app = ComicHubCLI()
    try:
        stats = app.fullsite_fetch(pages)

        print(f"\n{'='*60}")
        print("抓取完成")
        print(f"{'='*60}")

    finally:
        app.cleanup()


@cli.command()
def list():
    """列出所有已保存的漫画"""
    app = ComicHubCLI()
    try:
        app.list_comics()
    finally:
        app.cleanup()


@cli.command()
@click.option('--name', '-n', required=True, help='漫画名称')
def info(name: str):
    """查看漫画详情"""
    app = ComicHubCLI()
    try:
        app.show_comic_info(name)
    finally:
        app.cleanup()


@cli.command()
@click.option('--url', '-u', help='测试的漫画URL')
@click.option('--keyword', '-k', help='测试搜索关键词')
def test(url: Optional[str], keyword: Optional[str]):
    """测试功能"""
    print(f"\n{'='*60}")
    print("ComicHub 测试模式")
    print(f"{'='*60}\n")

    app = ComicHubCLI()
    try:
        # 默认测试 URL
        if not url:
            url = "https://m.manhuagui.com/comic/1128/"

        # 默认测试关键词
        if not keyword:
            keyword = "海贼王"

        # 测试 1: 搜索
        print("[测试 1] 搜索漫画...")
        results = app.fetcher.search_comics(keyword)
        if results:
            print(f"✅ 搜索成功: {len(results)} 部漫画")
            for i, r in enumerate(results[:3], 1):
                print(f"  {i}. {r['name']} (ID: {r['id']})")
        else:
            print("❌ 搜索失败")

        print()

        # 测试 2: 获取漫画信息
        print("[测试 2] 获取漫画信息...")
        comic_info = app.fetcher.get_comic_info(url)
        if comic_info:
            print(f"✅ 获取成功")
            print(f"  名称: {comic_info['name']}")
            print(f"  ID: {comic_info['id']}")
        else:
            print("❌ 获取失败")

        print()

        # 测试 3: 获取章节列表
        print("[测试 3] 获取章节列表...")
        chapters = app.fetcher.get_chapters(url)
        if chapters:
            print(f"✅ 获取成功: {len(chapters)} 个章节")
            print(f"  前3个章节:")
            for c in chapters[:3]:
                print(f"    第{c['chapter_num']}话 - {c['title']}")
        else:
            print("❌ 获取失败")

        print()
        print(f"{'='*60}")
        print("测试完成")
        print(f"{'='*60}")

    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        app.cleanup()


if __name__ == '__main__':
    cli()
