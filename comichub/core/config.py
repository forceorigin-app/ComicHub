"""
配置加载模块
负责加载和解析 YAML 配置文件
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class Config:
    """配置类"""

    def __init__(self, config_path: str = "config.yaml"):
        """
        初始化配置

        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info(f"配置文件加载成功: {self.config_path}")
            return config or {}
        except FileNotFoundError:
            logger.warning(f"配置文件不存在: {self.config_path}，使用默认配置")
            return self._get_default_config()
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'save_path': '~/data/comics',
            'database': {
                'host': 'localhost',
                'port': 5432,
                'database': 'comichub',
                'user': 'postgres',
                'password': 'postgres'
            },
            'fetch': {
                'concurrent_downloads': 5,
                'delay': 1,
                'retry': 3,
                'timeout': 30
            },
            'logging': {
                'level': 'INFO',
                'file': 'comichub.log'
            },
            'proxy_pool_service': {
                'url': 'http://localhost:5010',
                'enabled': False
            }
        }

    def get_save_path(self) -> Path:
        """
        获取保存路径（支持 ~ 展开）

        Returns:
            保存路径 Path 对象
        """
        save_path = self.config.get('save_path', '~/data/comics')
        # 展开 ~ 符号
        expanded_path = Path(save_path).expanduser()
        # 确保目录存在
        expanded_path.mkdir(parents=True, exist_ok=True)
        return expanded_path

    def get_database_config(self) -> Dict[str, Any]:
        """
        获取数据库配置

        Returns:
            数据库配置字典
        """
        return self.config.get('database', {})

    def get_fetch_config(self) -> Dict[str, Any]:
        """
        获取抓取配置

        Returns:
            抓取配置字典
        """
        return self.config.get('fetch', {})

    def get_logging_config(self) -> Dict[str, Any]:
        """
        获取日志配置

        Returns:
            日志配置字典
        """
        return self.config.get('logging', {})

    def get_proxy_config(self) -> Dict[str, Any]:
        """
        获取代理配置

        Returns:
            代理配置字典
        """
        return self.config.get('proxy_pool_service', {})

    def is_proxy_enabled(self) -> bool:
        """
        检查是否启用代理

        Returns:
            是否启用代理
        """
        proxy_config = self.get_proxy_config()
        return proxy_config.get('enabled', False)

    def get_proxy_url(self) -> str:
        """
        获取代理池 URL

        Returns:
            代理池 URL
        """
        proxy_config = self.get_proxy_config()
        return proxy_config.get('url', 'http://localhost:5010')

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项

        Args:
            key: 配置键（支持点号分隔的路径，如 'database.host'）
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default


# 全局配置实例
_config = None


def get_config(config_path: str = "config.yaml") -> Config:
    """
    获取全局配置实例

    Args:
        config_path: 配置文件路径

    Returns:
        Config 实例
    """
    global _config
    if _config is None:
        _config = Config(config_path)
    return _config


def reload_config(config_path: str = "config.yaml"):
    """
    重新加载配置

    Args:
        config_path: 配置文件路径
    """
    global _config
    _config = Config(config_path)
    logger.info("配置已重新加载")


if __name__ == "__main__":
    # 测试配置加载
    logging.basicConfig(level=logging.INFO)
    config = get_config()

    print("="*80)
    print("配置加载测试")
    print("="*80)
    print(f"保存路径: {config.get_save_path()}")
    print(f"数据库配置: {config.get_database_config()}")
    print(f"抓取配置: {config.get_fetch_config()}")
    print(f"日志配置: {config.get_logging_config()}")
    print(f"代理启用: {config.is_proxy_enabled()}")
    print(f"代理 URL: {config.get_proxy_url()}")
    print("="*80)
