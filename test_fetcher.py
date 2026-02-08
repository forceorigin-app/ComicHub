"""
测试新的 fetcher.py
"""

import logging
import sys

# 添加项目路径
sys.path.insert(0, '.')

from fetcher import create_fetcher, create_fetcher_from_config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_direct_connection():
    """测试 1: 不使用代理直接连接"""
    print("\n" + "="*80)
    print("测试 1: 不使用代理直接连接")
    print("="*80)
    
    try:
        fetcher = create_fetcher(use_proxy=False)
        print(f"抓取器已创建 (代理: 未启用)")
        
        # 搜索漫画
        results = fetcher.search_comics_direct("海贼王")
        print(f"\n✅ 直接搜索成功，找到 {len(results)} 部漫画")
        
        for i, comic in enumerate(results[:5], 1):
            print(f"  {i}. {comic['name']} (ID: {comic['id']})")
        
        return True
    except Exception as e:
        print(f"\n❌ 直接连接测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_proxy_connection():
    """测试 2: 使用代理连接"""
    print("\n" + "="*80)
    print("测试 2: 使用代理连接")
    print("="*80)
    
    try:
        fetcher = create_fetcher(use_proxy=True, proxy_pool_url="http://localhost:5010")
        print(f"抓取器已创建 (代理: 已启用)")
        
        # 搜索漫画
        results = fetcher.search_comics("海贼王")
        print(f"\n✅ 代理搜索成功，找到 {len(results)} 部漫画")
        
        for i, comic in enumerate(results[:5], 1):
            print(f"  {i}. {comic['name']} (ID: {comic['id']})")
        
        # 检查代理信息
        if fetcher.current_proxy:
            print(f"\n使用的代理: {fetcher.current_proxy}")
        
        return True
    except Exception as e:
        print(f"\n❌ 代理连接测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_based():
    """测试 3: 从配置文件创建"""
    print("\n" + "="*80)
    print("测试 3: 从配置文件创建")
    print("="*80)
    
    try:
        fetcher = create_fetcher_from_config("config.yaml")
        print(f"抓取器已创建 (从配置文件)")
        print(f"代理配置: {'已启用' if fetcher.use_proxy else '未启用'}")
        
        # 搜索漫画
        results = fetcher.search_comics("海贼王")
        print(f"\n✅ 配置文件搜索成功，找到 {len(results)} 部漫画")
        
        for i, comic in enumerate(results[:3], 1):
            print(f"  {i}. {comic['name']}")
        
        return True
    except Exception as e:
        print(f"\n❌ 配置文件测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("="*80)
    print("Fetcher V3 测试套件")
    print("="*80)
    
    results = []
    
    # 测试 1: 直接连接
    results.append(("直接连接", test_direct_connection()))
    
    # 测试 2: 代理连接
    results.append(("代理连接", test_proxy_connection()))
    
    # 测试 3: 配置文件
    results.append(("配置文件", test_config_based()))
    
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
