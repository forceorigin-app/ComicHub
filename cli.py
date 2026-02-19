#!/usr/bin/env python3
"""
ComicHub CLI - 主入口程序

漫画抓取工具，支持多种下载模式：
  • 搜索并下载：根据关键词搜索漫画并下载
  • URL 下载：直接指定漫画 URL 下载
  • 数据库管理：查看已下载漫画的详细信息

配置文件：config.yaml
"""

import sys
import logging
import time
import re
from pathlib import Path
from typing import Optional, List
import click
import requests

from comichub.core.config import get_config
from comichub.core.database import Database
from comichub.core.fetcher import ManhuaGuiFetcherSelenium
from comichub.downloader.batch import BatchDownloader
from comichub.utils.info import InfoTxtGenerator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Telegram 通知和进度日志辅助函数
def send_telegram_message(bot_token: str, chat_id: str, text: str) -> bool:
    """
    发送 Telegram 消息

    Args:
        bot_token: Telegram Bot Token
        chat_id: Telegram Chat ID
        text: 消息内容

    Returns:
        是否发送成功
    """
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        response = requests.post(url, json={'chat_id': chat_id, 'text': text}, timeout=10)
        return response.status_code == 200
    except Exception as e:
        logger.warning(f"发送 Telegram 消息失败: {e}")
        return False


