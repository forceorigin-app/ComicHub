"""
数据库操作模块 - 修复版
修复了 c.downloaded 拼写错误
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging
from pathlib import Path

from config_loader import get_config

logger = logging.getLogger(__name__)


class Database:
    """数据库操作类"""

    def __init__(self, config_path: str = "config.yaml"):
        """
        初始化数据库连接

        Args:
            config_path: 配置文件路径
        """
        self.config_loader = get_config(config_path)
        self.db_config = self.config_loader.get_database_config()
        self.conn = None
        self.connect()

    def connect(self):
        """建立数据库连接"""
        try:
            self.conn = psycopg2.connect(
                host=self.db_config.get('host', 'localhost'),
                port=self.db_config.get('port', 5432),
                database=self.db_config.get('database', 'postgres'),
                user=self.db_config.get('user', 'postgres'),
                password=self.db_config.get('password', 'postgres')
            )
            logger.info("数据库连接成功")
            self.init_tables()
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            raise

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            logger.info("数据库连接已关闭")

    def init_tables(self):
        """初始化数据库表"""
        cursor = self.conn.cursor()

        # 创建漫画表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS comics (
                id SERIAL PRIMARY KEY,
                name VARCHAR(500) NOT NULL UNIQUE,
                url VARCHAR(1000) NOT NULL UNIQUE,
                description TEXT,
                cover_image VARCHAR(1000),
                author VARCHAR(200),
                status VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 创建章节表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chapters (
                id SERIAL PRIMARY KEY,
                comic_id INTEGER NOT NULL REFERENCES comics(id) ON DELETE CASCADE,
                chapter_num VARCHAR(100),
                title VARCHAR(500),
                url VARCHAR(1000) NOT NULL UNIQUE,
                page_count INTEGER DEFAULT 0,
                downloaded BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(comic_id, chapter_num)
            );
        """)

        # 创建图片表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS images (
                id SERIAL PRIMARY KEY,
                chapter_id INTEGER NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
                page_num INTEGER NOT NULL,
                url VARCHAR(1000) NOT NULL,
                file_path VARCHAR(1000),
                downloaded BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(chapter_id, page_num)
            );
        """)

        # 创建抓取历史表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fetch_history (
                id SERIAL PRIMARY KEY,
                comic_id INTEGER REFERENCES comics(id) ON DELETE SET NULL,
                chapter_id INTEGER REFERENCES chapters(id) ON DELETE SET NULL,
                fetch_type VARCHAR(50),
                fetch_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(50) NOT NULL,
                error_msg TEXT,
                metadata JSONB
            );
        """)

        # 创建索引以提高查询性能
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_chapters_comic_id ON chapters(comic_id);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_images_chapter_id ON images(chapter_id);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_fetch_history_comic_id ON fetch_history(comic_id);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_fetch_history_fetch_time ON fetch_history(fetch_time);
        """)

        self.conn.commit()
        logger.info("数据库表初始化完成")

    def comic_exists(self, url: str) -> Optional[int]:
        """
        检查漫画是否已存在

        Args:
            url: 漫画URL

        Returns:
            漫画ID，如果不存在返回 None
        """
        cur = self.conn.cursor()
        cur.execute("SELECT id FROM comics WHERE url = %s", (url,))
        result = cur.fetchone()
        return result[0] if result else None

    def get_comic_by_name(self, name: str) -> Optional[Dict]:
        """
        根据名称获取漫画

        Args:
            name: 漫画名称

        Returns:
            漫画信息字典
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM comics WHERE name = %s", (name,))
        return cur.fetchone()

    def add_comic(self, name: str, url: str, description: str = None,
                  cover_image: str = None, author: str = None, status: str = None) -> int:
        """
        添加漫画

        Args:
            name: 漫画名称
            url: 漫画URL
            description: 描述
            cover_image: 封面图片URL
            author: 作者
            status: 状态

        Returns:
            漫画ID
        """
        cur = self.conn.cursor()
        try:
            cur.execute("""
                INSERT INTO comics (name, url, description, cover_image, author, status)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (url) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    cover_image = EXCLUDED.cover_image,
                    author = EXCLUDED.author,
                    status = EXCLUDED.status,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
            """, (name, url, description, cover_image, author, status))
            self.conn.commit()
            comic_id = cur.fetchone()[0]
            logger.info(f"漫画已添加/更新: {name} (ID: {comic_id})")
            return comic_id
        except Exception as e:
            self.conn.rollback()
            logger.error(f"添加漫画失败: {e}")
            raise

    def add_chapter(self, comic_id: int, chapter_num: str, title: str, url: str, page_count: int = 0) -> int:
        """
        添加章节

        Args:
            comic_id: 漫画ID
            chapter_num: 章节号
            title: 章节标题
            url: 章节URL
            page_count: 页数

        Returns:
            章节ID
        """
        cur = self.conn.cursor()
        try:
            cur.execute("""
                INSERT INTO chapters (comic_id, chapter_num, title, url, page_count)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (url) DO UPDATE SET
                    chapter_num = EXCLUDED.chapter_num,
                    title = EXCLUDED.title,
                    page_count = EXCLUDED.page_count
                RETURNING id
            """, (comic_id, chapter_num, title, url, page_count))
            self.conn.commit()
            chapter_id = cur.fetchone()[0]
            return chapter_id
        except Exception as e:
            self.conn.rollback()
            logger.error(f"添加章节失败: {e}")
            raise

    def add_image(self, chapter_id: int, page_num: int, url: str,
                 file_path: str = None) -> int:
        """
        添加图片

        Args:
            chapter_id: 章节ID
            page_num: 页码
            url: 图片URL
            file_path: 本地文件路径

        Returns:
            图片ID
        """
        cur = self.conn.cursor()
        try:
            cur.execute("""
                INSERT INTO images (chapter_id, page_num, url, file_path)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (chapter_id, page_num) DO UPDATE SET
                    url = EXCLUDED.url,
                    file_path = EXCLUDED.file_path
                RETURNING id
            """, (chapter_id, page_num, url, file_path))
            self.conn.commit()
            return cur.fetchone()[0]
        except Exception as e:
            self.conn.rollback()
            logger.error(f"添加图片记录失败: {e}")
            raise

    def mark_chapter_downloaded(self, chapter_id: int):
        """
        标记章节为已下载

        Args:
            chapter_id: 章节ID
        """
        cur = self.conn.cursor()
        try:
            cur.execute("""
                UPDATE chapters SET downloaded = TRUE WHERE id = %s
            """, (chapter_id,))
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            logger.error(f"标记章节下载状态失败: {e}")

    def mark_image_downloaded(self, image_id: int, file_path: str):
        """
        标记图片为已下载

        Args:
            image_id: 图片ID
            file_path: 文件路径
        """
        cur = self.conn.cursor()
        try:
            cur.execute("""
                UPDATE images SET downloaded = TRUE, file_path = %s WHERE id = %s
            """, (file_path, image_id))
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            logger.error(f"标记图片下载状态失败: {e}")

    def add_fetch_history(self, comic_id: int = None, chapter_id: int = None,
                          fetch_type: str = "comic", status: str = "success",
                          error_msg: str = None, metadata: Dict = None):
        """
        添加抓取历史记录

        Args:
            comic_id: 漫画ID
            chapter_id: 章节ID
            fetch_type: 抓取类型 (comic, chapter, image)
            status: 状态
            error_msg: 错误信息
            metadata: 额外元数据
        """
        import json
        cur = self.conn.cursor()
        try:
            metadata_json = json.dumps(metadata) if metadata else None
            cur.execute("""
                INSERT INTO fetch_history (comic_id, chapter_id, fetch_type, status, error_msg, metadata)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (comic_id, chapter_id, fetch_type, status, error_msg, metadata_json))
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            logger.error(f"添加抓取历史失败: {e}")

    def get_comic(self, comic_id: int = None, name: str = None) -> Optional[Dict]:
        """
        获取漫画信息

        Args:
            comic_id: 漫画ID
            name: 漫画名称

        Returns:
            漫画信息字典
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)
        if comic_id:
            cur.execute("SELECT * FROM comics WHERE id = %s", (comic_id,))
        elif name:
            cur.execute("SELECT * FROM comics WHERE name LIKE %s", (f"%{name}%",))
        else:
            return None
        return cur.fetchone()

    def list_comics(self) -> List[Dict]:
        """
        列出所有漫画

        Returns:
            漫画列表
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM comics ORDER BY created_at DESC")
        return cur.fetchall()

    def get_chapters(self, comic_id: int) -> List[Dict]:
        """
        获取漫画的所有章节

        Args:
            comic_id: 漫画ID

        Returns:
            章节列表
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "SELECT * FROM chapters WHERE comic_id = %s ORDER BY chapter_num",
            (comic_id,)
        )
        return cur.fetchall()

    def get_undownloaded_chapters(self, comic_id: int) -> List[Dict]:
        """
        获取未下载的章节

        Args:
            comic_id: 漫画ID

        Returns:
            未下载的章节列表
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "SELECT * FROM chapters WHERE comic_id = %s AND downloaded = FALSE ORDER BY chapter_num",
            (comic_id,)
        )
        return cur.fetchall()

    def get_chapter_images(self, chapter_id: int) -> List[Dict]:
        """
        获取章节的所有图片

        Args:
            chapter_id: 章节ID

        Returns:
            图片列表
        """
        cur = self.conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "SELECT * FROM images WHERE chapter_id = %s ORDER BY page_num",
            (chapter_id,)
        )
        return cur.fetchall()

    def get_fetched_chapters(self, comic_id: int) -> List[str]:
        """
        获取已抓取的章节号列表

        Args:
            comic_id: 漫画ID

        Returns:
            章节号列表
        """
        cur = self.conn.cursor()
        cur.execute(
            "SELECT chapter_num FROM chapters WHERE comic_id = %s",
            (comic_id,)
        )
        return [row[0] for row in cur.fetchall()]

    def get_comic_stats(self, comic_id: int) -> Dict:
        """
        获取漫画统计信息

        Args:
            comic_id: 漫画ID

        Returns:
            统计信息字典
        """
        cur = self.conn.cursor()
        cur.execute("""
            SELECT
                COUNT(DISTINCT c.id) as total_chapters,
                COUNT(DISTINCT CASE WHEN c.downloaded = TRUE THEN c.id END) as downloaded_chapters,
                COUNT(DISTINCT i.id) as total_images,
                COUNT(DISTINCT CASE WHEN i.downloaded = TRUE THEN i.id END) as downloaded_images
            FROM chapters c
            LEFT JOIN images i ON i.chapter_id = c.id
            WHERE c.comic_id = %s
        """, (comic_id,))

        result = cur.fetchone()
        return {
            'total_chapters': result[0],
            'downloaded_chapters': result[1],
            'total_images': result[2],
            'downloaded_images': result[3]
        }


def get_database(config_path: str = "config.yaml") -> Database:
    """
    获取数据库实例

    Args:
        config_path: 配置文件路径

    Returns:
        Database 实例
    """
    return Database(config_path)


if __name__ == "__main__":
    # 测试数据库
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    db = get_database()
    print("数据库初始化成功")

    # 列出所有漫画
    comics = db.list_comics()
    print(f"\n当前数据库中有 {len(comics)} 部漫画")

    db.close()
