# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2026-02-10

### Added
- 引入标准 Python 包结构 (`comichub/`)
- 添加 `.gitignore` 防止虚拟环境和日志文件被提交
- 添加 `docs/` 目录用于存放分析报告和文档

### Changed
- **架构重组**：将核心代码从根目录移入 `comichub/` 包
    - `config_loader.py` -> `comichub/core/config.py`
    - `database.py` -> `comichub/core/database.py`
    - `fetcher_selenium.py` -> `comichub/core/fetcher.py`
    - `batch_download.py` -> `comichub/downloader/batch.py`
    - `info_txt_generator.py` -> `comichub/utils/info.py`
- 更新所有 `import` 语句以适应新包结构
- 将独立辅助脚本移至 `scripts/` 目录

### Removed
- 删除根目录下 60+ 个历史版本文件 (fetcher_v1-v8, download_*, test_*, etc.)
- 删除根目录下的所有分析报告 `.md` 文件 (已移至 `docs/`)

### Fixed
- 清理 Git 历史 (13,764 行代码)，移除 `.venv` 和 `__pycache__` 以减小仓库体积
