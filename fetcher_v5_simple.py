"""
漫画抓取模块 V5 - 简化版
功能：直接测试不同的 TLS 设置
"""

import requests
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Optional
import logging
from pathlib import Path
from urllib.parse import urljoin
import time
import json
import ssl
import urllib3

logger = logging.getLogger(__name__)


class ManhuaGuiFetcherV5:
    """漫画龟抓取器 V5 (简化版 - 直接 SSL 配置）"""

    def __init__(self, base_url: str = "https://m.manhuagui.com"):
        """
        初始化抓取器
        
        Args:
            base_url: 基础 URL
        """
        self.base_url = base_url
        
        # 完整的浏览器请求头
        self.default_headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'Pragma': 'no-cache',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'DNT': '1',
            'Referer': base_url
        }
        
        logger.info(f"抓取器已初始化")

    def test_request_1(self, url: str) -> Optional[str]:
        """
        测试方法 1: 基础 requests，关闭 SSL 验证
        """
        try:
            logger.info(f"测试 1: 基础 requests，关闭 SSL 验证")
            
            response = requests.get(url, headers=self.default_headers, verify=False, timeout=30)
            
            if response.status_code == 200:
                logger.info(f"✅ 测试 1 成功: {response.status_code}")
                return response.text
            else:
                logger.warning(f"⚠️ 测试 1 状态码: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"❌ 测试 1 失败: {e}")
            return None

    def test_request_2(self, url: str) -> Optional[str]:
        """
        测试方法 2: 使用 session，设置 SSL 上下文
        """
        try:
            logger.info(f"测试 2: 使用 session，设置 SSL 上下文")
            
            session = requests.Session()
            session.headers.update(self.default_headers)
            
            # 创建宽松的 SSL 上下文
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            # 设置 TLS 1.0+ 支持
            ctx.minimum_version = ssl.TLSVersion.TLSv1
            ctx.maximum_version = ssl.TLSVersion.MAXIMUM_SUPPORTED
            
            # 设置加密套件
            ctx.set_ciphers('DEFAULT:@SECLEVEL=1')
            
            # 创建适配器
            adapter = requests.adapters.HTTPAdapter(
                max_retries=3,
                pool_connections=1
            )
            
            # 设置 SSL 上下文（通过 urllib3）
            adapter.poolmanager.connection_pool_kw['https'] = {
                'ssl_context': ctx,
                'assert_hostname': False,
                'cert_reqs': 0  # ssl.CERT_NONE
            }
            
            session.mount('https://', adapter)
            session.mount('http://', requests.adapters.HTTPAdapter(max_retries=3))
            
            response = session.get(url, timeout=30)
            
            if response.status_code == 200:
                logger.info(f"✅ 测试 2 成功: {response.status_code}")
                return response.text
            else:
                logger.warning(f"⚠️ 测试 2 状态码: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"❌ 测试 2 失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    def test_request_3(self, url: str) -> Optional[str]:
        """
        测试方法 3: 使用 urllib3 直接请求
        """
        try:
            logger.info(f"测试 3: 使用 urllib3 直接请求")
            
            http = urllib3.PoolManager(
                retries=urllib3.Retry(total=3, backoff_factor=2),
                cert_reqs='CERT_NONE',
                assert_hostname=False
            )
            
            # 发送请求
            response = http.request(
                'GET',
                url,
                headers=self.default_headers,
                timeout=urllib3.Timeout(timeout=30)
            )
            
            if response.status == 200:
                logger.info(f"✅ 测试 3 成功: {response.status}")
                return response.data.decode('utf-8')
            else:
                logger.warning(f"⚠️ 测试 3 状态码: {response.status}")
                return None
        except Exception as e:
            logger.error(f"❌ 测试 3 失败: {e}")
            import traceback
            traceback.print_exc()
            return None


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    print("="*80)
    print("Fetcher V5 简化版 - 多种 SSL/TLS 配置测试")
    print("="*80)
    print()
    
    fetcher = ManhuaGuiFetcherV5()
    url = 'https://m.manhuagui.com/comic/1128/'
    
    # 测试 1
    print("测试 1: 基础 requests")
    print("-"*50)
    result1 = fetcher.test_request_1(url)
    if result1:
        print(f"内容长度: {len(result1)} 字符")
        print(f"前 200 字符:")
        print(result1[:200])
        print("\n🎉 测试 1 成功！")
    else:
        print("测试 1 失败")
    
    print("\n" + "="*80 + "\n")
    
    # 测试 2
    print("测试 2: Session + SSL 上下文")
    print("-"*50)
    result2 = fetcher.test_request_2(url)
    if result2:
        print(f"内容长度: {len(result2)} 字符")
        print(f"前 200 字符:")
        print(result2[:200])
        print("\n🎉 测试 2 成功！")
    else:
        print("测试 2 失败")
    
    print("\n" + "="*80 + "\n")
    
    # 测试 3
    print("测试 3: urllib3 直接请求")
    print("-"*50)
    result3 = fetcher.test_request_3(url)
    if result3:
        print(f"内容长度: {len(result3)} 字符")
        print(f"前 200 字符:")
        print(result3[:200])
        print("\n🎉 测试 3 成功！")
    else:
        print("测试 3 失败")
    
    print("\n" + "="*80)
    print("测试总结")
    print("="*80)
    print(f"测试 1: {'✅ 成功' if result1 else '❌ 失败'}")
    print(f"测试 2: {'✅ 成功' if result2 else '❌ 失败'}")
    print(f"测试 3: {'✅ 成功' if result3 else '❌ 失败'}")
