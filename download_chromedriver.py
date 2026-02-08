#!/usr/bin/env python3
"""
简单下载 ChromeDriver 144 的脚本
"""

import urllib.request
import json
import os
import sys

print("=== 下载 ChromeDriver 144 ===")
print()

# 1. 获取版本信息
print("1. 获取版本信息...")
try:
    response = urllib.request.urlopen(
        "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"
    )
    data = json.loads(response.read().decode())
    
    # 查找版本 144
    version_144 = None
    for version in data.get("versions", []):
        if "144.0.7632.46" in version.get("version", ""):
            version_144 = version
            break
    
    if not version_144:
        print("   ❌ 未找到版本 144.0.7632.46")
        sys.exit(1)
    
    print(f"   ✅ 找到版本: {version_144['version']}")
    
    # 查找 Mac x64 下载
    download_url = None
    for platform in version_144.get("downloads", []):
        if platform.get("platform") == "mac-x64" and platform.get("architecture") == "x64":
            download_url = platform.get("url")
            break
    
    if not download_url:
        print("   ❌ 未找到 Mac x64 下载")
        sys.exit(1)
    
    print(f"   ✅ 找到下载: {download_url}")
    print()
    
    # 2. 下载 ChromeDriver
    print("2. 下载 ChromeDriver...")
    filename = f"/tmp/chromedriver_{version_144['version']}_mac_x64"
    
    try:
        urllib.request.urlretrieve(download_url, filename)
        file_size = os.path.getsize(filename)
        print(f"   ✅ 下载成功: {file_size} 字节")
        print(f"   保存位置: {filename}")
        print()
        
        # 3. 设置可执行权限
        print("3. 设置可执行权限...")
        os.chmod(filename, 0o755)
        print(f"   ✅ 权限已设置")
        print()
        
        # 4. 移动到 /usr/local/bin/
        print("4. 移动到 /usr/local/bin/chromedriver...")
        os.system(f"sudo cp {filename} /usr/local/bin/chromedriver")
        print(f"   ✅ 已复制到 /usr/local/bin/chromedriver")
        print()
        
        # 5. 验证
        print("5. 验证安装...")
        os.system("/usr/local/bin/chromedriver --version")
        print()
        
        print("="*80)
        print("✅ ChromeDriver 144 安装完成！")
        print("="*80)
        print()
        print("下一步：")
        print("1. 运行 Selenium 测试")
        print("2. 验证是否能访问漫画龟")
        
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        sys.exit(1)
        
except Exception as e:
    print(f"   ❌ 失败: {e}")
    sys.exit(1)

