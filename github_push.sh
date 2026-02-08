#!/bin/bash

# ComicHub GitHub 仓库创建和推送脚本

echo "========================================"
echo "ComicHub GitHub 仓库创建和推送"
echo "========================================"
echo ""

# 项目配置
REPO_NAME="ComicHub"
DESCRIPTION="ComicHub - 漫画抓取系统，支持代理池和 PostgreSQL 数据库"
VISIBILITY="public"

echo "📋 仓库配置："
echo "  仓库名称: $REPO_NAME"
echo "  描述: $DESCRIPTION"
echo "  可见性: $VISIBILITY"
echo ""

# 检查 gh 登录状态
echo "🔐 检查 GitHub 登录状态..."
if gh auth status &>/dev/null; then
    echo "✅ 已登录到 GitHub"
    gh auth status
else
    echo "❌ 未登录到 GitHub"
    echo ""
    echo "请先登录："
    echo "  gh auth login"
    echo ""
    echo "登录后再次运行此脚本"
    exit 1
fi

echo ""
echo "🚀 开始创建仓库..."
echo ""

# 创建仓库
echo "📦 创建 GitHub 仓库..."
gh repo create "$REPO_NAME" \
    --description "$DESCRIPTION" \
    --visibility "$VISIBILITY" \
    --source=. \
    --remote=origin \
    --push

echo ""
echo "✅ 仓库创建并推送完成！"
echo ""

# 显示仓库信息
echo "📊 仓库信息："
gh repo view

echo ""
echo "🔗 仓库链接："
gh repo view --json url --jq '.url'

echo ""
echo "========================================"
echo "🎉 完成！"
echo "========================================"
