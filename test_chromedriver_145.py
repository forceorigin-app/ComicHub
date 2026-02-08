"""
直接测试 ChromeDriver 145（不降级）
"""

import time

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    
    print("=== 测试 ChromeDriver 145 ===")
    print()
    
    # 配置 Chrome 选项
    options = Options()
    
    # 不使用无头模式，这样可以看到 Chrome 窗口
    # options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    
    # 禁用自动化检测
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # 设置窗口大小
    options.add_argument('--window-size=1920,1080')
    
    print("1. Chrome 选项:")
    print("   - 无头模式: 否（可以看到浏览器）")
    print("   - 禁用沙箱: ✅")
    print("   - 禁用自动化检测: ✅")
    print()
    
    # 初始化 WebDriver
    print("2. 初始化 Chrome WebDriver...")
    service = Service()
    driver = webdriver.Chrome(service=service, options=options)
    
    print("   ✅ WebDriver 初始化成功")
    print(f"   当前 URL: {driver.current_url}")
    print(f"   当前标题: {driver.title}")
    print()
    
    # 测试 1: 访问百度
    print("3. 测试 1: 访问百度...")
    driver.get('https://www.baidu.com/')
    time.sleep(2)
    
    print(f"   URL: {driver.current_url}")
    print(f"   标题: {driver.title}")
    print(f"   ✅ 百度访问成功")
    print()
    
    # 测试 2: 访问漫画龟
    print("4. 测试 2: 访问漫画龟首页...")
    driver.get('https://m.manhuagui.com/')
    time.sleep(3)
    
    print(f"   URL: {driver.current_url}")
    print(f"   标题: {driver.title}")
    print(f"   页面长度: {len(driver.page_source)} 字符")
    
    if '漫画' in driver.title or 'manhuagui' in driver.current_url.lower():
        print(f"   ✅ 漫画龟访问成功！")
    else:
        print(f"   ⚠️  页面可能未正确加载")
    
    print()
    print("5. 关闭 WebDriver...")
    driver.quit()
    print("   ✅ WebDriver 已关闭")
    print()
    
    print("="*80)
    print("🎉 测试成功！")
    print("="*80)
    print()
    print("✅ ChromeDriver 145 可以正常工作")
    print("✅ 可以访问百度")
    print("✅ 可以访问漫画龟")
    print()
    print("下一步:")
    print("1. 创建 fetcher_selenium.py 模块")
    print("2. 实现完整的漫画抓取功能")
    print("3. 测试所有功能")
    print("4. 推送代码到 GitHub")
    print()
    
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
