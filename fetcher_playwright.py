"""
Playwright 漫画抓取器 - 异步版
使用 async_playwright（playwright 只支持异步）
"""
import asyncio
import re
import logging
import traceback
from typing import List, Dict, Optional
from urllib.parse import urljoin

from playwright.async_api import async_playwright, Browser, Page
from bs4 import BeautifulSoup

# 设置日志
logger = logging.getLogger(__name__)


class ManhuaGuiFetcherPlaywright:
    """漫画柜 Playwright 抓取器（异步版）"""

    def __init__(self, headless: bool = True):
        """
        初始化抓取器

        Args:
            headless: 是否使用无头模式
        """
        self.base_url = "https://m.manhuagui.com"
        self.headless = headless
        
        # Playwright 组件（异步）
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        
        logger.info(f"抓取器已创建 (无头模式: {'是' if self.headless else '否'}, Playwright 异步版)")

    async def _init_browser(self):
        """初始化 Playwright 浏览器"""
        try:
            # 启动 Playwright
            self.playwright = await async_playwright().start()
            
            # 启动 Chromium
            self.browser = await self.playwright.chromium.launch(headless=self.headless)
            
            # 创建上下文
            self.context = await self.browser.new_context()
            
            # 创建页面
            self.page = await self.context.new_page()
            
            logger.info("Playwright 浏览器初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"Playwright 浏览器初始化失败: {e}")
            traceback.print_exc()
            return False

    async def _request(self, url: str, wait_time: int = 5):
        """
        访问 URL 并返回 Page

        Args:
            url: 请求 URL
            wait_time: 等待时间
        """
        logger.info(f"请求 URL: {url}")
        
        try:
            # 直接访问
            await self.page.goto(url, wait_until="networkidle", timeout=60000)
            # 等待一下
            await asyncio.sleep(wait_time)
            return self.page
        except Exception as e:
            logger.error(f"请求失败: {url}, 错误: {e}")
            return None

    async def search_comics(self, keyword: str) -> List[Dict]:
        """搜索漫画"""
        logger.info(f"搜索漫画: {keyword}")
        
        # 构建搜索 URL
        search_url = urljoin(self.base_url, f"/s/{keyword}")
        
        # 请求
        page = await self._request(search_url)
        if not page:
            return []
        
        # 解析页面
        soup = BeautifulSoup(await page.content(), 'html.parser')
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

    async def get_comic_info(self, comic_url: str) -> Optional[Dict]:
        """获取漫画信息"""
        logger.info(f"获取漫画信息: {comic_url}")
        
        # 请求
        page = await self._request(comic_url)
        if not page:
            return None
        
        # 解析页面
        soup = BeautifulSoup(await page.content(), 'html.parser')
        
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

    async def get_chapters(self, comic_url: str) -> List[Dict]:
        """获取章节列表"""
        logger.info(f"获取章节列表: {comic_url}")
        
        # 请求
        page = await self._request(comic_url)
        if not page:
            return []
        
        # 解析页面
        soup = BeautifulSoup(await page.content(), 'html.parser')
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

    async def get_images(self, chapter_url: str) -> List[str]:
        """获取章节图片列表（支持翻页）"""
        logger.info(f"获取章节图片: {chapter_url}")

        # 请求
        page = await self._request(chapter_url, wait_time=5)
        if not page:
            return []

        all_images = []
        page_num = 0
        max_pages = 30

        try:
            while page_num < max_pages:
                # 处理可能的 alert
                try:
                    # 检查是否有 alert
                    if await page.evaluate('() => !!document.querySelector("#pageNo")'):
                        # 点击 alert
                        await page.click('button:has-text("确定")')
                        await asyncio.sleep(1)
                        break
                except:
                    pass  # 没有 alert

                # 获取当前页面的图片
                soup = BeautifulSoup(await page.content(), 'html.parser')
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
                    page_indicator = page.locator('#pageNo')
                    if await page_indicator.count() > 0:
                        page_text = await page_indicator.inner_text()
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
                    # 使用 Playwright 的方式查找包含"下一页"文本的链接
                    next_links = page.locator('a:has-text("下一页")')

                    if await next_links.count() == 0:
                        # 尝试其他方式查找下一页
                        next_links = page.locator('a[data-action="next"]')

                    if await next_links.count() == 0:
                        logger.info("没有找到下一页按钮")
                        break

                    # 点击第一个"下一页"链接
                    await next_links.first.click()
                    await asyncio.sleep(2.5)  # 等待下一页加载
                    page_num += 1

                except Exception as e:
                    logger.info(f"点击下一页失败: {e}")
                    break

            logger.info(f"最终获取到 {len(all_images)} 张图片")
            return all_images

        except Exception as e:
            logger.error(f"获取图片失败: {e}")
            traceback.print_exc()
            return all_images

    async def close(self):
        """关闭 Playwright 浏览器"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        
        logger.info("Playwright 浏览器已关闭")


def create_fetcher_playwright(headless: bool = True):
    """
    创建漫画抓取器实例（Playwright 异步版）

    Args:
        headless: 是否使用无头模式
    """
    # 注意：这里返回的是类，不是实例，因为初始化是异步的
    return ManhuaGuiFetcherPlaywright
