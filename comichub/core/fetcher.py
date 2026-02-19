"""
Selenium 漫画抓取器 - 最终修复版（指定 chromedriver 路径）
直接指定本机 chromedriver，完全绕过 Chrome Manager
"""
import time
import re
import logging
import traceback
import subprocess
import os
from typing import List, Dict, Optional
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

# 设置日志
logger = logging.getLogger(__name__)


class ManhuaGuiFetcherSelenium:
    """漫画柜 Selenium 抓取器（最终修复版：指定 chromedriver 路径）"""

    def __init__(self, headless: bool = True):
        """
        初始化抓取器

        Args:
            headless: 是否使用无头模式
        """
        self.base_url = "https://m.manhuagui.com"
        self.headless = headless
        
        # 查找本机 chromedriver
        self.chromedriver_path = self._find_chromedriver()
        
        # WebDriver
        self.driver = None
        
        # 初始化
        self._init_driver()
        
        logger.info(f"抓取器已初始化 (无头模式: {'是' if self.headless else '否'}, chromedriver: {self.chromedriver_path})")

    def _find_chromedriver(self):
        """查找本机 chromedriver 路径"""
        # 常见路径
        possible_paths = [
            '/usr/local/bin/chromedriver',
            '/usr/bin/chromedriver',
            '/opt/homebrew/bin/chromedriver',
            '/Applications/Google Chrome.app/Contents/MacOS/chromedriver',
            os.path.expanduser('~/bin/chromedriver'),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        # 使用 which 查找
        try:
            result = subprocess.run(['which', 'chromedriver'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        
        # 如果都找不到，返回默认路径
        logger.warning("未找到 chromedriver，使用默认路径")
        return '/usr/local/bin/chromedriver'

    def _init_driver(self):
        """初始化 Chrome WebDriver（指定 chromedriver 路径）"""
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
            
            # 禁用证书验证
            chrome_options.add_argument('--ignore-certificate-errors')
            chrome_options.add_argument('--ignore-ssl-errors')
            
            logger.info("Chrome 选项配置完成")
            
            # 使用本机 chromedriver，完全绕过 Selenium Chrome Manager
            service = ChromeService(executable_path=self.chromedriver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # 设置超时
            self.driver.set_page_load_timeout(60)
            self.driver.set_script_timeout(30)
            
            logger.info(f"WebDriver 初始化成功（使用本机 chromedriver: {self.chromedriver_path})")
            return True
            
        except Exception as e:
            logger.error(f"WebDriver 初始化失败: {e}")
            traceback.print_exc()
            return False

    def _request(self, url: str, wait_time: int = 5):
        """
        访问 URL 并返回 Driver

        Args:
            url: 请求 URL
            wait_time: 等待时间
        """
        logger.info(f"请求 URL: {url}")
        
        try:
            # 直接访问
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

    def get_images(self, chapter_url: str) -> Dict[str, any]:
        """
        获取章节图片列表（支持翻页）

        Args:
            chapter_url: 章节URL

        Returns:
            {
                'images': List[Dict],  # 图片信息列表，每项包含 {'url': str, 'page': int}
                'total_count': int,    # 总图片数
            }
        """
        logger.info(f"获取章节图片: {chapter_url}")

        # 请求
        driver = self._request(chapter_url, wait_time=5)
        if not driver:
            return {'images': [], 'total_count': 0}

        all_images = []  # List[Dict] 存储 {'url': str, 'page': int}
        page_num = 0
        max_pages = 1000  # 设置一个很高的上限，实际由页面指示器控制
        total_images_from_indicator = None  # 从页面指示器获取的总图片数

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

                # 从当前 URL 中提取页码（如果有的话）
                current_url = driver.current_url
                current_page_num = self._extract_page_number_from_url(current_url)

                for img in soup.find_all('img'):
                    src = img.get('src') or img.get('data-src') or img.get('data-original')
                    if src and ('jpg' in src or 'png' in src or 'jpeg' in src or 'webp' in src):
                        # 过滤掉无关图片
                        if not any(x in src.lower() for x in ['logo', 'icon', 'banner', 'ad', 'avatar']):
                            # 检查是否已存在（去重）
                            if not any(img_info['url'] == src for img_info in all_images):
                                # 使用当前 URL 中的页码，如果没有则使用列表长度+1
                                if current_page_num is not None:
                                    page_number = current_page_num
                                else:
                                    page_number = len(all_images) + 1

                                all_images.append({
                                    'url': src,
                                    'page': page_number
                                })

                logger.info(f"第 {page_num + 1} 页: 已收集 {len(all_images)} 张图片")

                # 检查页面指示
                try:
                    # 优先使用 span.manga-page（包含完整信息如 "1/184P"）
                    # 回退到 #pageNo（只显示当前页码 "1"）
                    page_indicator = None
                    try:
                        page_indicator = driver.find_element(By.CSS_SELECTOR, 'span.manga-page')
                    except:
                        page_indicator = driver.find_element(By.CSS_SELECTOR, '#pageNo')

                    page_text = page_indicator.text
                    logger.info(f"页面指示: {page_text}")

                    # 解析 "1/184P" 格式
                    if '/' in page_text:
                        match = page_text.split('/')
                        if match:
                            current = match[0].strip()
                            total = match[1].rstrip('P').strip()

                            # 第一页就提取总图片数
                            if page_num == 0 and total.isdigit():
                                total_images_from_indicator = int(total)
                                logger.info(f"从页面指示器获取总图片数: {total_images_from_indicator}")

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

            # 使用页面指示器的总数，如果没有则使用实际获取的数量
            final_count = total_images_from_indicator if total_images_from_indicator is not None else len(all_images)
            logger.info(f"最终获取到 {len(all_images)} 张图片，总数: {final_count}")

            return {
                'images': all_images,
                'total_count': final_count
            }

        except Exception as e:
            logger.error(f"获取图片失败: {e}")
            traceback.print_exc()
            return {
                'images': all_images,
                'total_count': len(all_images)
            }

    def _extract_page_number_from_url(self, url: str) -> Optional[int]:
        """
        从 URL 中提取页码
        例如: https://m.manhuagui.com/comic/1128/9771.html#p=2 -> 2

        Args:
            url: 章节页面 URL

        Returns:
            页码，如果无法提取则返回 None
        """
        try:
            # 查找 #p= 数字 格式
            match = re.search(r'#p=(\d+)', url)
            if match:
                return int(match.group(1))

            # 尝试其他可能的格式，例如 ?p=2
            match = re.search(r'[?&]p=(\d+)', url)
            if match:
                return int(match.group(1))

        except Exception as e:
            logger.debug(f"从 URL 提取页码失败: {url}, 错误: {e}")

        return None

    def get_image_count(self, chapter_url: str) -> int:
        """
        快速获取章节图片数量（只访问第一页，读取页面指示器）

        Args:
            chapter_url: 章节URL

        Returns:
            图片数量，如果获取失败返回 0
        """
        logger.info(f"快速获取图片数量: {chapter_url}")

        driver = self._request(chapter_url, wait_time=3)
        if not driver:
            logger.warning("无法获取页面，返回0")
            return 0

        try:
            # 优先使用 span.manga-page（包含完整信息如 "1/184P"）
            # 回退到 #pageNo（只显示当前页码 "1"）
            page_indicator = None
            try:
                page_indicator = driver.find_element(By.CSS_SELECTOR, 'span.manga-page')
            except:
                page_indicator = driver.find_element(By.CSS_SELECTOR, '#pageNo')

            page_text = page_indicator.text
            logger.info(f"页面指示: {page_text}")

            # 解析 "1/184P" 或 "1" 格式
            # 有些章节只有一页，指示器只显示 "1"
            # 有些章节有多页，指示器显示 "1/184P"
            if '/' in page_text:
                # 多页格式: "1/184P"
                match = page_text.split('/')
                if match and len(match) >= 2:
                    total = match[1].rstrip('P').strip()
                    if total.isdigit():
                        count = int(total)
                        logger.info(f"快速获取到图片数量: {count}")
                        return count
            else:
                # 单页格式: "1" 或其他数字
                if page_text.isdigit():
                    count = int(page_text)
                    logger.info(f"单页章节，图片数量: {count}")
                    return count

            logger.warning(f"页面指示器格式无法解析: {page_text}")
        except Exception as e:
            logger.warning(f"获取页面指示器失败: {e}")

        return 0

    def close(self):
        """关闭 WebDriver"""
        if self.driver:
            logger.info("关闭 WebDriver...")
            self.driver.quit()
            self.driver = None


def create_fetcher_selenium(use_proxy: bool = False,
                         proxy_pool_url: str = "",
                         headless: bool = True):
    """
    创建漫画抓取器实例（最终修复版：指定 chromedriver 路径）

    Args:
        use_proxy: 忽略此参数
        proxy_pool_url: 忽略此参数
        headless: 是否使用无头模式
    """
    return ManhuaGuiFetcherSelenium(
        headless=headless
    )
