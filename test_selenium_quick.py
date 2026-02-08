"""
快速 Selenium 测试 - 测试基础功能
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def quick_test():
    """快速测试 Selenium 是否能工作"""
    try:
        # 配置 Chrome 选项
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        
        print("✅ Chrome 选项配置完成")
        print()
        
        # 初始化 WebDriver
        print("1. 初始化 WebDriver...")
        driver = webdriver.Chrome(options=chrome_options)
        print("   ✅ WebDriver 初始化成功")
        print()
        
        # 测试 1: 访问百度（快速测试）
        print("2. 测试 1: 访问百度...")
        driver.get('https://www.baidu.com/')
        time.sleep(2)
        print(f"   ✅ 百度访问成功")
        print(f"   标题: {driver.title}")
        print()
        
        # 测试 2: 访问漫画龟
        print("3. 测试 2: 访问漫画龟首页...")
        driver.get('https://m.manhuagui.com/')
        time.sleep(3)
        print(f"   ✅ 漫画龟首页访问成功")
        print(f"   URL: {driver.current_url}")
        print(f"   页面标题: {driver.title}")
        print(f"   页面长度: {len(driver.page_source)} 字符")
        
        if '漫画' in driver.title or 'manhuagui' in driver.current_url.lower():
            print("   ✅ 页面内容正确！")
        else:
            print("   ⚠️  页面内容可能不正确")
        
        print()
        print("🎉 Selenium 测试成功！")
        return True
        
    except Exception as e:
        print(f"❌ Selenium 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 关闭浏览器
        try:
            if 'driver' in locals():
                print("")
                print("4. 关闭 WebDriver...")
                driver.quit()
                print("   ✅ WebDriver 已关闭")
        except:
            pass

if __name__ == "__main__":
    print("="*80)
    print("Selenium 快速测试")
    print("="*80)
    print()
    
    success = quick_test()
    
    print()
    print("="*80)
    if success:
        print("✅ Selenium 方案验证成功！")
        print("   - ChromeDriver 正常工作")
        print("   - 可以访问百度")
        print("   - 可以访问漫画龟")
        print()
        print("下一步:")
        print("1. 创建 fetcher_selenium.py 模块")
        print("2. 实现完整的漫画抓取功能")
        print("3. 测试所有功能")
    else:
        print("⚠️  Selenium 测试失败")
        print()
        print("可能的问题:")
        print("1. Chrome 浏览器未安装")
        print("2. ChromeDriver 版本不匹配")
        print("3. 系统权限问题")
        print()
        print("解决方案:")
        print("1. 安装 Chrome 浏览器")
        print("2. 重新安装 ChromeDriver")
        print("3. 使用 sudo 运行测试")
    print("="*80)
