"""
info.txt 生成器模块
负责生成漫画目录下的 info.txt 文件
"""

import logging
import time
from pathlib import Path
from typing import Dict, List, Optional

from comichub.core.database import Database

logger = logging.getLogger(__name__)


class InfoTxtGenerator:
    """info.txt 生成器"""

    def __init__(self, database: Database):
        """
        初始化生成器

        Args:
            database: 数据库实例
        """
        self.db = database

    def generate(self, comic_id: int, comic_dir: Path, comic_info: Dict,
                 chapters: Optional[List[Dict]] = None) -> bool:
        """
        生成 info.txt 文件

        Args:
            comic_id: 漫画ID
            comic_dir: 漫画目录
            comic_info: 漫画信息
            chapters: 章节列表（可选）

        Returns:
            是否成功
        """
        try:
            # 获取数据库中的章节信息
            if chapters is None:
                chapters = self.db.get_chapters(comic_id)

            # 获取统计信息
            stats = self.db.get_comic_stats(comic_id)
            fetched_chapters = self.db.get_fetched_chapters(comic_id)

            # 获取漫画详细信息
            comic_detail = self.db.get_comic(comic_id=comic_id)

            # 构建内容
            content = self._build_content(
                comic_info=comic_info,
                comic_detail=comic_detail,
                chapters=chapters,
                stats=stats,
                fetched_chapters=fetched_chapters
            )

            # 写入文件
            info_file = comic_dir / 'info.txt'
            with open(info_file, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info(f"已生成 info.txt: {info_file}")
            return True

        except Exception as e:
            logger.error(f"生成 info.txt 失败: {e}")
            return False

    def _build_content(self, comic_info: Dict, comic_detail: Optional[Dict],
                      chapters: List[Dict], stats: Dict,
                      fetched_chapters: List[str]) -> str:
        """构建 info.txt 内容"""

        lines = [
            "=" * 60,
            "漫画信息",
            "=" * 60,
            "",
        ]

        # 基本信息
        lines.extend([
            f"名称：{comic_info.get('name', 'N/A')}",
            f"URL：{comic_info.get('url', 'N/A')}",
        ])

        # 详细信息（如果从数据库获取）
        if comic_detail:
            if comic_detail.get('author'):
                lines.append(f"作者：{comic_detail['author']}")
            if comic_detail.get('status'):
                lines.append(f"状态：{comic_detail['status']}")
            if comic_detail.get('description'):
                lines.append(f"描述：{comic_detail['description']}")

        lines.extend([
            "",
            "=" * 60,
            "章节信息",
            "=" * 60,
            "",
            f"总章节数：{len(chapters)}",
            f"已抓取章节：{len(fetched_chapters)}",
        ])

        # 最新章节
        if chapters:
            latest = chapters[-1]
            lines.append(f"最新章节：第{latest['chapter_num']}话 - {latest['title']}")

        lines.extend([
            "",
            "=" * 60,
            "下载统计",
            "=" * 60,
            "",
            f"总图片数：{stats['total_images']}",
            f"已下载图片：{stats['downloaded_images']}",
            f"总章节：{stats['total_chapters']}",
            f"已下载章节：{stats['downloaded_chapters']}",
            "",
        ])

        # 下载进度
        if stats['total_images'] > 0:
            progress = (stats['downloaded_images'] / stats['total_images']) * 100
            lines.append(f"下载进度：{progress:.1f}%")

        lines.extend([
            "",
            "=" * 60,
            "抓取记录",
            "=" * 60,
            "",
            f"抓取时间：{time.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
        ])

        # 章节列表（前20个和后20个）
        if chapters and len(chapters) > 0:
            lines.extend([
                "=" * 60,
                "章节列表",
                "=" * 60,
                "",
            ])

            display_count = min(20, len(chapters))
            lines.append(f"前 {display_count} 个章节:")
            for i, chapter in enumerate(chapters[:display_count], 1):
                downloaded_mark = "✓" if chapter.get('downloaded') else " "
                lines.append(f"  [{downloaded_mark}] 第{chapter['chapter_num']}话 - {chapter['title']}")

            if len(chapters) > display_count:
                lines.append(f"  ... 省略 {len(chapters) - 2 * display_count} 个章节 ...")
                for chapter in chapters[-display_count:]:
                    downloaded_mark = "✓" if chapter.get('downloaded') else " "
                    lines.append(f"  [{downloaded_mark}] 第{chapter['chapter_num']}话 - {chapter['title']}")

            lines.append("")

        lines.extend([
            "=" * 60,
            f"由 ComicHub 自动生成 | {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 60,
        ])

        return "\n".join(lines)

    def update(self, comic_id: int, comic_dir: Path) -> bool:
        """
        更新已有的 info.txt 文件

        Args:
            comic_id: 漫画ID
            comic_dir: 漫画目录

        Returns:
            是否成功
        """
        try:
            # 获取漫画信息
            comic_detail = self.db.get_comic(comic_id=comic_id)
            if not comic_detail:
                logger.warning(f"找不到漫画 ID: {comic_id}")
                return False

            # 获取章节信息
            chapters = self.db.get_chapters(comic_id)

            # 构建基本信息
            comic_info = {
                'name': comic_detail['name'],
                'url': comic_detail['url'],
                'description': comic_detail.get('description'),
            }

            return self.generate(comic_id, comic_dir, comic_info, chapters)

        except Exception as e:
            logger.error(f"更新 info.txt 失败: {e}")
            return False


def create_info_txt_generator(database: Database) -> InfoTxtGenerator:
    """
    创建 info.txt 生成器

    Args:
        database: 数据库实例

    Returns:
        InfoTxtGenerator 实例
    """
    return InfoTxtGenerator(database)


if __name__ == "__main__":
    # 测试生成器
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        db = Database()
        generator = InfoTxtGenerator(db)

        # 列出所有漫画
        comics = db.list_comics()

        if comics:
            print(f"找到 {len(comics)} 部漫画")

            # 为第一部漫画生成 info.txt
            comic = comics[0]
            comic_dir = Path('~/data/comics').expanduser() / comic['name']

            print(f"\n为漫画生成 info.txt: {comic['name']}")
            print(f"目录: {comic_dir}")

            success = generator.update(comic['id'], comic_dir)

            if success:
                print("✅ 生成成功")
            else:
                print("❌ 生成失败")
        else:
            print("数据库中没有漫画")

        db.close()

    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
