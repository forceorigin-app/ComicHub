"""
漫画抓取模块 V2
增强版：更好的错误处理、重试机制和日志
"""

import requests
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Optional
import logging
from pathlib import Path
from urllib.parse import urljoin
import time
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

logger = logging.getLogger(__name__)


class RetryAdapter(HTTPAdapter):
    """自定义重试适配器"""
    
    def __init__(self, max_retries=5, backoff_factor=1):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[500, 502, 503, 504, 520, 521, 522, 523, 524],
            allowed_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "TRACE"]
        )
        super().__init__(max_retries=retry_strategy)


class ManhuaGuiFetcherV2:
    """漫画龟抓取器 V2"""

    def __init__(self, base_url: str = "https://m.manhuagui.com"):
        self.base_url = base_url
        
        # 创建 session
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
        
        # 添加重试适配器
        retry_adapter = RetryAdapter(max_retries=5, backoff_factor=2)
        self.session.mount('http://', retry_adapter)
        self.session.mount('https://', retry_adapter)

    def _request(self, url: str, timeout: int = 30) -> Optional[requests.Response]:
        """
        发送 HTTP 请求，带有重试机制
        """
        for attempt in range(3):
            try:
                logger.debug(f"请求 URL: {url} (尝试 {attempt + 1}/3)")
                response = self.session.get(url, timeout=timeout, verify=False)
                response.encoding = 'utf-8'
                return response
            except requests.exceptions.SSLError as e:
                logger.warning(f"SSL 错误 (尝试 {attempt + 1}/3): {e}")
                if attempt < 2:
                    time.sleep(3 * (attempt + 1))
                    continue
                raise
            except requests.exceptions.RequestException as e:
                logger.warning(f"请求错误 (尝试 {attempt + 1}/3): {e}")
                if attempt < 2:
                    time.sleep(2 * (attempt + 1))
                    continue
                raise
        return None

    def search_comics(self, keyword: str) -> List[Dict]:
        """搜索漫画"""
        search_urls = [
            urljoin(self.base_url, f"/s/{keyword}"),
            urljoin(self.base_url, f"/search/?title={keyword}"),
        ]
        
        for search_url in search_urls:
            response = self._request(search_url)
            if response is None:
                continue
            
            soup = BeautifulSoup(response.text, 'html.parser')
            comics = []
            
            # 查找漫画列表
            for link in soup.select('a[href*="/comic/"]'):
                href = link.get('href')
                title = link.get('title') or link.text.strip()
                
                # 提取漫画ID
                match = re.search(r'/comic/(\d+)/', href)
                if match:
                    comic_id = match.group(1)
                    comics.append({
                        'id': comic_id,
                        'name': title,
                        'url': urljoin(self.base_url, href)
                    })
            
            if comics:
                logger.info(f"搜索到 {len(comics)} 部漫画")
                return comics
        
        return []

    def get_comic_info(self, comic_url: str) -> Optional[Dict]:
        """获取漫画信息"""
        response = self._request(comic_url)
        if response is None:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 查找标题
        title = soup.select_one('h1')
        comic_name = title.text.strip() if title else "未知"
        
        # 提取ID
        match = re.search(r'/comic/(\d+)/', comic_url)
        comic_id = match.group(1) if match else None
        
        return {
            'id': comic_id,
            'name': comic_name,
            'url': comic_url
        }

    def get_chapters(self, comic_url: str) -> List[Dict]:
        """获取章节列表"""
        response = self._request(comic_url)
        if response is None:
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        chapters = []
        
        # 查找章节链接
        for link in soup.select('a[href*="/comic/"]'):
            href = link.get('href')
            match = re.search(r'/(\d+)\.html?$', href)
            if match:
                chapter_num = match.group(1)
                chapters.append({
                    'chapter_num': chapter_num,
                    'title': link.text.strip(),
                    'url': urljoin(self.base_url, href)
                })
        
        logger.info(f"获取到 {len(chapters)} 个章节")
        return chapters

    def get_images(self, chapter_url: str) -> List[str]:
        """获取章节图片列表"""
        response = self._request(chapter_url)
        if response is None:
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        images = []
        
        # 查找所有图片
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src') or img.get('data-original')
            if src and ('jpg' in src or 'png' in src or 'jpeg' in src or 'webp' in src):
                images.append(src)
        
        # 去重
        images = list(set(images))
        logger.info(f"获取到 {len(images)} 张图片")
        return images

    def download_image(self, url: str, save_path: str) -> bool:
        """下载图片"""
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