def log_progress(log_path: Path, msg: str):
    """
    写入进度日志

    Args:
        log_path: 日志文件路径
        msg: 日志消息
    """
    try:
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {msg}\n")
    except Exception as e:
        logger.warning(f"写入进度日志失败: {e}")


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

        # Telegram 配置
        self.telegram_enabled = self.config_loader.is_telegram_enabled()
        self.telegram_bot_token = self.config_loader.get_telegram_bot_token()
        self.telegram_chat_id = self.config_loader.get_telegram_chat_id()
        self.telegram_report_interval = self.config_loader.get_telegram_report_interval() * 60  # 转为秒
        self.telegram_report_chapter_interval = self.config_loader.get_telegram_report_chapter_interval()

        # 进度日志
        self.progress_log_path = self.config_loader.get_progress_log_path()

        # 初始化数据库
        try:
            self.db = Database(config_path)
            logger.info("数据库初始化成功")
        except Exception as e:
            logger.warning(f"数据库初始化失败: {e}")
            self.db = None

        # 初始化抓取器
        self.fetcher = ManhuaGuiFetcherSelenium(headless=True)

    def send_notification(self, text: str):
        """发送 Telegram 通知（如果启用）"""
        if self.telegram_enabled and self.telegram_bot_token and self.telegram_chat_id:
            send_telegram_message(self.telegram_bot_token, self.telegram_chat_id, text)

    def log_progress(self, msg: str):
        """写入进度日志"""
        log_progress(self.progress_log_path, msg)

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
                          end_chapter: Optional[int] = None,
                          reverse_chapters: bool = False) -> dict:
        """
        模式 2: 指定 URL 抓取模式

        Args:
            comic_url: 漫画 URL
            start_chapter: 起始章节号
            end_chapter: 结束章节号
            reverse_chapters: 是否反转章节顺序（从第一章开始）

        Returns:
            抓取统计信息
        """
        logger.info(f"抓取漫画: {comic_url}")
        log_msg = f"开始下载: {comic_url}"
        if reverse_chapters:
            log_msg += " (从第一章开始)"
        self.log_progress(log_msg)

        try:
            downloader = BatchDownloader()
            stats = downloader.download_comic(comic_url, start_chapter, end_chapter, reverse_chapters)
            downloader.close()

            # 记录完成日志
            log_msg = f"下载完成: {stats['comic_name']} - 章节: {stats['downloaded_chapters']}/{stats['total_chapters']}, 图片: {stats['downloaded_images']}/{stats['total_images']}"
            self.log_progress(log_msg)
            self.send_notification(f"✅ {log_msg}")

            return stats
        except Exception as e:
            logger.error(f"抓取漫画失败: {e}")
            self.log_progress(f"下载失败: {e}")
            self.send_notification(f"❌ 下载失败: {e}")
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

    def check_download_integrity(self, comic_url: str, verify: bool = False) -> dict:
        """
        检查下载完整性

        Args:
            comic_url: 漫画 URL
            verify: 是否验证图片数量（需要重新获取章节信息，较慢）

        Returns:
            检查结果统计
        """
        import os

        logger.info(f"检查下载完整性: {comic_url}")

        try:
            # 获取漫画信息
            comic_info = self.fetcher.get_comic_info(comic_url)
            if not comic_info:
                logger.error(f"无法获取漫画信息: {comic_url}")
                return {'error': '无法获取漫画信息'}

            comic_name = comic_info['name']
            comic_dir_name = re.sub(r'[\\/:*?"<>|]', '', comic_name)
            comic_dir = self.save_path / comic_dir_name

            if not comic_dir.exists():
                return {
                    'comic_name': comic_name,
                    'total_chapters': 0,
                    'missing_chapters': 0,
                    'incomplete_chapters': 0,
                    'complete_chapters': 0,
                    'details': []
                }

            # 获取章节列表
            chapters = self.fetcher.get_chapters(comic_url)
            if not chapters:
                return {'error': '无法获取章节列表'}

            result = {
                'comic_name': comic_name,
                'total_chapters': len(chapters),
                'missing_chapters': 0,
                'incomplete_chapters': 0,
                'complete_chapters': 0,
                'details': []
            }

            print(f"\n{'='*60}")
            print(f"检查漫画: {comic_name}")
            print(f"路径: {comic_dir}")
            if verify:
                print(f"模式: 完整验证（会重新获取章节信息）")
            else:
                print(f"模式: 快速检查（仅验证文件存在）")
            print(f"{'='*60}\n")

            for idx, chapter in enumerate(chapters, 1):
                chapter_title = chapter['title']
                chapter_dir_name = re.sub(r'[\\/:*?"<>|]', '', chapter_title)
                chapter_dir = comic_dir / chapter_dir_name

                if not chapter_dir.exists():
                    result['missing_chapters'] += 1
                    result['details'].append({
                        'title': chapter_title,
                        'status': 'missing',
                        'reason': '章节目录不存在'
                    })
                    print(f"❌ 缺失: {chapter_title}")
                else:
                    files = list(chapter_dir.glob('*'))
                    if not files:
                        result['incomplete_chapters'] += 1
                        result['details'].append({
                            'title': chapter_title,
                            'status': 'incomplete',
                            'reason': '目录为空',
                            'file_count': 0
                        })
                        print(f"⚠️  不完整: {chapter_title} (空目录)")
                    else:
                        # 检查是否有空文件
                        empty_files = [f for f in files if f.stat().st_size == 0]
                        if empty_files:
                            result['incomplete_chapters'] += 1
                            result['details'].append({
                                'title': chapter_title,
                                'status': 'incomplete',
                                'reason': f'{len(empty_files)} 个空文件',
                                'file_count': len(files),
                                'empty_files': len(empty_files)
                            })
                            print(f"⚠️  不完整: {chapter_title} ({len(files)} 张图片, {len(empty_files)} 个失败)")
                        elif verify:
                            # 完整验证：优先使用快速方法获取图片数量
                            print(f"🔍 验证中 [{idx}/{len(chapters)}]: {chapter_title}...", end='\r', flush=True)
                            try:
                                # 优先级：1. 数据库 > 2. 快速方法（页面指示器） > 3. 完整获取
                                expected_count = None

                                # 1. 尝试从数据库获取
                                if self.db:
                                    chapters_in_db = self.db.get_chapters_by_url(chapter['url'])
                                    if chapters_in_db:
                                        expected_count = chapters_in_db[0].get('page_count')

                                # 2. 如果数据库没有，使用快速方法（只读取页面指示器）
                                if expected_count is None or expected_count == 0:
                                    expected_count = self.fetcher.get_image_count(chapter['url'])

                                actual_count = len(files)

                                if expected_count == 0:
                                    # 如果快速方法也失败，使用完整获取（作为最后的后备）
                                    logger.debug(f"快速方法失败，使用完整获取: {chapter_title}")
                                    result = self.fetcher.get_images(chapter['url'])
                                    expected_count = result['total_count']
                                    actual_count = len(files)

                                if actual_count < expected_count:
                                    result['incomplete_chapters'] += 1
                                    missing = expected_count - actual_count
                                    result['details'].append({
                                        'title': chapter_title,
                                        'status': 'incomplete',
                                        'reason': f'缺少 {missing} 张图片',
                                        'file_count': actual_count,
                                        'expected_count': expected_count
                                    })
                                    print(f"⚠️  不完整: {chapter_title} ({actual_count}/{expected_count} 张，缺少 {missing} 张)")
                                else:
                                    result['complete_chapters'] += 1
                                    print(f"✅ 完整: {chapter_title} ({actual_count} 张)")
                            except Exception as e:
                                result['incomplete_chapters'] += 1
                                result['details'].append({
                                    'title': chapter_title,
                                    'status': 'incomplete',
                                    'reason': f'验证失败: {str(e)}',
                                    'file_count': len(files)
                                })
                                print(f"⚠️  验证失败: {chapter_title}")
                        else:
                            # 快速检查：只检查文件存在
                            result['complete_chapters'] += 1
                            print(f"✅ 完整: {chapter_title} ({len(files)} 张)")

            print(f"\n{'='*60}")
            print("检查完成")
            print(f"{'='*60}")
            print(f"总章节数: {result['total_chapters']}")
            print(f"✅ 完整: {result['complete_chapters']}")
            print(f"❌ 缺失: {result['missing_chapters']}")
            print(f"⚠️  不完整: {result['incomplete_chapters']}")

            if result['missing_chapters'] > 0 or result['incomplete_chapters'] > 0:
                print(f"\n💡 提示: 重新运行下载命令将自动修复问题")
                print(f"   python cli.py url -u \"{comic_url}\" --all")
            elif not verify:
                print(f"\n💡 提示: 如需验证图片数量是否完整，请使用 --verify 选项")
                print(f"   python cli.py check -u \"{comic_url}\" --verify")

            return result

        except Exception as e:
            logger.error(f"检查完整性失败: {e}")
            import traceback
            traceback.print_exc()
            return {'error': str(e)}

    def cleanup(self):
        """清理资源"""
        if self.fetcher:
            self.fetcher.close()
        if self.db:
            self.db.close()


