"""
Selenium 简单测试脚本 - 不下载，不安装
假设你已经手动安装了 ChromeDriver 144
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time
import sys

print("="*80)
print("Selenium 简单测试")
print("="*80)
print()
print("此脚本假设你已经手动安装了 ChromeDriver 144")
print()

try:
    print("步骤 1: 检查 ChromeDriver 是否存在...")
    import subprocess
    
    try:
        # 检查 ChromeDriver 是否在 PATH 中
        result = subprocess.run(['which', 'chromedriver'], capture_output=True, text=True)
        if result.returncode == 0:
            chromedriver_path = result.stdout.strip()
            print(f"   ✅ 找到 ChromeDriver: {chromedriver_path}")
            
            # 检查版本
            version_result = subprocess.run(['chromedriver', '--version'], capture_output=True, text=True, stderr=subprocess.STDOUT)
            print(f"   版本: {version_result.stdout.strip() if version_result.stdout else version_result.stderr.strip()}")
        else:
            print(f"   ⚠️  chromedriver 命令未找到")
            print(f"   请先手动安装 ChromeDriver 144")
            sys.exit(1)
    except Exception as e:
        print(f"   ❌ 检查失败: {e}")
        sys.exit(1)
    
    print()
    print("步骤 2: 配置 Chrome 选项...")
    options = Options()
    
    # 不使用无头模式，这样可以看到浏览器窗口（更容易调试）
    # options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    
    # 禁用自动化检测
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    print("   - 禁用沙箱")
    print("   - 禁用自动化检测")
    print("   - 无头模式: 否（可以看到浏览器窗口）")
    
    print()
    print("步骤 3: 初始化 WebDriver...")
    driver = webdriver.Chrome(options=options)
    
    print("   ✅ WebDriver 初始化成功")
    print(f"   当前 URL: {driver.current_url}")
    print(f"   当前标题: {driver.title}")
    
    # 等待一下，让浏览器完全启动
    time.sleep(3)
    
    print()
    print("步骤 4: 测试访问百度...")
    driver.get('https://www.baidu.com/')
    time.sleep(3)
    
    print(f"   ✅ 百度访问成功")
    print(f"   URL: {driver.current_url}")
    print(f"   标题: {driver.title}")
    
    print()
    print("步骤 5: 测试访问漫画龟...")
    driver.get('https://m.manhuagui.com/')
    time.sleep(5)
    
    print(f"   URL: {driver.current_url}")
    print(f"   标题: {driver.title}")
    print(f"   页面长度: {len(driver.page_source)} 字符")
    
    if '漫画' in driver.title or 'manhuagui' in driver.current_url.lower() or len(driver.page_source) > 1000:
        print(f"   ✅ 漫画龟访问成功！")
    else:
        print(f"   ⚠️  页面可能未正确加载")
    
    print()
    print("步骤 6: 关闭 WebDriver...")
    driver.quit()
    
    print("   ✅ WebDriver 已关闭")
    print()
    print("="*80)
    print("🎉 测试成功！")
    print("="*80)
    print()
    print("✅ ChromeDriver 正常工作")
    print("✅ 可以访问百度")
    print("✅ 可以访问漫画龟")
    print()
    print("下一步:")
    print("1. 创建 fetcher_selenium.py 模块")
    print("2. 实现完整的漫画抓取功能")
    print("3. 测试所有功能")
    print("4. 推送代码到 GitHub")
    print()
    sys.exit(0)
    
except Exception as e:
    print()
    print("="*80)
    print("❌ 测试失败")
    print("="*80)
    print()
    print(f"错误: {e}")
    print()
    import traceback
    traceback.print_exc()
    print()
    print("可能的问题:")
    print("1. ChromeDriver 未正确安装")
    print("2. Chrome 浏览器未安装")
    print("3. ChromeDriver 版本与 Chrome 不匹配")
    print("4. 系统权限问题")
    print()
    print("解决方案:")
    print("1. 手动安装 ChromeDriver 144")
    print("2. 确保 Chrome 浏览器是 144 版本")
    print("3. 重启终端后再次运行测试")
    print()
    sys.exit(1)
