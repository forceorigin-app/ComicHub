"""
Selenium 漫画抓取器 V8 - 修复版
修复代理逻辑，确保直连模式不被代理池干扰
"""
import time
import re
import logging
import asyncio
from typing import Optional, List, Dict
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.service import Service
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

try:
    from proxy_pool_client import ProxyPoolClient
except ImportError:
    ProxyPoolClient = None

# 设置日志
logger = logging.getLogger(__name__)


class ManhuaGuiFetcherSeleniumV8:
    """漫画柜 Selenium 抓取器 V8"""

    def __init__(self, use_proxy: bool = False,
                 proxy_pool_url: str = "http://localhost:5010",
                 headless: bool = True):
        """
        初始化抓取器

        Args:
            use_proxy: 是否使用代理池
            proxy_pool_url: 代理池服务地址
            headless: 是否使用无头模式
        """
        self.base_url = "https://m.manhuagui.com"
        self.use_proxy = use_proxy
        self.proxy_pool_url = proxy_pool_url
        self.headless = headless
        
        # 代理池客户端（只在需要时初始化）
        self.proxy_pool_client = None
        self.current_proxy = None
        
        # Cookie 管理状态
        self.cookies_loaded = False
        
        # WebDriver
        self.driver = None
        
        # 初始化
        self._init_driver()
    
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
            
            # 完全禁用代理（避免任何代理配置干扰）
            chrome_options.add_argument('--proxy-server="')
            chrome_options.add_experimental_option('proxy', {})
            
            # 代理配置（仅在真正使用代理时添加）
            # 注意：Selenium 代理配置需要在 Chrome 级别设置
            # 这里我们暂时不设置代理，避免超时问题
            
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
    
    def _request(self, url: str, wait_time: int = 5):
        """
        访问 URL 并返回 driver
        
        Args:
            url: 请求 URL
            wait_time: 等待时间
        
        修复：完全禁用代理逻辑，确保直连模式
        """
        # 无论配置如何，直接访问，不走代理
        logger.info(f"请求 URL: {url}")
        
        try:
            self.driver.get(url)
            time.sleep(wait_time)
            return self.driver
        except Exception as e:
            logger.error(f"请求失败: {url}, 错误: {e}")
            return None
    
    def search_comics(self, keyword: str) -> List[Dict]:
        """搜索漫画"""
        logger.info(f"搜索漫画: {keyword}")
        
        # 构建搜索 URL
        search_url = urljoin(self.base_url, f"/s/{keyword}")
        
        # 请求
        driver = self._request(search_url)
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
            
            # 提取漫画 ID
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
    
    def get_comic_info(self, comic_url: str) -> Optional[Dict]:
        """获取漫画信息"""
        logger.info(f"获取漫画信息: {comic_url}")
        
        # 请求
        driver = self._request(comic_url)
        if not driver:
            return None
        
        # 解析页面
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # 查找标题
        title = soup.select_one('h1')
        comic_name = title.text.strip() if title else "未知"
        
        # 提取 ID
        match = re.search(r'/comic/(\d+)/', comic_url)
        comic_id = match.group(1) if match else None
        
        return {
            'id': comic_id,
            'name': comic_name,
            'url': comic_url
        }
    
    def get_chapters(self, comic_url: str) -> List[Dict]:
        """获取章节列表"""
        logger.info(f"获取章节列表: {comic_url}")
        
        # 请求
        driver = self._request(comic_url)
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
                # 从 URL 提取章节标识
                url_id = match.group(1)

                # 从标题中提取真正的章节号
                title = link.text.strip()
                chapter_num_match = re.search(r'第(\d+)[话章节]', title)

                if chapter_num_match:
                    chapter_num = chapter_num_match.group(1)
                else:
                    # 如果无法从标题提取，使用 URL 中的 ID
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
    
    def get_images(self, chapter_url: str) -> List[str]:
        """获取章节图片列表（支持翻页）"""
        logger.info(f"获取章节图片: {chapter_url}")

        # 请求
        driver = self._request(chapter_url, wait_time=5)
        if not driver:
            return []

        all_images = []
        page_num = 0
        max_pages = 30

        from selenium.webdriver.common.by import By

        try:
            while page_num < max_pages:
                # 处理可能的 alert
                try:
                    alert = self.driver.switch_to.alert
                    logger.info(f"检测到 alert: {alert.text}")
                    alert.accept()
                    time.sleep(1)
                    break
                except:
                    pass  # 没有 alert

                # 获取当前页面的图片
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                for img in soup.find_all('img'):
                    src = img.get('src') or img.get('data-src') or img.get('data-original')
                    if src and ('jpg' in src or 'png' in src or 'jpeg' in src or 'webp' in src):
                        # 过滤掉无关图片
                        if not any(x in src.lower() for x in ['logo', 'icon', 'banner', 'ad', 'avatar']):
                            if src not in all_images:
                                all_images.append(src)

                logger.info(f"第 {page_num + 1} 页: 已收集 {len(all_images)} 张图片")

                # 检查页面指示
                try:
                    page_indicator = driver.find_element(By.CSS_SELECTOR, '#pageNo')
                    page_text = page_indicator.text
                    logger.info(f"页面指示: {page_text}")

                    # 解析 "1/13P" 格式
                    match = page_text.split('/')
                    if match:
                        current = match[0].strip()
                        total = match[1].rstrip('P').strip()
                        if current == total:
                            logger.info(f"已到最后一页: {page_text}")
                            break
                except:
                    pass  # 没有找到页面指示器

                # 尝试点击"下一页"按钮
                try:
                    # 使用 XPath 查找包含"下一页"文本的链接
                    next_links = driver.find_elements(By.XPATH, "//a[contains(text(), '下一页') or contains(@data-action, 'next')]")

                    if not next_links:
                        logger.info("没有找到下一页按钮")
                        break

                    # 点击第一个"下一页"链接
                    next_link = next_links[0]
                    next_link.click()
                    time.sleep(2.5)  # 等待下一页加载
                    page_num += 1

                except Exception as e:
                    logger.info(f"点击下一页失败: {e}")
                    break

            logger.info(f"最终获取到 {len(all_images)} 张图片")
            return all_images

        except Exception as e:
            logger.error(f"获取图片失败: {e}")
            import traceback
            traceback.print_exc()
            return all_images

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
    创建漫画抓取器实例 V8 (Selenium 版本)

    Args:
        use_proxy: 是否使用代理
        proxy_pool_url: 代理池服务地址
        headless: 是否使用无头模式
    """
    return ManhuaGuiFetcherSeleniumV8(
        use_proxy=use_proxy,
        proxy_pool_url=proxy_pool_url,
        headless=headless
    )