# CLI 命令定义
@click.group(invoke_without_command=True)
@click.version_option(version='1.0.0', prog_name='comichub')
@click.pass_context
def cli(ctx):
    """ComicHub - 漫画抓取工具

    \b
    使用示例：
      python cli.py url -u "URL" --all           # 下载所有章节（从第一章开始）
      python cli.py url -u "URL" -s 1 -e 100     # 下载第1-100章
      python cli.py search -k "海贼王" -l 1       # 搜索并下载第1部结果
      python cli.py list                         # 列出所有已下载漫画
      python cli.py info -n "海贼王"              # 查看漫画详情
      python cli.py examples                     # 查看更多使用示例
    """
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command()
@click.option('--keyword', '-k', required=True, help='搜索关键词（例如：海贼王、火影忍者）')
@click.option('--limit', '-l', default=1, help='下载前 N 部漫画（默认: 1）')
@click.option('--start-chapter', '-s', type=int, help='起始章节号（例如：1）')
@click.option('--end-chapter', '-e', type=int, help='结束章节号（例如：100）')
def search(keyword: str, limit: int, start_chapter: Optional[int], end_chapter: Optional[int]):
    """搜索并下载漫画

    \b
    根据关键词搜索漫画，并下载搜索结果。

    \b
    示例：
      python cli.py search -k "海贼王"                    # 下载搜索到的第1部漫画
      python cli.py search -k "火影" -l 3                # 下载前3部搜索结果
      python cli.py search -k "死神" -s 1 -e 50          # 下载第1-50章
      python cli.py search -k "银魂" --start-chapter 10   # 从第10章开始下载
    """
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
@click.option('--url', '-u', required=True, help='漫画 URL（例如：https://m.manhuagui.com/comic/2592/）')
@click.option('--start-chapter', '-s', type=int, help='起始章节号（与 --all 互斥）')
@click.option('--end-chapter', '-e', type=int, help='结束章节号（与 --all 互斥）')
@click.option('--all', '-a', is_flag=True, help='下载所有章节，从第一章开始正序下载')
def url(url: str, start_chapter: Optional[int], end_chapter: Optional[int], all: bool):
    """根据 URL 下载漫画

    \b
    直接指定漫画 URL 进行下载，支持章节范围选择。

    \b
    下载模式：
      • 默认：倒序下载（从最新章节开始）
      • --all：正序下载（从第一章开始，推荐追更使用）

    \b
    示例：
      python cli.py url -u "https://m.manhuagui.com/comic/2592/" --all      # 从第一章开始全部下载
      python cli.py url -u "https://m.manhuagui.com/comic/2592/" -s 1 -e 100 # 下载第1-100章
      python cli.py url -u "https://m.manhuagui.com/comic/2592/"             # 下载最新章节
      python cli.py url -u "URL" --start-chapter 50                          # 从第50章开始
    """
    print(f"\n{'='*60}")
    print("模式 2: 指定 URL 抓取")
    print(f"{'='*60}")
    print(f"URL: {url}")
    if all:
        print(f"下载模式: 所有章节（从第一章开始）")
    elif start_chapter or end_chapter:
        print(f"章节范围: {start_chapter or '开始'} - {end_chapter or '结束'}")
    print()

    app = ComicHubCLI()
    try:
        stats = app.fetch_comic_by_url(url, start_chapter, end_chapter, reverse_chapters=all)

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
@click.option('--pages', '-p', default=1, help='抓取页数（默认: 1，当前功能开发中）')
def fullsite(pages: int):
    """全站抓取模式（开发中）

    \b
    示例：
      python cli.py fullsite -p 1    # 抓取第1页的所有漫画
    """
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


