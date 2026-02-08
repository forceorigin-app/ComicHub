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
import time

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
        
        # 创建 session 并设置更好的 headers
        self.session = requests.Session()
        
        # 模拟真实浏览器的 headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Referer': self.base_url
        })
        
        # 设置重试策略
        retry_strategy = requests.adapters.HTTPAdapter(
            max_retries=3,
            pool_connections=10,
            pool_maxsize=10
        )
        self.session.mount('http://', retry_strategy)
        self.session.mount('https://', retry_strategy)

    def _request(self, url: str, timeout: int = 30, retries: int = 3) -> Optional[requests.Response]:
        """
        发送 HTTP 请求，带有重试机制

        Args:
            url: 请求URL
            timeout: 超时时间（秒）
            retries: 重试次数

        Returns:
            Response 对象，失败返回 None
        """
        for attempt in range(retries):
            try:
                logger.debug(f"请求 URL: {url} (尝试 {attempt + 1}/{retries})")
                # 禁用 SSL 验证（仅用于测试）
                response = self.session.get(url, timeout=timeout, verify=False)
                response.encoding = 'utf-8'
                return response
            except requests.exceptions.RequestException as e:
                logger.warning(f"请求失败 (尝试 {attempt + 1}/{retries}): {e}")
                if attempt < retries - 1:
                    time.sleep(2 * (attempt + 1))
                    continue
                raise
        return None

    def search_comics(self, keyword: str) -> List[Dict]:
        """
        搜索漫画

        Args:
            keyword: 搜索关键词

        Returns:
            漫画列表
        """
        try:
            # 尝试多个搜索 URL 格式
            search_urls = [
                urljoin(self.base_url, f"/s/{keyword}"),
                urljoin(self.base_url, f"/search/?title={keyword}"),
                f"{self.base_url}/s_all/{keyword}/"
            ]
            
            for search_url in search_urls:
                logger.info(f"尝试搜索 URL: {search_url}")
                response = self._request(search_url)
                
                if response is None:
                    continue
                    
                soup = BeautifulSoup(response.text, 'html.parser')
                comics = []
                
                # 尝试不同的选择器
                selectors = [
                    '.book-result',
                    '.book-list li',
                    '.result-list li',
                    '.search-result .item'
                ]
                
                comic_items = []
                for selector in selectors:
                    comic_items = soup.select(selector)
                    if comic_items:
                        break
                
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
                
                if comics:
                    logger.info(f"搜索到 {len(comics)} 部漫画")
                    return comics
            
            logger.warning(f"所有搜索 URL 都失败了")
            return []
            
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
            response = self._request(comic_url)
            if response is None:
                return None
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 漫画名称
            title_selectors = ['h1', '.book-title', '.detail-title']
            title = None
            for selector in title_selectors:
                title = soup.select_one(selector)
                if title:
                    break
            comic_name = title.text.strip() if title else "未知"
            
            # 描述
            desc = soup.select_one('.detail-list p') or soup.select_one('.intro') or soup.select_one('.description')
            description = desc.text.strip() if desc else ""
            
            # 封面
            cover = soup.select_one('.book-cover img') or soup.select_one('.cover img')
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
            response = self._request(comic_url)
            if response is None:
                return []
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            chapters = []
            
            # 尝试不同的章节选择器
            chapter_selectors = [
                '.chapter-list a',
                '.chapter-item a',
                '#chapterlist a',
                '.list-chapter a'
            ]
            
            chapter_items = []
            for selector in chapter_selectors:
                chapter_items = soup.select(selector)
                if chapter_items:
                    break
            
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
            response = self._request(chapter_url)
            if response is None:
                return []
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找图片
            images = []
            
            # 方法1: 查找所有 img 标签
            img_tags = soup.find_all('img')
            for img in img_tags:
                src = img.get('src') or img.get('data-src') or img.get('data-original')
                if src and ('jpg' in src or 'png' in src or 'jpeg' in src or 'webp' in src):
                    # 过滤掉封面、头像、图标
                    url_lower = src.lower()
                    if not any(x in url_lower for x in ['cover', 'avatar', 'icon', 'logo', 'header', 'footer', 'banner']):
                        # 使用完整URL
                        if not src.startswith('http'):
                            src = urljoin(self.base_url, src)
                        images.append(src)
            
            # 方法2: 查找图片容器
            if not images:
                container_selectors = ['#cp_image', '#images', '.comic-page', '.comic-image']
                container = None
                for selector in container_selectors:
                    container = soup.select_one(selector)
                    if container:
                        break
                
                if container:
                    img_tags = container.find_all('img')
                    for img in img_tags:
                        src = img.get('src') or img.get('data-src') or img.get('data-original')
                        if src:
                            if not src.startswith('http'):
                                src = urljoin(self.base_url, src)
                            images.append(src)
            
            # 去重
            images = list(set(images))
            logger.info(f"获取到 {len(images)} 张图片")
            return images
            
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
            response = self.session.get(url, timeout=30, verify=False)
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(save_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"下载图片成功: {save_path}")
            return True
            
        except Exception as e:
            logger.error(f"下载图片失败: {url}, 错误: {e}")
            return False
