"""
漫画抓取模块 V7 - 修复图片分页问题
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from bs4 import BeautifulSoup
import re
import logging
from pathlib import Path
from urllib.parse import urljoin, urlparse
import time
import json
import random
import os
from typing import List, Dict, Optional

try:
    from proxy_pool_client import ProxyPoolClient
    PROXY_POOL_AVAILABLE = True
except ImportError:
    PROXY_POOL_AVAILABLE = False

logger = logging.getLogger(__name__)


class ManhuaGuiFetcherSelenium:
    """漫画龟抓取器 V7 (支持分页)"""

    def __init__(self, 
                 base_url: str = "https://m.manhuagui.com",
                 use_proxy: bool = False,
                 proxy_pool_url: str = "http://localhost:5010",
                 headless: bool = True):
        """
        初始化抓取器
        
        Args:
            base_url: 基础 URL
            use_proxy: 是否使用代理
            proxy_pool_url: 代理池 API 地址
            headless: 是否使用无头模式
        """
        self.base_url = base_url
        self.use_proxy = use_proxy
        self.headless = headless
        
        # 浏览器请求头
        self.default_headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'Referer': base_url
        }
        
        # 初始化代理池客户端
        self.proxy_pool_client = None
        self.current_proxy = None
        
        if use_proxy and PROXY_POOL_AVAILABLE:
            try:
                self.proxy_pool_client = ProxyPoolClient(api_url=proxy_pool_url)
                logger.info(f"代理池客户端已初始化: {proxy_pool_url}")
                proxy_data = self.proxy_pool_client.get_proxy()
                if proxy_data:
                    self.current_proxy = proxy_data.get('proxy')
                    logger.info(f"已获取代理: {self.current_proxy}")
            except Exception as e:
                logger.warning(f"代理池客户端初始化失败: {e}")
                self.use_proxy = False
        
        # 初始化 WebDriver
        self.driver = None
        self._init_driver()
        
        # Cookie 管理状态
        self.cookies_loaded = False
        
        logger.info(f"抓取器已初始化 (代理: {'已启用' if self.use_proxy else '未启用'}, 无头模式: {'是' if self.headless else '否'})")

    def _init_driver(self):
        """初始化 Chrome WebDriver"""
        try:
            # 配置 Chrome 选项
            chrome_options = Options()
            
            # 无头模式
            if self.headless:
                chrome_options.add_argument('--headless')
            
            # 性能优化
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-software-rasterizer')
            
            # 禁用自动化检测
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # 窗口大小
            chrome_options.add_argument('--window-size=1920,1080')
            
            logger.info("Chrome 选项配置完成")
            
            # 初始化 WebDriver
            service = Service()
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            logger.info("WebDriver 初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"WebDriver 初始化失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _request(self, url: str, wait_time: int = 5, use_proxy: Optional[bool] = None):
        """
        访问 URL 并返回 driver
        
        Args:
            url: 请求 URL
            wait_time: 等待时间
            use_proxy: 是否使用代理（None = 使用配置）
        """
        # 确定是否使用代理
        should_use_proxy = use_proxy if use_proxy is not None else self.use_proxy
        
        # 如果使用代理但当前没有代理，尝试获取
        if should_use_proxy and self.proxy_pool_client and not self.current_proxy:
            logger.info("尝试获取新代理...")
            proxy_data = self.proxy_pool_client.get_proxy()
            if proxy_data:
                self.current_proxy = proxy_data.get('proxy')
                logger.info(f"已获取新代理: {self.current_proxy}")
        
        try:
            # 设置代理（如果需要）
            if should_use_proxy and self.current_proxy:
                # 注意：在 Selenium 中通过 Chrome 设置代理
                # 这里简化处理，暂时不使用 Selenium 代理
                pass
            
            logger.debug(f"请求 URL: {url} (代理: {'是' if should_use_proxy else '否'})")
            
            # 访问 URL
            self.driver.get(url)
            time.sleep(wait_time)
            
            return self.driver
        except Exception as e:
            logger.error(f"请求失败: {url}, 错误: {e}")
            return None

    def search_comics(self, keyword: str, use_proxy: Optional[bool] = None) -> List[Dict]:
        """搜索漫画"""
        logger.info(f"搜索漫画: {keyword}")
        
        # 构建搜索 URL
        search_url = urljoin(self.base_url, f"/s/{keyword}")
        
        # 请求
        driver = self._request(search_url, use_proxy=use_proxy)
        if not driver:
            return []
        
        # 解析页面
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        comics = []
        
        # 查找漫画列表
        comic_links = soup.select('a[href*="/comic/"]')
        seen_ids = set()
        
        for link in comic_links:
            href = link.get('href')
            title = link.get('title') or link.text.strip()
            
            # 提取漫画ID
            match = re.search(r'/comic/(\d+)/', href)
            if match:
                comic_id = match.group(1)
                
                # 去重
                if comic_id not in seen_ids:
                    seen_ids.add(comic_id)
                    comics.append({
                        'id': comic_id,
                        'name': title,
                        'url': urljoin(self.base_url, href)
                    })
        
        logger.info(f"搜索到 {len(comics)} 部漫画")
        return comics

    def get_comic_info(self, comic_url: str, use_proxy: Optional[bool] = None) -> Optional[Dict]:
        """获取漫画信息"""
        logger.info(f"获取漫画信息: {comic_url}")
        
        # 请求
        driver = self._request(comic_url, use_proxy=use_proxy)
        if not driver:
            return None
        
        # 解析页面
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
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

    def get_chapters(self, comic_url: str, use_proxy: Optional[bool] = None) -> List[Dict]:
        """获取章节列表"""
        logger.info(f"获取章节列表: {comic_url}")
        
        # 请求
        driver = self._request(comic_url, use_proxy=use_proxy)
        if not driver:
            return []
        
        # 解析页面
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        chapters = []
        
        # 查找章节链接
        chapter_links = soup.select('a[href*="/comic/"]')
        seen_chapters = set()
        
        for link in chapter_links:
            href = link.get('href')
            match = re.search(r'/(\d+)\.html?$', href)
            if match:
                # 从URL提取章节标识
                url_id = match.group(1)

                # 从标题中提取真正的章节号
                title = link.text.strip()
                chapter_num_match = re.search(r'第(\d+)[话章节]', title)

                if chapter_num_match:
                    chapter_num = chapter_num_match.group(1)
                else:
                    # 如果无法从标题提取，使用URL中的ID
                    chapter_num = url_id

                # 去重
                if chapter_num not in seen_chapters:
                    seen_chapters.add(chapter_num)
                    chapters.append({
                        'chapter_num': chapter_num,
                        'title': title,
                        'url': urljoin(self.base_url, href)
                    })
        
        logger.info(f"获取到 {len(chapters)} 个章节")
        return chapters

    def get_images(self, chapter_url: str, use_proxy: Optional[bool] = None) -> List[str]:
        """获取章节图片列表（支持分页）"""
        logger.info(f"获取章节图片: {chapter_url}")

        # 请求
        driver = self._request(chapter_url, use_proxy=use_proxy, wait_time=5)
        if not driver:
            return []

        images = []
        
        try:
            # 方法：等待 JavaScript 解码后，通过点击"下一页"获取所有图片
            logger.info("等待页面加载并收集图片...")
            time.sleep(3)

            for page_num in range(1, 30):  # 最多翻页 30 次
                # 获取当前页面的图片
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                for img in soup.find_all('img'):
                    src = img.get('src') or img.get('data-src') or img.get('data-original')
                    if src and ('jpg' in src or 'png' in src or 'jpeg' in src or 'webp' in src):
                        if not any(x in src.lower() for x in ['logo', 'icon', 'banner', 'ad', 'avatar', 'logo_mini']):
                            if src not in images:
                                images.append(src)

                logger.info(f"第 {page_num} 页: 已收集 {len(images)} 张图片")

                # 检查是否有"下一页"按钮
                try:
                    next_button = driver.find_element(By.CSS_SELECTOR, '[data-action="next"]')
                    next_button.click()
                    time.sleep(2)  # 等待下一页加载
                except Exception:
                    logger.info(f"没有更多页面了，共获取 {len(images)} 张图片")
                    break

        except Exception as e:
            logger.error(f"获取图片失败: {e}")
            import traceback
            traceback.print_exc()

        logger.info(f"最终获取到 {len(images)} 张图片")
        return images

    def close(self):
        """关闭 WebDriver"""
        if self.driver:
            logger.info("关闭 WebDriver...")
            self.driver.quit()
            self.driver = None


def create_fetcher_selenium(use_proxy: bool = False, 
                         proxy_pool_url: str = "http://localhost:5010",
                         headless: bool = True):
    """
    创建漫画抓取器实例 V7
    
    Args:
        use_proxy: 是否使用代理
        proxy_pool_url: 代理池 API 地址
        headless: 是否使用无头模式
        
    Returns:
        ManhuaGuiFetcherSelenium 实例
    """
    return ManhuaGuiFetcherSelenium(
        use_proxy=use_proxy,
        proxy_pool_url=proxy_pool_url,
        headless=headless
    )


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    print("="*80)
    print("Fetcher V7 - 分页支持")
    print("="*80)
    print()
    print("✅ 修复内容:")
    print("   - 支持翻页获取所有图片")
    print("   - 自动点击'下一页'按钮")
    print("   - 收集所有页面的图片URL")
    print()
    print("="*80)

    # 测试
    try:
        fetcher = create_fetcher_selenium(use_proxy=False, headless=True)
        print("✅ 抓取器创建成功")
        print()
        
        # 测试图片抓取
        print("测试图片抓取...")
        test_url = "https://m.manhuagui.com/comic/1128/862270.html"
        images = fetcher.get_images(test_url)
        
        print(f"✅ 抓取成功: {len(images)} 张图片")
        for i, img in enumerate(images[:10], 1):
            print(f"  {i}. {img[:80]}...")
        
        if len(images) > 10:
            print(f"  ... 还有 {len(images) - 10} 张")
        
        # 关闭
        fetcher.close()
        print("✅ 抓取器已关闭")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
