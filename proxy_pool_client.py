"""
代理池客户端模块
用于从代理池获取代理并验证其可用性
"""

import requests
import logging
from typing import Optional, Dict, List
import json
from urllib.parse import urlparse
import time

logger = logging.getLogger(__name__)


class ProxyPoolClient:
    """代理池客户端"""
    
    def __init__(self, api_url: str = "http://localhost:5010"):
        """
        初始化代理池客户端
        
        Args:
            api_url: 代理池 API 地址
        """
        self.api_url = api_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
        
    def get_proxy(self, mode: str = "random") -> Optional[Dict]:
        """
        从代理池获取代理
        
        Args:
            mode: 获取模式 (random: 随机, fast: 最快)
            
        Returns:
            代理信息字典
        """
        try:
            url = f"{self.api_url}/get/"
            if mode == "fast":
                url += "?type=fast"
            elif mode == "https":
                url += "?type=fast&protocol=https"
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            proxy_data = response.json()
            logger.info(f"获取到代理: {proxy_data.get('proxy', 'N/A')}")
            
            return proxy_data
            
        except Exception as e:
            logger.error(f"获取代理失败: {e}")
            return None
    
    def validate_proxy(self, proxy_url: str, test_url: str = "https://www.baidu.com", 
                     timeout: int = 10) -> bool:
        """
        验证代理是否可用
        
        Args:
            proxy_url: 代理地址 (格式: http://ip:port)
            test_url: 测试 URL
            timeout: 超时时间（秒）
            
        Returns:
            代理是否可用
        """
        try:
            proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
            
            start_time = time.time()
            response = requests.get(
                test_url,
                proxies=proxies,
                timeout=timeout,
                verify=False
            )
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                logger.info(f"代理验证成功: {proxy_url} (耗时: {elapsed:.2f}s)")
                return True
            else:
                logger.warning(f"代理返回非 200 状态码: {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            logger.warning(f"代理超时: {proxy_url}")
            return False
        except requests.exceptions.ProxyError as e:
            logger.warning(f"代理错误: {e}")
            return False
        except Exception as e:
            logger.error(f"代理验证异常: {e}")
            return False
    
    def delete_proxy(self, proxy_url: str) -> bool:
        """
        从代理池删除无效代理
        
        Args:
            proxy_url: 代理地址
            
        Returns:
            是否删除成功
        """
        try:
            url = f"{self.api_url}/delete/"
            data = {'proxy': proxy_url}
            
            response = self.session.delete(url, json=data, timeout=10)
            response.raise_for_status()
            
            logger.info(f"代理已从池中删除: {proxy_url}")
            return True
            
        except Exception as e:
            logger.error(f"删除代理失败: {e}")
            return False
    
    def get_proxy_stats(self) -> Optional[Dict]:
        """
        获取代理池统计信息
        
        Returns:
            统计信息字典
        """
        try:
            url = f"{self.api_url}/get_status/"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"获取代理池统计失败: {e}")
            return None
    
    def get_available_proxies(self, count: int = 1) -> List[Dict]:
        """
        获取多个可用代理
        
        Args:
            count: 需要的代理数量
            
        Returns:
            代理列表
        """
        proxies = []
        attempts = 0
        max_attempts = 10
        
        while len(proxies) < count and attempts < max_attempts:
            attempts += 1
            proxy_data = self.get_proxy()
            
            if not proxy_data:
                continue
            
            proxy_url = proxy_data.get('proxy')
            if not proxy_url:
                continue
            
            # 验证代理
            if self.validate_proxy(proxy_url):
                proxies.append(proxy_data)
            else:
                # 删除无效代理
                self.delete_proxy(proxy_url)
        
        logger.info(f"获取到 {len(proxies)} 个可用代理（尝试次数: {attempts}）")
        return proxies
    
    def create_session_with_proxy(self, proxy_url: Optional[str] = None) -> requests.Session:
        """
        创建使用代理的请求会话
        
        Args:
            proxy_url: 代理地址 (格式: http://ip:port)
            
        Returns:
            requests.Session 对象
        """
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        if proxy_url:
            session.proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
            logger.info(f"会话已配置代理: {proxy_url}")
        
        return session


def create_proxy_pool_client(api_url: str = "http://localhost:5010") -> ProxyPoolClient:
    """
    创建代理池客户端实例
    
    Args:
        api_url: 代理池 API 地址
        
    Returns:
        ProxyPoolClient 实例
    """
    return ProxyPoolClient(api_url=api_url)


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    client = create_proxy_pool_client()
    
    print("=== 测试代理池客户端 ===")
    
    # 获取代理统计
    print("\n1. 代理池统计:")
    stats = client.get_proxy_stats()
    if stats:
        print(json.dumps(stats, indent=2, ensure_ascii=False))
    
    # 获取一个随机代理
    print("\n2. 获取随机代理:")
    proxy = client.get_proxy(mode="random")
    if proxy:
        print(json.dumps(proxy, indent=2, ensure_ascii=False))
    
    # 验证代理
    if proxy:
        print("\n3. 验证代理:")
        proxy_url = proxy.get('proxy')
        if proxy_url:
            is_valid = client.validate_proxy(proxy_url)
            print(f"代理可用: {is_valid}")
    
    # 获取可用代理
    print("\n4. 获取可用代理:")
    available = client.get_available_proxies(count=1)
    if available:
        print(json.dumps(available, indent=2, ensure_ascii=False))
