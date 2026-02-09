"""
漫画抓取模块 V8 - 完整分页支持
使用 JavaScript 获取所有图片（不依赖 Selenium 翻页）
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import logging
from urllib.parse import urljoin
from typing import List, Dict, Optional
import time

logger = logging.getLogger(__name__)


class ManhuaGuiFetcherSeleniumV8:
    """漫画龟抓取器 V8 (完整图片抓取)"""

    def __init__(self, headless: bool = True):
        """初始化抓取器"""
        self.headless = headless
        self.driver = None
        self._init_driver()
        logger.info(f"抓取器已初始化 (无头模式: {'是' if self.headless else '否'})")

    def _init_driver(self):
        """初始化 Chrome WebDriver"""
        try:
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            
            service = Service()
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("WebDriver 初始化成功")
            return True
        except Exception as e:
            logger.error(f"WebDriver 初始化失败: {e}")
            return False

    def get_images(self, chapter_url: str) -> List[str]:
        """获取章节图片列表（完整版）"""
        logger.info(f"获取章节图片: {chapter_url}")

        try:
            self.driver.get(chapter_url)
            time.sleep(5)  # 等待页面加载和 JavaScript 解码

            # 使用 JavaScript 收集所有图片（点击所有页）
            js_code = """
            (async function() {
                let allImages = [];
                let pageCount = 0;
                
                // 收集当前页的图片
                function collectImages() {
                    const imgs = document.querySelectorAll('img[src*=".webp"]');
                    for (let img of imgs) {
                        if (!img.src.includes('logo') && !img.src.includes('icon') && !img.src.includes('banner')) {
                            if (!allImages.includes(img.src)) {
                                allImages.push(img.src);
                            }
                        }
                    }
                }
                
                collectImages();
                pageCount++;
                
                // 点击"下一页"并收集
                while (pageCount <= 30) {
                    const nextBtn = document.querySelector('[data-action="next"]');
                    if (!nextBtn) break;
                    
                    nextBtn.click();
                    await new Promise(resolve => setTimeout(resolve, 2000));
                    collectImages();
                    pageCount++;
                }
                
                return allImages;
            })()
            """
            
            images = self.driver.execute_script(js_code)
            logger.info(f"获取到 {len(images)} 张图片")
            
            return images

        except Exception as e:
            logger.error(f"获取图片失败: {e}")
            return []

    def close(self):
        """关闭 WebDriver"""
        if self.driver:
            self.driver.quit()
            self.driver = None


# 临时测试函数
def test_fetcher():
    """测试抓取器"""
    logging.basicConfig(level=logging.INFO)
    
    fetcher = ManhuaGuiFetcherSeleniumV8(headless=True)
    url = 'https://m.manhuagui.com/comic/1128/862270.html'
    
    print(f"测试图片抓取: {url}")
    images = fetcher.get_images(url)
    
    print(f"\n找到 {len(images)} 张图片:")
    for i, img in enumerate(images, 1):
        print(f"  {i}. {img}")
    
    fetcher.close()


if __name__ == "__main__":
    test_fetcher()
