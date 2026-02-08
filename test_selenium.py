"""
Selenium 测试脚本 - 测试是否能访问漫画龟
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import logging
import time

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_selenium_access():
    """测试 Selenium 访问漫画龟"""
    print("="*80)
    print("Selenium 测试 - 漫画龟访问")
    print("="*80)
    print()
    
    # 配置 Chrome 选项
    chrome_options = Options()
    
    # 使用无头模式（Headless）
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    # 添加用户代理
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # 设置 User-Agent（模拟真实浏览器）
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    print("Chrome 选项:")
    print("  无头模式: ✅")
    print("  禁用 GPU: ✅")
    print("  禁用沙箱: ✅")
    print("  反自动化检测: ✅")
    print()
    
    driver = None
    try:
        print("1. 初始化 Chrome WebDriver...")
        driver = webdriver.Chrome(options=chrome_options)
        
        print("   ✅ WebDriver 初始化成功")
        print()
        
        # 测试 1: 访问首页
        print("2. 测试 1: 访问漫画龟首页...")
        print("   URL: https://m.manhuagui.com/")
        
        driver.get('https://m.manhuagui.com/')
        
        # 等待页面加载
        time.sleep(5)
        
        # 获取页面标题
        title = driver.title
        print(f"   页面标题: {title}")
        print(f"   URL: {driver.current_url}")
        
        # 获取页面源
        page_source = driver.page_source
        print(f"   页面长度: {len(page_source)} 字符")
        
        if '漫画' in title or 'manhuagui' in driver.current_url.lower():
            print("   ✅ 首页访问成功！")
        else:
            print("   ⚠️  首页可能未正确加载")
        
        print()
        
        # 测试 2: 访问漫画详情页
        print("3. 测试 2: 访问漫画详情页...")
        print("   URL: https://m.manhuagui.com/comic/1128/")
        
        driver.get('https://m.manhuagui.com/comic/1128/')
        
        # 等待页面加载
        time.sleep(5)
        
        # 获取页面信息
        title = driver.title
        print(f"   页面标题: {title}")
        print(f"   URL: {driver.current_url}")
        
        # 获取页面源
        page_source = driver.page_source
        print(f"   页面长度: {len(page_source)} 字符")
        
        # 检查页面内容
        if '1128' in page_source or '漫画' in page_source:
            print("   ✅ 漫画详情页访问成功！")
            print(f"   页面片段（前 200 字符）:")
            print(f"     {page_source[:200]}...")
        else:
            print("   ⚠️  漫画详情页可能未正确加载")
        
        print()
        print("="*80)
        print("✅ Selenium 测试完成！")
        print("="*80)
        print()
        print("🎉 如果上述测试都成功，说明 Selenium 方案有效！")
        print()
        print("下一步:")
        print("1. 创建 fetcher_selenium.py 模块")
        print("2. 集成 Selenium 到 ComicHub")
        print("3. 测试完整抓取功能")
        print()
        return True
        
    except Exception as e:
        print()
        print("="*80)
        print("❌ Selenium 测试失败")
        print("="*80)
        print(f"错误: {e}")
        print()
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # 关闭浏览器
        if driver:
            print("关闭 WebDriver...")
            driver.quit()
            print("✅ WebDriver 已关闭")
            print()


if __name__ == "__main__":
    try:
        success = test_selenium_access()
        
        if success:
            print("🎉 Selenium 方案验证成功！")
            exit(0)
        else:
            print("⚠️  Selenium 方案验证失败，需要进一步诊断")
            exit(1)
    except Exception as e:
        print(f"❌ 测试脚本异常: {e}")
        exit(1)
