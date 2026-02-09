"""
漫画抓取模块 V8 - 修复版（处理 Alert）
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import logging
import time

logger = logging.getLogger(__name__)


class ManhuaGuiFetcherSeleniumV8:
    """漫画龟抓取器 V8 (修复 Alert 问题）"""

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
            
            service = webdriver.chrome.service.Service()
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("WebDriver 初始化成功")
            return True
        except Exception as e:
            logger.error(f"WebDriver 初始化失败: {e}")
            return False

    def get_images(self, chapter_url: str) -> list:
        """获取章节图片列表（处理 Alert）"""
        logger.info(f"获取章节图片: {chapter_url}")

        try:
            self.driver.get(chapter_url)
            time.sleep(5)  # 等待页面加载和 JavaScript 解码

            all_images = []
            page_num = 0
            max_pages = 20

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
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                for img in soup.find_all('img'):
                    src = img.get('src') or img.get('data-src') or img.get('data-original')
                    if src and ('jpg' in src or 'png' in src or 'jpeg' in src or 'webp' in src):
                        # 过滤掉无关图片
                        if not any(x in src.lower() for x in ['logo', 'icon', 'banner', 'ad', 'avatar']):
                            if src not in all_images:
                                all_images.append(src)

                logger.info(f"第 {page_num + 1} 页: 已收集 {len(all_images)} 张图片")

                # 检查页面指示
                page_indicator = self.driver.find_element(By.CSS_SELECTOR, '#pageNo')
                current_page = page_indicator.text
                logger.info(f"页面指示: {current_page}")

                # 尝试点击"下一页"按钮
                try:
                    # 查找 data-action="next" 的按钮（不是 chapter.next）
                    next_buttons = self.driver.find_elements(By.CSS_SELECTOR, 'a[data-action="next"]')
                    
                    if not next_buttons:
                        logger.info("没有找到下一页按钮")
                        break

                    # 查找页码指示器，检查是否是最后一页
                    page_indicator = self.driver.find_element(By.CSS_SELECTOR, '#pageNo')
                    if page_indicator:
                        page_text = page_indicator.text
                        # 解析 "1/13P" 格式
                        match = page_text.split('/')
                        if match:
                            current = match[0].strip()
                            total = match[1].rstrip('P').strip()
                            if current == total:
                                logger.info(f"已到最后一页: {page_text}")
                                break

                    # 点击下一页
                    next_button = next_buttons[0]
                    next_button.click()
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
            return []

    def close(self):
        """关闭 WebDriver"""
        if self.driver:
            self.driver.quit()
            self.driver = None


# 测试函数
def test_fetcher():
    """测试抓取器"""
    logging.basicConfig(level=logging.INFO)
    
    fetcher = ManhuaGuiFetcherSeleniumV8(headless=True)
    url = 'https://m.manhuagui.com/comic/1128/862270.html'
    
    print(f"测试图片抓取: {url}")
    images = fetcher.get_images(url)
    
    print(f"\n找到 {len(images)} 张图片:")
    for i, img in enumerate(images[:20], 1):
        print(f"  {i}. {img}")
    
    if len(images) > 20:
        print(f"  ... 还有 {len(images) - 20} 张")
    
    fetcher.close()
    print("\n测试完成!")


if __name__ == "__main__":
    test_fetcher()
