"""
批量下载模块
负责下载漫画章节图片
"""

import logging
import time
import requests
from pathlib import Path
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

from comichub.core.config import get_config
from comichub.core.database import Database
from comichub.core.fetcher import ManhuaGuiFetcherSelenium

logger = logging.getLogger(__name__)


class BatchDownloader:
    """批量下载器"""

    def __init__(self, config_path: str = "config.yaml"):
        """
        初始化批量下载器

        Args:
            config_path: 配置文件路径
        """
        self.config_loader = get_config(config_path)
        self.fetch_config = self.config_loader.get_fetch_config()
        self.save_path = self.config_loader.get_save_path()

        # 抓取配置
        self.concurrent_downloads = self.fetch_config.get('concurrent_downloads', 5)
        self.delay = self.fetch_config.get('delay', 1)
        self.retry = self.fetch_config.get('retry', 3)
        self.timeout = self.fetch_config.get('timeout', 30)

        # 初始化数据库
        try:
            self.db = Database(config_path)
            logger.info("数据库初始化成功")
        except Exception as e:
            logger.warning(f"数据库初始化失败: {e}")
            self.db = None

        # 初始化抓取器
        self.fetcher = ManhuaGuiFetcherSelenium(headless=True)

        logger.info("批量下载器初始化成功")

    def download_comic(self, comic_url: str, start_chapter: Optional[int] = None,
                       end_chapter: Optional[int] = None, reverse_chapters: bool = False) -> Dict:
        """
        下载整部漫画

        Args:
            comic_url: 漫画URL
            start_chapter: 起始章节号（可选）
            end_chapter: 结束章节号（可选）
            reverse_chapters: 是否反转章节顺序（从第一章开始）

        Returns:
            下载统计信息
        """
        logger.info(f"开始下载漫画: {comic_url}")

        stats = {
            'comic_name': '',
            'total_chapters': 0,
            'downloaded_chapters': 0,
            'total_images': 0,
            'downloaded_images': 0,
            'failed_images': 0
        }

        try:
            # 获取漫画信息
            comic_info = self.fetcher.get_comic_info(comic_url)
            if not comic_info:
                logger.error(f"无法获取漫画信息: {comic_url}")
                return stats

            stats['comic_name'] = comic_info['name']
            comic_name = comic_info['name']

            # 清理文件名
            comic_dir_name = self._sanitize_filename(comic_name)
            comic_dir = self.save_path / comic_dir_name
            comic_dir.mkdir(parents=True, exist_ok=True)

            # 保存到数据库
            comic_id = None
            if self.db:
                try:
                    comic_id = self.db.add_comic(
                        name=comic_name,
                        url=comic_url,
                        description=comic_info.get('description'),
                        cover_image=comic_info.get('cover_image')
                    )
                    self.db.add_fetch_history(comic_id=comic_id, fetch_type='comic',
                                            status='success', metadata={'url': comic_url})
                except Exception as e:
                    logger.warning(f"保存漫画信息到数据库失败: {e}")

            # 获取章节列表
            chapters = self.fetcher.get_chapters(comic_url)
            if not chapters:
                logger.error(f"无法获取章节列表: {comic_url}")
                return stats

            # 反转章节顺序（从第一章开始）
            if reverse_chapters:
                chapters.reverse()
                logger.info("章节顺序已反转，从第一章开始下载")

            stats['total_chapters'] = len(chapters)

            # 过滤章节范围
            if start_chapter is not None or end_chapter is not None:
                chapters = self._filter_chapters(chapters, start_chapter, end_chapter)
                logger.info(f"过滤后章节数: {len(chapters)}")

            # 下载章节
            for i, chapter in enumerate(chapters, 1):
                chapter_num = chapter['chapter_num']
                chapter_title = chapter['title']
                chapter_url = chapter['url']

                logger.info(f"下载章节 [{i}/{len(chapters)}]: {chapter_title}")

                chapter_stats = self.download_chapter(
                    comic_id=comic_id,
                    chapter_url=chapter_url,
                    chapter_num=chapter_num,
                    chapter_title=chapter_title,
                    comic_dir=comic_dir
                )

                stats['downloaded_chapters'] += chapter_stats['success']
                stats['total_images'] += chapter_stats['total_images']
                stats['downloaded_images'] += chapter_stats['downloaded_images']
                stats['failed_images'] += chapter_stats['failed_images']

                # 延迟
                time.sleep(self.delay)

            # 生成 info.txt
            if self.db and comic_id:
                self._generate_info_txt(comic_id, comic_dir, comic_info, chapters)

            logger.info(f"漫画下载完成: {comic_name}")
            logger.info(f"  总章节: {stats['total_chapters']}")
            logger.info(f"  已下载: {stats['downloaded_chapters']}")
            logger.info(f"  总图片: {stats['total_images']}")
            logger.info(f"  成功: {stats['downloaded_images']}")
            logger.info(f"  失败: {stats['failed_images']}")

        except Exception as e:
            logger.error(f"下载漫画失败: {e}")
            import traceback
            traceback.print_exc()

        return stats

    def download_chapter(self, comic_id: Optional[int], chapter_url: str,
                        chapter_num: str, chapter_title: str,
                        comic_dir: Path) -> Dict:
        """
        下载单个章节

        Args:
            comic_id: 漫画ID
            chapter_url: 章节URL
            chapter_num: 章节号
            chapter_title: 章节标题
            comic_dir: 漫画目录

        Returns:
            章节下载统计
        """
        stats = {
            'success': False,
            'total_images': 0,
            'downloaded_images': 0,
            'failed_images': 0
        }

        try:
            # 获取图片列表
            images = self.fetcher.get_images(chapter_url)
            if not images:
                logger.warning(f"无法获取图片列表: {chapter_url}")
                return stats

            stats['total_images'] = len(images)

            # 创建章节目录
            chapter_dir_name = f"第{chapter_num}话"
            chapter_dir = comic_dir / chapter_dir_name
            chapter_dir.mkdir(parents=True, exist_ok=True)

            # 保存章节到数据库
            chapter_id = None
            if self.db and comic_id:
                try:
                    chapter_id = self.db.add_chapter(
                        comic_id=comic_id,
                        chapter_num=chapter_num,
                        title=chapter_title,
                        url=chapter_url,
                        page_count=len(images)
                    )
                except Exception as e:
                    logger.warning(f"保存章节信息到数据库失败: {e}")

            # 下载图片
            downloaded_count = 0
            failed_count = 0

            with ThreadPoolExecutor(max_workers=self.concurrent_downloads) as executor:
                futures = {}
                for i, img_url in enumerate(images, 1):
                    filename = f"{i:03d}.jpg"
                    save_path = chapter_dir / filename

                    future = executor.submit(self._download_image, img_url, save_path)
                    futures[future] = (i, filename)

                # 等待完成
                for future in tqdm(as_completed(futures), total=len(futures),
                                 desc=f"下载 {chapter_dir_name}", unit="张"):
                    i, filename = futures[future]
                    try:
                        success = future.result()
                        if success:
                            downloaded_count += 1
                        else:
                            failed_count += 1
                    except Exception as e:
                        logger.error(f"下载图片异常 {filename}: {e}")
                        failed_count += 1

            stats['downloaded_images'] = downloaded_count
            stats['failed_images'] = failed_count
            stats['success'] = downloaded_count > 0

            # 标记章节已下载
            if self.db and chapter_id:
                try:
                    self.db.mark_chapter_downloaded(chapter_id)
                    self.db.add_fetch_history(
                        comic_id=comic_id,
                        chapter_id=chapter_id,
                        fetch_type='chapter',
                        status='success',
                        metadata={
                            'downloaded_images': downloaded_count,
                            'failed_images': failed_count
                        }
                    )
                except Exception as e:
                    logger.warning(f"更新章节状态失败: {e}")

            logger.info(f"章节下载完成: {chapter_title} ({downloaded_count}/{len(images)})")

        except Exception as e:
            logger.error(f"下载章节失败: {chapter_url}, 错误: {e}")
            if self.db and comic_id:
                try:
                    self.db.add_fetch_history(
                        comic_id=comic_id,
                        fetch_type='chapter',
                        status='failed',
                        error_msg=str(e),
                        metadata={'chapter_url': chapter_url}
                    )
                except:
                    pass

        return stats

    def _download_image(self, url: str, save_path: Path) -> bool:
        """
        下载单张图片

        Args:
            url: 图片URL
            save_path: 保存路径

        Returns:
            是否成功
        """
        # 检查文件是否已存在且有内容（避免重复下载）
        if save_path.exists() and save_path.stat().st_size > 0:
            logger.debug(f"文件已存在，跳过下载: {save_path.name}")
            return True

        for attempt in range(self.retry):
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                    'Referer': 'https://m.manhuagui.com/'
                }

                response = requests.get(url, headers=headers, timeout=self.timeout, verify=False)
                if response.status_code == 200:
                    with open(save_path, 'wb') as f:
                        f.write(response.content)
                    return True
                else:
                    logger.warning(f"下载失败 {url}: 状态码 {response.status_code}")

            except Exception as e:
                if attempt < self.retry - 1:
                    time.sleep(1)
                    continue
                logger.debug(f"下载图片失败 {url}: {e}")

        return False

    def _filter_chapters(self, chapters: List[Dict], start: Optional[int],
                        end: Optional[int]) -> List[Dict]:
        """过滤章节范围"""
        filtered = []

        for chapter in chapters:
            try:
                num = int(chapter['chapter_num'])
                if start is not None and num < start:
                    continue
                if end is not None and num > end:
                    continue
                filtered.append(chapter)
            except ValueError:
                # 如果无法转换为数字，保留
                filtered.append(chapter)

        return filtered

    def _sanitize_filename(self, name: str) -> str:
        """清理文件名"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        return name.strip()

    def _generate_info_txt(self, comic_id: int, comic_dir: Path,
                          comic_info: Dict, chapters: List[Dict]):
        """生成 info.txt 文件"""
        try:
            # 获取统计信息
            stats = self.db.get_comic_stats(comic_id)
            fetched_chapters = self.db.get_fetched_chapters(comic_id)

            content = f"""# 漫画信息

