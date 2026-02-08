#!/bin/bash

set -e

echo "============================================="
echo "ChromeDriver 修复脚本"
echo "============================================="
echo ""

echo "步骤 1: 检查 brew 状态"
echo "-----------------------------------"
brew list chromedriver 2>/dev/null || echo "ChromeDriver 未在 brew 中"

echo ""
echo "步骤 2: 检查实际安装位置"
echo "-----------------------------------"
if [ -d "$(brew --prefix)/opt/chromedriver" ]; then
    echo "brew Cellar 路径: $(brew --prefix)/opt/chromedriver"
    ls -lh "$(brew --prefix)/opt/chromedriver/" 2>/dev/null | head -10
elif [ -d "$(brew --prefix)/Caskroom/chromedriver" ]; then
    echo "Caskroom 路径: $(brew --prefix)/Caskroom/chromedriver"
    ls -lh "$(brew --prefix)/Caskroom/chromedriver/" 2>/dev/null | head -10
else
    echo "未找到 brew 安装位置"
fi

echo ""
echo "步骤 3: 检查符号链接"
echo "-----------------------------------"
if [ -L "/usr/local/bin/chromedriver" ]; then
    echo "符号链接存在: /usr/local/bin/chromedriver"
    ls -l /usr/local/bin/chromedriver
    
    # 检查符号链接指向
    if readlink -f /usr/local/bin/chromedriver &>/dev/null; then
        REAL_PATH=$(readlink -f /usr/local/bin/chromedriver)
        echo "真实路径: $REAL_PATH"
        
        # 检查真实文件是否存在
        if [ -f "$REAL_PATH" ]; then
            echo "真实文件存在: ✅"
        else
            echo "真实文件不存在: ❌ (这就是问题！)"
        fi
    fi
else
    echo "符号链接不存在或不是符号链接"
fi

echo ""
echo "步骤 4: 检查所有可能的 ChromeDriver 位置"
echo "-----------------------------------"
for path in /usr/local/bin/chromedriver /opt/homebrew/bin/chromedriver "$(brew --prefix)/bin/chromedriver" "$(brew --prefix)/opt/chromedriver/chromedriver" "$(brew --prefix)/Caskroom/chromedriver/chromedriver/chromedriver"; do
    if [ -e "$path" ]; then
        echo "存在: $path"
        file "$path"
    fi
done

echo ""
echo "步骤 5: 重新安装 ChromeDriver 144"
echo "-----------------------------------"
echo "卸载旧版本..."
brew uninstall chromedriver 2>/dev/null || echo "卸载失败或未安装"

echo ""
echo "安装新版本..."
brew install chromedriver@144

echo ""
echo "步骤 6: 验证安装"
echo "-----------------------------------"
if command -v chromedriver &>/dev/null; then
    echo "✅ chromedriver 命令可用"
    chromedriver --version
else
    echo "❌ chromedriver 命令不可用"
fi

echo ""
echo "============================================="
echo "修复完成！"
echo "============================================="
echo ""
echo "如果 chromedriver --version 成功，我们可以继续测试 Selenium"
echo ""
