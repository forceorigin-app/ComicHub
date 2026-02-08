"""
漫画抓取模块 V5 - SSL 优化版（简化）
功能：宽松 SSL 配置，TLS 1.0+ 支持
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
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

# 导入代理池客户端
try:
    from proxy_pool_client import ProxyPoolClient
    PROXY_POOL_AVAILABLE = True
except ImportError:
    PROXY_POOL_AVAILABLE = False

logger = logging.getLogger(__name__)


class ManhuaGuiFetcherV5:
    """漫画龟抓取器 V5 (SSL 优化版 - 简化）"""

    def __init__(self, 
                 base_url: str = "https://m.manhuagui.com",
                 use_proxy: bool = False,
                 proxy_pool_url: str = "http://localhost:5010"):
        """
        初始化抓取器
        
        Args:
            base_url: 基础 URL
            use_proxy: 是否使用代理
            proxy_pool_url: 代理池 API 地址
        """
        self.base_url = base_url
        self.use_proxy = use_proxy
        
        # 完整的浏览器请求头
        self.default_headers = {
            # 基础请求头
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            
            # 缓存控制
            'Cache-Control': 'max-age=0',
            'Pragma': 'no-cache',
            
            # 浏览器特性（Chrome）
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            
            # 其他
            'DNT': '1',  # Do Not Track
            
            # Referer（动态设置）
            'Referer': base_url
        }
        
        # 初始化代理池客户端
        self.proxy_pool_client = None
        self.current_proxy = None
        
        if use_proxy and PROXY_POOL_AVAILABLE:
            try:
                self.proxy_pool_client = ProxyPoolClient(api_url=proxy_pool_url)
                logger.info(f"代理池客户端已初始化: {proxy_pool_url}")
                # 获取一个可用代理
                proxy_data = self.proxy_pool_client.get_proxy()
                if proxy_data:
                    self.current_proxy = proxy_data.get('proxy')
                    logger.info(f"已获取代理: {self.current_proxy}")
            except Exception as e:
                logger.warning(f"代理池客户端初始化失败: {e}")
                self.use_proxy = False
        
        # 创建请求会话（使用宽松 SSL 配置）
        self.session = requests.Session()
        self.session.headers.update(self.default_headers)
        
        # 创建宽松 SSL 上下文
        ssl_context = self._create_permissive_ssl_context()
        
        # 创建重试策略
        retry_strategy = Retry(
            total=3,
            backoff_factor=2,
            status_forcelist=[500, 502, 503, 504, 520, 521, 522, 523, 524],
            allowed_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "TRACE"]
        )
        
        # 创建 SSL 适配器
        ssl_adapter = HTTPAdapter(max_retries=retry_strategy)
        
        # 设置 SSL 上下文（通过 urllib3）
        ssl_adapter.poolmanager.connection_pool_kw['https'] = {
            'ssl_context': ssl_context,
            'assert_hostname': False,
            'verify_mode': 0  # ssl.CERT_NONE
        }
        
        # 挂载适配器
        self.session.mount('https://', ssl_adapter)
        self.session.mount('http://', HTTPAdapter(max_retries=retry_strategy))
        
        # 如果使用代理，配置代理
        if self.use_proxy and self.current_proxy:
            self.session.proxies = {
                'http': self.current_proxy,
                'https': self.current_proxy
            }
            logger.info(f"会话已配置代理: {self.current_proxy}")
        
        # Cookie 管理状态
        self.cookies_loaded = False
        
        logger.info(f"抓取器已初始化 (代理: {'已启用' if self.use_proxy else '未启用'})")

    def _create_permissive_ssl_context(self):
        """创建宽松的 SSL 上下文（类似浏览器）"""
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        # 设置最小 TLS 版本（允许 TLS 1.0+）
        ctx.minimum_version = ssl.TLSVersion.TLSv1
        
        # 设置最大 TLS 版本
        ctx.maximum_version = ssl.TLSVersion.MAXIMUM_SUPPORTED
        
        # 设置加密套件（宽松设置）
        try:
            ctx.set_ciphers('DEFAULT:@SECLEVEL=1')
        except:
            pass
        
        return ctx

    def load_cookies(self, cookie_file: str = "cookies.json"):
        """从文件加载 Cookies"""
        try:
            if Path(cookie_file).exists():
                with open(cookie_file, 'r') as f:
                    cookies = json.load(f)
                    for cookie in cookies:
                        self.session.cookies.set(cookie['name'], cookie['value'], domain=cookie.get('domain'))
                    self.cookies_loaded = True
                    logger.info(f"已从文件加载 {len(cookies)} 个 cookies")
        except Exception as e:
            logger.warning(f"加载 cookies 失败: {e}")

    def save_cookies(self, cookie_file: str = "cookies.json"):
        """保存 Cookies 到文件"""
        try:
            cookies = []
            for cookie in self.session.cookies:
                cookies.append({
                    'name': cookie.name,
                    'value': cookie.value,
                    'domain': cookie.domain,
                    'path': cookie.path,
                    'expires': cookie.expires
                })
            
            with open(cookie_file, 'w') as f:
                json.dump(cookies, f, indent=2)
            
            logger.info(f"已保存 {len(cookies)} 个 cookies 到文件")
        except Exception as e:
            logger.warning(f"保存 cookies 失败: {e}")

    def _request(self, url: str, timeout: int = 30, use_proxy: Optional[bool] = None, 
                 load_cookies_first: bool = False) -> Optional[requests.Response]:
        """
        发送 HTTP 请求，可选择是否使用代理
        
        Args:
            url: 请求 URL
            timeout: 超时时间
            use_proxy: 是否使用代理（None = 使用配置默认值）
            load_cookies_first: 是否先加载 cookies
        """
        # 确定是否使用代理
        should_use_proxy = use_proxy if use_proxy is not None else self.use_proxy
        
        # 如果使用代理但当前没有代理，尝试获取
        if should_use_proxy and self.proxy_pool_client and not self.current_proxy:
            proxy_data = self.proxy_pool_client.get_proxy()
            if proxy_data:
                self.current_proxy = proxy_data.get('proxy')
                if self.current_proxy:
                    self.session.proxies = {
                        'http': self.current_proxy,
                        'https': self.current_proxy
                    }
                    logger.info(f"已配置代理: {self.current_proxy}")
                else:
                    # 如果获取代理失败，直接连接
                    should_use_proxy = False
                    self.session.proxies = {}
                    logger.warning("无法获取代理，使用直接连接")
            else:
                # 获取代理失败，直接连接
                should_use_proxy = False
                self.session.proxies = {}
                logger.warning("无法获取代理，使用直接连接")
        
        # 如果需要，先加载 cookies
        if load_cookies_first and not self.cookies_loaded:
            self.load_cookies()
        
        # 添加 Referer
        self.session.headers['Referer'] = self.base_url
        
        for attempt in range(3):
            try:
                logger.debug(f"请求 URL: {url} (尝试 {attempt + 1}/3, 代理: {'是' if should_use_proxy else '否'})")
                
                # 设置超时（更长的超时时间）
                actual_timeout = timeout if attempt == 0 else timeout * 2
                
                response = self.session.get(url, timeout=actual_timeout, verify=False)
                response.encoding = 'utf-8'
                
                # 保存 cookies（首次请求后）
                if attempt == 0 and not self.cookies_loaded:
                    self.save_cookies()
                    self.cookies_loaded = True
                
                return response
            except requests.exceptions.SSLError as e:
                logger.warning(f"SSL 错误 (尝试 {attempt + 1}/3): {e}")
                if attempt < 2:
                    time.sleep(3 * (attempt + 1))
                    continue
                else:
                    raise
            except requests.exceptions.ProxyError as e:
                logger.warning(f"代理错误 (尝试 {attempt + 1}/3): {e}")
                if should_use_proxy and attempt < 2:
                    # 代理错误，尝试切换代理
                    logger.info("代理错误，尝试切换代理...")
                    self._switch_proxy()
                    continue
                else:
                    raise
            except requests.exceptions.RequestException as e:
                logger.warning(f"请求错误 (尝试 {attempt + 1}/3): {e}")
                if should_use_proxy and attempt < 2:
                    time.sleep(3 * (attempt + 1))
                    continue
                raise
        return None

    def _request_direct(self, url: str, timeout: int = 30, 
                       load_cookies_first: bool = False) -> Optional[requests.Response]:
        """
        直接请求（不使用代理，使用宽松 SSL 配置）
        
        Args:
            url: 请求 URL
            timeout: 超时时间
            load_cookies_first: 是否先加载 cookies
        """
        # 创建新的会话，不使用代理，使用宽松 SSL 配置
        session = requests.Session()
        session.headers.update(self.default_headers)
        
        # 创建宽松 SSL 上下文
        ssl_context = self._create_permissive_ssl_context()
        
        # 创建重试策略
        retry_strategy = Retry(
            total=2,
            backoff_factor=2,
            status_forcelist=[500, 502, 503, 504]
        )
        
        # 创建适配器
        ssl_adapter = HTTPAdapter(max_retries=retry_strategy)
        
        # 设置 SSL 上下文
        ssl_adapter.poolmanager.connection_pool_kw['https'] = {
            'ssl_context': ssl_context,
            'assert_hostname': False,
            'verify_mode': 0
        }
        
        session.mount('https://', ssl_adapter)
        session.mount('http://', HTTPAdapter(max_retries=retry_strategy))
        
        # 加载 cookies
        if load_cookies_first:
            self.load_cookies()
            session.cookies.update(self.session.cookies)
        
        # 添加 Referer
        session.headers['Referer'] = self.base_url
        
        try:
            logger.debug(f"直接请求 URL: {url} (宽松 SSL 配置)")
            response = session.get(url, timeout=timeout, verify=False)
            response.encoding = 'utf-8'
            
            # 保存 cookies
            self.save_cookies()
            self.cookies_loaded = True
            
            return response
        except Exception as e:
            logger.error(f"直接请求失败: {e}")
            raise

    def _switch_proxy(self):
        """切换到新的代理"""
        if not self.proxy_pool_client:
            return
        
        logger.info("切换代理...")
        
        # 获取新代理
        proxy_data = self.proxy_pool_client.get_proxy()
        if not proxy_data:
            logger.warning("无法获取新代理")
            return
        
        new_proxy = proxy_data.get('proxy')
        if not new_proxy:
            logger.warning("新代理地址为空")
            return
        
        # 更新当前代理
        self.current_proxy = new_proxy
        self.session.proxies = {
            'http': new_proxy,
            'https': new_proxy
        }
        logger.info(f"已切换到新代理: {new_proxy}")

    def initialize_session(self, url: Optional[str] = None):
        """
        初始化会话（访问首页获取 cookies）
        
        Args:
            url: 首页 URL（None = 使用 base_url）
        """
        if url is None:
            url = self.base_url
        
        logger.info(f"初始化会话，访问: {url}")
        
        try:
            response = self._request(url, load_cookies_first=False, timeout=30)
            if response:
                logger.info(f"✅ 会话初始化成功: {response.status_code}")
                self.cookies_loaded = True
                return True
            else:
                logger.warning("❌ 会话初始化失败: 无响应")
                return False
        except Exception as e:
            logger.error(f"❌ 会话初始化异常: {e}")
            return False

    def search_comics(self, keyword: str, use_proxy: Optional[bool] = None) -> List[Dict]:
        """
        搜索漫画（先初始化会话）
        
        Args:
            keyword: 搜索关键词
            use_proxy: 是否使用代理
        """
        # 先初始化会话
        logger.info("正在初始化会话（访问首页获取 cookies）...")
        if not self.initialize_session():
            logger.warning("会话初始化失败，尝试直接搜索...")
        
        # 搜索
        search_urls = [
            urljoin(self.base_url, f"/s/{keyword}"),
            urljoin(self.base_url, f"/search/?title={keyword}"),
        ]
        
        for search_url in search_urls:
            response = self._request(search_url, use_proxy=use_proxy, load_cookies_first=True)
            if response is None:
                continue
            
            soup = BeautifulSoup(response.text, 'html.parser')
            comics = []
            
            # 查找漫画列表
            for link in soup.select('a[href*="/comic/"]'):
                href = link.get('href')
                title = link.get('title') or link.text.strip()
                
                # 提取漫画ID
                match = re.search(r'/comic/(\d+)/', href)
                if match:
                    comic_id = match.group(1)
                    comics.append({
                        'id': comic_id,
                        'name': title,
                        'url': urljoin(self.base_url, href)
                    })
            
            if comics:
                logger.info(f"搜索到 {len(comics)} 部漫画")
                return comics
        
        return []

    def get_comic_info(self, comic_url: str, use_proxy: Optional[bool] = None) -> Optional[Dict]:
        """
        获取漫画信息
        
        Args:
            comic_url: 漫画 URL
            use_proxy: 是否使用代理
        """
        # 确保会话已初始化
        if not self.cookies_loaded:
            self.initialize_session()
        
        response = self._request(comic_url, use_proxy=use_proxy, load_cookies_first=True)
        if response is None:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 查找标题
        title = soup.select_one('h1')
        comic_name = title.text.strip() if title else "未知"
        
        # 提取ID
        match = re.search(r'/comic/(\d+)/', comic_url)
        comic_id = match.group(1) if match else None
        
        return {
            'id': comic_id,
            'name': comic_name,
            'url': comic_url
        }

    def get_chapters(self, comic_url: str, use_proxy: Optional[bool] = None) -> List[Dict]:
        """获取章节列表"""
        # 确保会话已初始化
        if not self.cookies_loaded:
            self.initialize_session()
        
        response = self._request(comic_url, use_proxy=use_proxy, load_cookies_first=True)
        if response is None:
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        chapters = []
        
        # 查找章节链接
        for link in soup.select('a[href*="/comic/"]'):
            href = link.get('href')
            match = re.search(r'/(\d+)\.html?$', href)
            if match:
                chapter_num = match.group(1)
                chapters.append({
                    'chapter_num': chapter_num,
                    'title': link.text.strip(),
                    'url': urljoin(self.base_url, href)
                })
        
        logger.info(f"获取到 {len(chapters)} 个章节")
        return chapters

    def get_images(self, chapter_url: str, use_proxy: Optional[bool] = None) -> List[str]:
        """获取章节图片列表"""
        # 确保会话已初始化
        if not self.cookies_loaded:
            self.initialize_session()
        
        response = self._request(chapter_url, use_proxy=use_proxy, load_cookies_first=True)
        if response is None:
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        images = []
        
        # 查找所有图片
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src') or img.get('data-original')
            if src and ('jpg' in src or 'png' in src or 'jpeg' in src or 'webp' in src):
                images.append(src)
        
        # 去重
        images = list(set(images))
        logger.info(f"获取到 {len(images)} 张图片")
        return images

    def download_image(self, url: str, save_path: str, use_proxy: Optional[bool] = None) -> bool:
        """下载图片"""
        try:
            response = self._request(url, use_proxy=use_proxy, load_cookies_first=True)
            if response is None:
                return False
            
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(save_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"下载图片成功: {save_path}")
            return True
        except Exception as e:
            logger.error(f"下载图片失败: {url}, 错误: {e}")
            return False
    
    def search_comics_direct(self, keyword: str) -> List[Dict]:
        """
        直接搜索（不使用代理）
        
        Args:
            keyword: 搜索关键词
        """
        return self.search_comics(keyword, use_proxy=False)
    
    def get_comic_info_direct(self, comic_url: str) -> Optional[Dict]:
        """
        直接获取漫画信息（不使用代理）
        
        Args:
            comic_url: 漫画 URL
        """
        return self.get_comic_info(comic_url, use_proxy=False)


def create_fetcher_v5(use_proxy: bool = False, 
                     proxy_pool_url: str = "http://localhost:5010") -> ManhuaGuiFetcherV5:
    """
    创建漫画抓取器实例 V5
    
    Args:
        use_proxy: 是否使用代理
        proxy_pool_url: 代理池 API 地址
        
    Returns:
        ManhuaGuiFetcherV5 实例
    """
    return ManhuaGuiFetcherV5(
        use_proxy=use_proxy,
        proxy_pool_url=proxy_pool_url
    )


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    print("=== 测试漫画抓取器 V5 (SSL 优化版 - 简化）===")
    
    # 测试 1: 直接连接（宽松 SSL 配置）
    print("\n测试 1: 直接连接（宽松 SSL 配置 - TLS 1.0+）")
    print("-" * 50)
    try:
        fetcher = create_fetcher_v5(use_proxy=False)
        
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
        else:
            print("❌ 漫画页连接失败")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
