"""
最简化的 SSL 测试
"""

import requests
import logging

logging.basicConfig(level=logging.INFO)

def test_1_basic():
    """测试 1: 最基础的 requests"""
    print("\n" + "="*80)
    print("测试 1: 最基础的 requests（关闭 SSL 验证）")
    print("="*80)
    
    try:
        print("\n请求首页...")
        response = requests.get(
            'https://m.manhuagui.com/',
            verify=False,
            timeout=30,
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
        )
        
        print(f"状态码: {response.status_code}")
        print(f"内容长度: {len(response.text)} 字符")
        print(f"响应头: {dict(response.headers)}")
        
        return True
    except Exception as e:
        print(f"错误: {e}")
        return False

def test_2_session():
    """测试 2: 使用 session（模拟浏览器）"""
    print("\n" + "="*80)
    print("测试 2: 使用 session（模拟浏览器）")
    print("="*80)
    
    try:
        session = requests.Session()
        
        # 设置浏览器 headers
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'Pragma': 'no-cache',
            'Upgrade-Insecure-Requests': '1'
        })
        
        print("\n请求首页...")
        response = session.get(
            'https://m.manhuagui.com/',
            verify=False,
            timeout=30
        )
        
        print(f"状态码: {response.status_code}")
        print(f"内容长度: {len(response.text)} 字符")
        print(f"Session cookies: {list(session.cookies)}")
        
        print("\n请求漫画页...")
        response2 = session.get(
            'https://m.manhuagui.com/comic/1128/',
            verify=False,
            timeout=30
        )
        
        print(f"状态码: {response2.status_code}")
        print(f"内容长度: {len(response2.text)} 字符")
        
        return True
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_3_with_env():
    """测试 3: 设置环境变量控制 SSL"""
    print("\n" + "="*80)
    print("测试 3: 使用环境变量禁用 SSL 验证")
    print("="*80)
    
    import os
    import ssl
    
    # 设置环境变量（requests 尊重这些）
    os.environ['CURL_CA_BUNDLE'] = ''
    os.environ['REQUESTS_CA_BUNDLE'] = ''
    
    try:
        print("\n请求首页...")
        response = requests.get(
            'https://m.manhuagui.com/',
            verify=False,
            timeout=30,
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
        )
        
        print(f"状态码: {response.status_code}")
        print(f"内容长度: {len(response.text)} 字符")
        
        return True
    except Exception as e:
        print(f"错误: {e}")
        return False

def main():
    """主测试函数"""
    print("="*80)
    print("简化版 SSL 测试")
    print("="*80)
    
    results = []
    
    # 测试 1
    results.append(("基础 requests", test_1_basic()))
    
    # 测试 2
    results.append(("Session 模拟", test_2_session()))
    
    # 测试 3
    results.append(("环境变量", test_3_with_env()))
    
    # 总结
    print("\n" + "="*80)
    print("测试总结")
    print("="*80)
    
    for test_name, success in results:
        status = "✅ 成功" if success else "❌ 失败"
        print(f"{test_name}: {status}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"\n总计: {passed}/{total} 个测试通过")
    
    if passed > 0:
        print("\n🎉 至少有部分测试成功！")
    else:
        print("\n⚠️  所有测试失败")

if __name__ == "__main__":
    main()
