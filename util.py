"""
工具模块
包含日志配置和文件操作
"""

import os
import logging
from typing import Optional
from pathlib import Path


def setup_logging(config: dict) -> logging.Logger:
    """
    配置日志

    Args:
        config: 配置字典

    Returns:
        Logger 对象
    """
    level_str = config.get('Logging', {}).get('level', 'INFO')
    log_file = config.get('Logging', {}).get('file', 'comichub.log')

    # 映射日志级别
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR
    }
    level = level_map.get(level_str, logging.INFO)

    # 配置日志格式
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

    return logging.getLogger('ComicHub')


def ensure_dir(path: str) -> Path:
    """
    确保目录存在

    Args:
        path: 目录路径

    Returns:
        Path 对象
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def save_info_txt(comic_name: str, comic_info: dict, save_path: str):
    """
    保存漫画信息到 info.txt

    Args:
        comic_name: 漫画名称
        comic_info: 漫画信息字典
        save_path: 保存路径
    """
    info_file = Path(save_path) / comic_name / 'info.txt'
    
    content = f"""名称：{comic_info.get('name', 'N/A')}
URL：{comic_info.get('url', 'N/A')}
描述：{comic_info.get('description', 'N/A')}
创建时间：{comic_info.get('created_at', 'N/A')}
最后更新：{comic_info.get('updated_at', 'N/A')}
章节数量：{comic_info.get('chapter_count', 0)}
已抓取章节：{', '.join(comic_info.get('fetched_chapters', []))}
"""
    
    with open(info_file, 'w', encoding='utf-8') as f:
        f.write(content)


def sanitize_filename(name: str) -> str:
    """
    清理文件名，移除非法字符

    Args:
        name: 原始文件名

    Returns:
        清理后的文件名
    """
    # 移除 Windows 文件名中的非法字符
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, '_')
    
    return name.strip()
