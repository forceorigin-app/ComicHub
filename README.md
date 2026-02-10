# ComicHub

一个基于 Python 和 Selenium 的漫画下载与管理工具，专为漫画鸟网站设计。

## ✨ 特性

- **全站抓取**：支持批量抓取漫画列表
- **断点续传**：基于数据库管理下载状态，支持中断后继续
- **多线程下载**：利用线程池加速图片下载
- **Telegram 通知**：支持下载完成后的消息推送
- **数据持久化**：使用 PostgreSQL 存储漫画元数据

## 🚀 快速开始

### 环境准备

1.  **安装依赖**
    ```bash
    pip install -r requirements.txt
    ```

2.  **配置文件**
    复制并编辑 `config.yaml`，填入你的数据库信息和 Telegram Bot Token。

3.  **运行程序**
    ```bash
    python cli.py
    ```

    你会看到一个交互式命令行界面，可以选择不同的抓取模式。

## 📂 项目结构

本项目采用标准的 Python 包结构，核心逻辑已模块化：

```
ComicHub/
├── cli.py                 # 程序主入口 (CLI 界面)
├── config.yaml            # 配置文件
├── requirements.txt       # Python 依赖列表
├── comichub/               # 核心代码包
│   ├── core/              # 核心业务逻辑
│   │   ├── fetcher.py     # 漫画列表/章节抓取 (Selenium)
│   │   ├── database.py    # 数据库操作
│   │   └── config.py      # 配置加载
│   ├── downloader/        # 下载模块
│   │   └── batch.py       # 批量下载逻辑
│   └── utils/             # 工具函数
│       └── info.py        # Info.txt 生成器
├── scripts/               # 独立辅助脚本
│   ├── analyze_chapter.py # 章节分析工具
│   └── diagnose_ssl.py    # SSL 诊断工具
└── docs/                  # 项目文档与分析报告
```

## 🛠️ 开发指南

### 核心类说明

- `ManhuaGuiFetcherSelenium` (`comichub/core/fetcher.py`): 使用 Selenium 驱动浏览器，处理动态加载的漫画页面。
- `BatchDownloader` (`comichub/downloader/batch.py`): 多线程下载管理器，负责并发下载图片。
- `Database` (`comichub/core/database.py`): 封装所有数据库操作，提供统一的查询接口。

### 添加新功能

如果需要添加新的解析逻辑或下载策略，建议在 `comichub/core/` 或 `comichub/downloader/` 下创建新模块，并在 `cli.py` 中引入。

## 📄 许可证

MIT License