名称：{comic_info.get('name', 'N/A')}
URL：{comic_info.get('url', 'N/A')}
描述：{comic_info.get('description', 'N/A')}

# 章节信息

总章节数：{len(chapters)}
已抓取章节：{len(fetched_chapters)}

# 下载统计

总图片数：{stats['total_images']}
已下载图片：{stats['downloaded_images']}
总章节：{stats['total_chapters']}
已下载章节：{stats['downloaded_chapters']}

# 抓取记录

抓取时间：{time.strftime('%Y-%m-%d %H:%M:%S')}
"""

            info_file = comic_dir / 'info.txt'
            with open(info_file, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info(f"已生成 info.txt: {info_file}")

        except Exception as e:
            logger.warning(f"生成 info.txt 失败: {e}")

    def close(self):
        """关闭下载器"""
        if self.fetcher:
            self.fetcher.close()
        if self.db:
            self.db.close()


if __name__ == "__main__":
    # 测试批量下载
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    downloader = BatchDownloader()

    # 测试下载海贼王
    test_url = "https://m.manhuagui.com/comic/1128/"
    stats = downloader.download_comic(test_url, start_chapter=1170, end_chapter=1172)

    print(f"\n下载统计:")
    print(f"  漫画名称: {stats['comic_name']}")
    print(f"  总章节: {stats['total_chapters']}")
    print(f"  已下载: {stats['downloaded_chapters']}")
    print(f"  总图片: {stats['total_images']}")
    print(f"  成功: {stats['downloaded_images']}")
    print(f"  失败: {stats['failed_images']}")

    downloader.close()