@cli.command(name='list')
def list_comics():
    """列出所有已下载的漫画

    \b
    从数据库中读取并显示所有已保存的漫画信息。

    \b
    示例：
      python cli.py list
    """
    app = ComicHubCLI()
    try:
        app.list_comics()
    finally:
        app.cleanup()


@cli.command()
@click.option('--name', '-n', required=True, help='漫画名称（支持模糊匹配）')
def info(name: str):
    """查看漫画详细信息

    \b
    显示指定漫画的详细统计信息，包括章节数量、下载进度等。

    \b
    示例：
      python cli.py info -n "海贼王"
      python cli.py info -n "火影"
    """
    app = ComicHubCLI()
    try:
        app.show_comic_info(name)
    finally:
        app.cleanup()


@cli.command()
@click.option('--url', '-u', required=True, help='漫画 URL')
@click.option('--verify', '-v', is_flag=True, help='完整验证模式（重新获取章节信息，验证图片数量）')
def check(url: str, verify: bool):
    """检查下载完整性

    \b
    检查漫画的下载状态，找出缺失或不完整的章节。

    \b
    检查模式：
      • 快速检查（默认）：只检查文件是否存在
      • 完整验证（--verify）：重新获取章节信息，验证图片数量

    \b
    示例：
      python cli.py check -u "https://m.manhuagui.com/comic/2592/"           # 快速检查
      python cli.py check -u "https://m.manhuagui.com/comic/2592/" --verify # 完整验证

    \b
    检查完成后，如有问题，重新运行下载命令即可自动修复：
      python cli.py url -u "https://m.manhuagui.com/comic/2592/" --all
    """
    app = ComicHubCLI()
    try:
        app.check_download_integrity(url, verify=verify)
    finally:
        app.cleanup()


@cli.command()
@click.option('--url', '-u', help='测试的漫画URL')
@click.option('--keyword', '-k', help='测试搜索关键词')
def test(url: Optional[str], keyword: Optional[str]):
    """测试抓取器功能

    \b
    运行测试以验证 Selenium、网络连接和解析功能是否正常。

    \b
    示例：
      python cli.py test                                    # 使用默认测试用例
      python cli.py test -u "https://m.manhuagui.com/comic/1128/"
      python cli.py test -k "海贼王"
    """
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


