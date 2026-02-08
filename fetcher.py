"""
漫画抓取模块
负责从漫画龟抓取漫画信息、章节和图片
"""

import requests
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Optional
import logging
from pathlib import Path
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class ManhuaGuiFetcher:
    """漫画龟抓取器"""

    def __init__(self, base_url: str = "https://m.manhuagui.com"):
        """
        初始化抓取器

        Args:
            base_url: 基础URL
        """
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.2 Mobile/15E148 Safari/604.1'
        })

    def search_comics(self, keyword: str) -> List[Dict]:
        """
        搜索漫画

        Args:
            keyword: 搜索关键词

        Returns:
            漫画列表
        """
        try:
            url = urljoin(self.base_url, f"/s/{keyword}")
            response = self.session.get(url, timeout=30)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            comics = []
            comic_items = soup.select('.book-result') or soup.select('.book-list li')
            
            for item in comic_items:
                try:
                    link = item.select_one('a')
                    if not link:
                        continue
                    
                    title = link.get('title') or link.text.strip()
                    comic_url = urljoin(self.base_url, link['href'])
                    cover = item.select_one('img')
                    cover_url = cover['src'] if cover else None
                    
                    # 提取漫画ID
                    match = re.search(r'/comic/(\d+)/', comic_url)
                    comic_id = match.group(1) if match else None
                    
                    if comic_id:
                        comics.append({
                            'id': comic_id,
                            'name': title,
                            'url': comic_url,
                            'cover_image': cover_url
                        })
                except Exception as e:
                    logger.error(f"解析搜索结果失败: {e}")
                    continue
            
            logger.info(f"搜索到 {len(comics)} 部漫画")
            return comics
            
        except Exception as e:
            logger.error(f"搜索漫画失败: {e}")
            return []

    def get_comic_info(self, comic_url: str) -> Optional[Dict]:
        """
        获取漫画信息

        Args:
            comic_url: 漫画URL

        Returns:
            漫画信息字典
        """
        try:
            response = self.session.get(comic_url, timeout=30)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 漫画名称
            title = soup.select_one('h1')
            comic_name = title.text.strip() if title else "未知"
            
            # 描述
            desc = soup.select_one('.detail-list p') or soup.select_one('.intro')
            description = desc.text.strip() if desc else ""
            
            # 封面
            cover = soup.select_one('.book-cover img')
            cover_image = cover['src'] if cover else None
            
            # 漫画ID
            match = re.search(r'/comic/(\d+)/', comic_url)
            comic_id = match.group(1) if match else None
            
            return {
                'id': comic_id,
                'name': comic_name,
                'url': comic_url,
                'description': description,
                'cover_image': cover_image
            }
            
        except Exception as e:
            logger.error(f"获取漫画信息失败: {e}")
            return None

    def get_chapters(self, comic_url: str) -> List[Dict]:
        """
        获取漫画章节列表

        Args:
            comic_url: 漫画URL

        Returns:
            章节列表
        """
        try:
            response = self.session.get(comic_url, timeout=30)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            chapters = []
            chapter_items = soup.select('.chapter-list a') or soup.select('.chapter-item a')
            
            # 反向遍历，保持章节顺序
            for item in reversed(chapter_items):
                try:
                    title = item.text.strip()
                    chapter_url = urljoin(self.base_url, item['href'])
                    
                    # 提取章节号
                    match = re.search(r'/(\d+)(?:\.html)?$', chapter_url)
                    chapter_num = match.group(1) if match else "0"
                    
                    chapters.append({
                        'chapter_num': chapter_num,
                        'title': title,
                        'url': chapter_url
                    })
                except Exception as e:
                    logger.error(f"解析章节失败: {e}")
                    continue
            
            logger.info(f"获取到 {len(chapters)} 个章节")
            return chapters
            
        except Exception as e:
            logger.error(f"获取章节列表失败: {e}")
            return []

    def get_images(self, chapter_url: str) -> List[str]:
        """
        获取章节图片URL列表

        Args:
            chapter_url: 章节URL

        Returns:
            图片URL列表
        """
        try:
            response = self.session.get(chapter_url, timeout=30)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找图片
            images = []
            
            # 方法1: 查找 img 标签
            img_tags = soup.select('img')
            for img in img_tags:
                src = img.get('src') or img.get('data-src')
                if src and ('jpg' in src or 'png' in src or 'jpeg' in src):
                    # 过滤掉封面和头像
                    if 'cover' not in src.lower() and 'avatar' not in src.lower():
                        # 使用完整URL
                        if not src.startswith('http'):
                            src = urljoin(self.base_url, src)
                        images.append(src)
            
            # 方法2: 查找图片容器
            if not images:
                container = soup.select_one('#cp_image') or soup.select_one('.comic-page')
                if container:
                    img_tags = container.select('img')
                    for img in img_tags:
                        src = img.get('src') or img.get('data-src')
                        if src:
                            if not src.startswith('http'):
                                src = urljoin(self.base_url, src)
                            images.append(src)
            
            logger.info(f"获取到 {len(images)} 张图片")
            return list(set(images))  # 去重
            
        except Exception as e:
            logger.error(f"获取图片列表失败: {e}")
            return []

    def download_image(self, url: str, save_path: str) -> bool:
        """
        下载图片

        Args:
            url: 图片URL
            save_path: 保存路径

        Returns:
            是否下载成功
        """
        try:
            response = self.session.get(url, timeout=30)
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(save_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"下载图片成功: {save_path}")
            return True
            
        except Exception as e:
            logger.error(f"下载图片失败: {url}, 错误: {e}")
            return False
