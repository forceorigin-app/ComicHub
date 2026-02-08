"""
测试 fetcher_v4.py
"""

import logging
import sys

# 添加项目路径
sys.path.insert(0, '.')

from fetcher_v4 import create_fetcher_v4

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_direct_connection():
    """测试 1: 不使用代理直接连接"""
    print("\n" + "="*80)
    print("测试 1: 不使用代理直接连接（V4 - 完整浏览器请求头 + Cookie 管理）")
    print("="*80)
    
    try:
        fetcher = create_fetcher_v4(use_proxy=False)
        
        # 初始化会话（访问首页获取 cookies）
        print("\n1.1 初始化会话（访问首页获取 cookies）...")
        if fetcher.initialize_session():
            print("✅ 会话初始化成功")
        else:
            print("⚠️  会话初始化失败，但继续尝试搜索...")
        
        # 搜索漫画
        print("\n1.2 搜索漫画...")
        results = fetcher.search_comics_direct("海贼王")
        print(f"✅ 搜索结果: {len(results)} 部漫画")
        
        for i, comic in enumerate(results[:5], 1):
            print(f"  {i}. {comic['name']} (ID: {comic['id']})")
        
        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_proxy_connection():
    """测试 2: 使用代理连接"""
    print("\n" + "="*80)
    print("测试 2: 使用代理连接（V4 - 完整浏览器请求头 + Cookie 管理）")
    print("="*80)
    
    try:
        fetcher = create_fetcher_v4(use_proxy=True, proxy_pool_url="http://localhost:5010")
        
        # 初始化会话（访问首页获取 cookies）
        print("\n2.1 初始化会话（访问首页获取 cookies）...")
        if fetcher.initialize_session():
            print("✅ 会话初始化成功")
        else:
            print("⚠️  会话初始化失败，但继续尝试搜索...")
        
        # 搜索漫画
        print("\n2.2 搜索漫画...")
        results = fetcher.search_comics("海贼王")
        print(f"✅ 搜索结果: {len(results)} 部漫画")
        
        for i, comic in enumerate(results[:5], 1):
            print(f"  {i}. {comic['name']} (ID: {comic['id']})")
        
        # 检查代理信息
        if fetcher.current_proxy:
            print(f"\n使用的代理: {fetcher.current_proxy}")
        
        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("="*80)
    print("Fetcher V4 测试套件")
    print("="*80)
    print("\nV4 新特性:")
    print("  ✅ 完整的浏览器请求头")
    print("  ✅ Cookie 会话管理")
    print("  ✅ 先访问首页获取 cookies")
    print("  ✅ 支持 Cookie 加载和保存")
    print("  ✅ 支持 Sec-Fetch-* 系列请求头")
    print("  ✅ 支持 Cache-Control 和 Pragma")
    
    results = []
    
    # 测试 1: 直接连接
    results.append(("直接连接", test_direct_connection()))
    
    # 测试 2: 代理连接
    results.append(("代理连接", test_proxy_connection()))
    
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
    
    if passed == total:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print("\n⚠️  部分测试失败，请检查日志")
        return 1

if __name__ == "__main__":
    sys.exit(main())