@cli.command(name='examples')
def show_examples():
    """显示详细的使用示例"""
    examples = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                           ComicHub 使用示例                                    ║
╚══════════════════════════════════════════════════════════════════════════════╝

📚 基础用法
─────────────────────────────────────────────────────────────────────────────
  # 查看帮助
  python cli.py --help

  # 查看某个命令的帮助
  python cli.py url --help


🔗 URL 下载（最常用）
─────────────────────────────────────────────────────────────────────────────
  # 从第一章开始，正序下载所有章节（推荐追更）
  python cli.py url -u "https://m.manhuagui.com/comic/2592/" --all

  # 下载指定章节范围
  python cli.py url -u "https://m.manhuagui.com/comic/2592/" -s 1 -e 100

  # 下载最新章节（默认行为，倒序）
  python cli.py url -u "https://m.manhuagui.com/comic/2592/"

  # 从第50章开始下载到最新
  python cli.py url -u "URL" --start-chapter 50


🔍 搜索下载
─────────────────────────────────────────────────────────────────────────────
  # 搜索并下载第1部结果
  python cli.py search -k "海贼王"

  # 搜索并下载前3部结果
  python cli.py search -k "火影" -l 3

  # 搜索并下载指定章节范围
  python cli.py search -k "死神" -s 1 -e 50


📊 数据库管理
─────────────────────────────────────────────────────────────────────────────
  # 列出所有已下载的漫画
  python cli.py list

  # 查看漫画详细信息（包含下载进度）
  python cli.py info -n "海贼王"


🔍 查漏补缺
─────────────────────────────────────────────────────────────────────────────
  # 快速检查：验证文件是否存在
  python cli.py check -u "https://m.manhuagui.com/comic/2592/"

  # 完整验证：重新获取章节信息，验证图片数量（较慢但更准确）
  python cli.py check -u "https://m.manhuagui.com/comic/2592/" --verify

  # 重新运行下载命令来自动修复问题（会跳过已下载的文件）
  python cli.py url -u "https://m.manhuagui.com/comic/2592/" --all


🧪 测试功能
─────────────────────────────────────────────────────────────────────────────
  # 测试默认漫画和关键词
  python cli.py test

  # 测试指定的漫画
  python cli.py test -u "https://m.manhuagui.com/comic/1128/"

  # 测试搜索功能
  python cli.py test -k "海贼王"


💡 使用技巧
─────────────────────────────────────────────────────────────────────────────
  • 短选项：-u (url), -k (keyword), -s (start-chapter), -e (end-chapter), -a (all)
  • --all 标志会从第一章开始正序下载，适合追更
  • 不使用 --all 时，默认从最新章节开始倒序下载
  • 文件存在时会自动跳过，支持断点续传
  • 配置文件：config.yaml（修改保存路径、Telegram 通知等）


📝 配置 Telegram 通知（可选）
─────────────────────────────────────────────────────────────────────────────
  1. 编辑 config.yaml，设置 telegram.enabled = true
  2. 填写 bot_token 和 chat_id
  3. 调整 report_interval（分钟）和 report_chapter_interval（章数）

  获取 Bot Token：
    • 向 @BotFather 发送 /newbot
    • 按提示创建机器人并复制 Token

  获取 Chat ID：
    • 向 @userinfobot 发送任意消息
    • 复制返回的 Chat ID


🔧 故障排查
─────────────────────────────────────────────────────────────────────────────
  问题：ChromeDriver 找不到
  解决：brew install chromedriver

  问题：下载的章节只有30张图片
  解决：已修复，重新运行即可

  问题：部分图片下载失败
  解决：正常现象，程序会自动重试，失败的图片不影响其他图片

  问题：需要重新下载某章节
  解决：删除对应章节文件夹，重新运行命令

  问题：网络问题导致下载不完整
  解决：
    1. 先检查完整性：python cli.py check -u "URL"
    2. 重新运行下载：python cli.py url -u "URL" --all
       程序会自动跳过已下载的文件，只下载缺失的部分

  问题：下载中断后如何继续
  解决：直接重新运行相同的下载命令，程序会自动续传
"""
    click.echo(examples)


if __name__ == '__main__':
    cli()
