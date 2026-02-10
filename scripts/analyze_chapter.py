"""
漫画章节页面分析脚本 - 最终修复版（使用正确的域名）
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import re
import time
from pathlib import Path
from urllib.parse import urljoin
import logging
import sys
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

logger = logging.getLogger(__name__)


class ChapterAnalyzer:
    """章节页面分析器（使用正确的域名）"""
    
    def __init__(self, chapter_url: str):
        """
        初始化分析器
        
        Args:
            chapter_url: 章节 URL（如 https://m.anhuagui.com/comic/1128/858078.html）
        """
        # 修复域名
        self.chapter_url = chapter_url.replace('m.anhuagui.com', 'manhuagui.com')
        self.base_url = 'https://m.anhuagui.com'
        self.driver = None
        self.images = []
        
        logger.info(f"章节URL: {self.chapter_url}")
        logger.info(f"基础URL: {self.base_url}")
        
        self._init_driver()
    
    def _init_driver(self):
        """初始化 Chrome WebDriver"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            
            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("浏览器初始化成功")
        except Exception as e:
            logger.error(f"浏览器初始化失败: {e}")
            sys.exit(1)
    
    def analyze_page(self):
        """分析章节页面，找出所有图片"""
        try:
            logger.info("开始分析章节页面...")
            self.driver.get(self.chapter_url)
            time.sleep(5)  # 增加等待时间
            
            page_source = self.driver.page_source
            logger.info(f"页面长度: {len(page_source)} 字符")
            
            soup = BeautifulSoup(page_source, 'html.parser')
            images = []
            
            logger.info("方法 1: 查找 img 标签...")
            for img in soup.find_all('img'):
                src = img.get('src') or img.get('data-src') or img.get('data-original')
                alt = img.get('alt') or img.get('title') or ''
                
                if src and ('jpg' in src or 'png' in src or 'jpeg' in src or 'webp' in src):
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        src = urljoin(self.base_url, src)
                    
                    images.append({
                        'url': src,
                        'alt': alt,
                        'tag': 'img'
                    })
                    logger.info(f"  找到图片: {alt[:30]}... - {src[:50]}...")
            
            logger.info(f"方法 1 找到 {len(images)} 个 img 标签")
            
            logger.info("方法 2: 查找 script 标签中的图片 URL...")
            for script in soup.find_all('script'):
                script_content = script.string
                if script_content:
                    # 查找图片数组
                    matches = re.findall(r'["\']([^"\']+\.jpe?g)["\']', script_content)
                    for match in matches:
                        if match.startswith('http'):
                            images.append({
                                'url': match,
                                'alt': f'JS_{len(images) + 1}',
                                'tag': 'script'
                            })
                            logger.info(f"  找到图片 (JS): {match[:50]}...")
            
            logger.info(f"方法 2 找到 {len(images) - len([i for i in images if i['tag'] == 'img'])} 个 script 图片")
            
            # 去重
            logger.info("去重并排序...")
            unique_images = []
            seen_urls = set()
            
            for img in images:
                if img['url'] not in seen_urls:
                    seen_urls.add(img['url'])
                    unique_images.append(img)
            
            self.images = unique_images
            logger.info(f"总共找到 {len(unique_images)} 张图片（去重后）")
            
            return unique_images
        except Exception as e:
            logger.error(f"页面分析失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_image_count_from_page(self):
        """从页面显示的图片数量"""
        try:
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # 查找页面显示的图片数量
            for element in soup.find_all(text=re.compile(r'\d+张|页|P')):
                text = element.strip()
                if '张' in text or 'P' in text:
                    numbers = re.findall(r'\d+', text)
                    if numbers:
                        return int(numbers[0])
            
            return len(self.images)
        except:
            return len(self.images)
    
    def download_images(self, save_dir: str, chapter_name: str = "未知章节"):
        """下载所有图片到指定目录"""
        try:
            logger.info("="*80)
            logger.info(f"开始下载 {len(self.images)} 张图片")
            logger.info("="*80)
            logger.info(f"保存目录: {save_dir}")
            logger.info(f"章节名称: {chapter_name}")
            logger.info("")
            
            # 创建保存目录
            Path(save_dir).mkdir(parents=True, exist_ok=True)
            chapter_dir = Path(save_dir) / chapter_name
            chapter_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"章节目录创建成功: {chapter_dir}")
            logger.info("")
            
            # 下载图片
            import requests
            
            success_count = 0
            for i, img in enumerate(self.images, 1):
                img_url = img['url']
                filename = f"{i:03d}.jpg"  # 3 位编号
                save_path = chapter_dir / filename
                
                logger.info(f"下载 [{i}/{len(self.images)}] {filename}...")
                
                try:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Referer': self.chapter_url
                    }
                    
                    response = requests.get(img_url, headers=headers, timeout=30, verify=False)
                    if response.status_code == 200:
                        with open(save_path, 'wb') as f:
                            f.write(response.content)
                        success_count += 1
                        logger.info(f"  ✅ 下载成功")
                    else:
                        logger.warning(f"  ❌ 下载失败，状态码: {response.status_code}")
                except Exception as e:
                    logger.error(f"  ❌ 下载异常: {e}")
            
            logger.info("")
            logger.info("="*80)
            logger.info("下载完成")
            logger.info("="*80)
            logger.info(f"✅ 成功下载: {success_count}/{len(self.images)} 张图片")
            logger.info(f"📁 保存位置: {chapter_dir}")
            logger.info("="*80)
            
            return success_count
        except Exception as e:
            logger.error(f"批量下载失败: {e}")
            import traceback
            traceback.print_exc()
            return 0
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            logger.info("关闭浏览器...")
            self.driver.quit()
            self.driver = None


def main():
    """主函数"""
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python3 analyze_chapter.py <章节URL> [保存目录]")
        print("")
        print("示例:")
        print("  python3 analyze_chapter.py https://m.anhuagui.com/comic/1128/858078.html")
        print("  python3 analyze_chapter.py https://m.anhuagui.com/comic/1128/858078.html downloads")
        print("")
        print("注意:")
        print("  - URL 会自动修复域名（m.anhuagui.com -> manhuagui.com）")
        print("  - 图片会按 001.jpg, 002.jpg... 顺序命名")
        print("  - 保存目录: downloads/漫画名/章节名/")
        sys.exit(1)
    
    chapter_url = sys.argv[1]
    save_dir = sys.argv[2] if len(sys.argv) > 2 else "downloads"
    
    # 创建分析器
    analyzer = ChapterAnalyzer(chapter_url)
    
    # 分析页面
    try:
        analyzer.analyze_page()
        
        # 下载图片
        if analyzer.images:
            # 从 URL 提取章节名称
            chapter_num = chapter_url.split('/')[-1].split('.')[0]
            analyzer.download_images(save_dir, f"第{chapter_num}话")
        else:
            logger.warning("没有找到图片，跳过下载")
    finally:
        analyzer.close()
        logger.info("✅ 分析器已关闭")
        logger.info("")


if __name__ == "__main__":
    main()
