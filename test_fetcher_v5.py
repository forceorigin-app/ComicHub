"""
测试 fetcher_v5.py (SSL 优化版）
"""

import logging
import sys
import time

# 添加项目路径
sys.path.insert(0, '.')

from fetcher_v5 import create_fetcher_v5

# 配置日志（显示详细日志）
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_permissive_ssl():
    """测试 1: 宽松 SSL 模式（permissive - TLS 1.0+）"""
    print("\n" + "="*80)
    print("测试 1: 宽松 SSL 模式 (permissive - TLS 1.0+)")
    print("="*80)
    
    try:
        fetcher = create_fetcher_v5(use_proxy=False, ssl_mode="permissive")
        
        # 初始化会话
        print("\n1.1 初始化会话（访问首页获取 cookies）...")
        if fetcher.initialize_session():
            print("✅ 会话初始化成功")
        else:
            print("⚠️  会话初始化失败，但继续测试...")
        
        # 测试漫画页
        print("\n1.2 测试漫画页...")
        r = fetcher._request_direct('https://m.manhuagui.com/comic/1128/', timeout=30)
        
        if r:
            print(f"✅ 漫画页连接成功: {r.status_code}")
            print(f"内容长度: {len(r.text)} 字符")
            print(f"HTML 片段（前 300 字符):")
            print(f"  {r.text[:300]}...")
            return True
        else:
            print("❌ 漫画页连接失败")
            return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_legacy_ssl():
    """测试 2: 旧版本 SSL 模式（legacy - TLS 1.0-1.1）"""
    print("\n" + "="*80)
    print("测试 2: 旧版本 SSL 模式 (legacy - TLS 1.0-1.1)")
    print("="*80)
    
    try:
        fetcher = create_fetcher_v5(use_proxy=False, ssl_mode="legacy")
        
        # 初始化会话
        print("\n2.1 初始化会话（访问首页获取 cookies）...")
        if fetcher.initialize_session():
            print("✅ 会话初始化成功")
        else:
            print("⚠️  会话初始化失败，但继续测试...")
        
        # 测试漫画页
        print("\n2.2 测试漫画页...")
        r = fetcher._request_direct('https://m.manhuagui.com/comic/1128/', timeout=30)
        
        if r:
            print(f"✅ 漫画页连接成功: {r.status_code}")
            print(f"内容长度: {len(r.text)} 字符")
            return True
        else:
            print("❌ 漫画页连接失败")
            return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_search():
    """测试 3: 搜索功能（自动使用宽松 SSL）"""
    print("\n" + "="*80)
    print("测试 3: 搜索功能（自动使用宽松 SSL）")
    print("="*80)
    
    try:
        fetcher = create_fetcher_v5(use_proxy=False, ssl_mode="permissive")
        
        print("\n3.1 搜索漫画...")
        results = fetcher.search_comics_direct("海贼王")
        
        if results:
            print(f"✅ 搜索成功: {len(results)} 部漫画")
            for i, comic in enumerate(results[:5], 1):
                print(f"  {i}. {comic['name']} (ID: {comic['id']})")
            return True
        else:
            print("❌ 搜索失败")
            return False
    except Exception as e:
        print(f"❌ 搜索失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("="*80)
    print("Fetcher V5 测试套件 (SSL 优化版)")
    print("="*80)
    print("\nV5 新特性:")
    print("  ✅ 多种 SSL 模式（permissive/modern/legacy）")
    print("  ✅ 宽松 SSL 配置（类似浏览器）")
    print("  ✅ 自动切换到更宽松的 SSL 模式")
    print("  ✅ 更长的超时时间")
    print("  ✅ TLS 1.0+ 支持")
    print("  ✅ 证书验证控制")
    print("  ✅ 加密套件控制")
    print("  ✅ 完整浏览器请求头")
    print("  ✅ Cookie 会话管理")
    
    results = []
    
    # 测试 1: 宽松 SSL 模式
    print("\n开始测试 1...")
    results.append(("宽松 SSL", test_permissive_ssl()))
    
    # 等待
    print("\n等待 5 秒...")
    time.sleep(5)
    
    # 测试 2: 旧版本 SSL 模式
    print("\n开始测试 2...")
    results.append(("Legacy SSL", test_legacy_ssl()))
    
    # 等待
    print("\n等待 5 秒...")
    time.sleep(5)
    
    # 测试 3: 搜索功能
    print("\n开始测试 3...")
    results.append(("搜索功能", test_search()))
    
    # 测试总结
    print("\n" + "="*80)
    print("测试总结")
    print("="*80)
    
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{test_name}: {status}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"\n总计: {passed}/{total} 个测试通过")
    
    if passed > 0:
        print("\n🎉 至少有部分测试成功！SSL 问题可能已部分解决")
        return 0
    else:
        print("\n⚠️  所有测试失败，可能需要进一步诊断")
        return 1

if __name__ == "__main__":
    sys.exit(main())
