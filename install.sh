#!/bin/bash
#
# Kimi Autoresearch 安装脚本
# Usage: ./install.sh [target_directory]
#

set -e

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 默认安装目录
DEFAULT_TARGET=".agents/skills/kimi-autoresearch"
TARGET_DIR="${1:-$DEFAULT_TARGET}"

echo -e "${GREEN}Installing Kimi Autoresearch...${NC}"
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is required but not installed.${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $PYTHON_VERSION"

# 检查 Git
if ! command -v git &> /dev/null; then
    echo -e "${RED}Error: Git is required but not installed.${NC}"
    exit 1
fi

echo "✓ Git is available"

# 创建目录
echo ""
echo "Creating directory: $TARGET_DIR"
mkdir -p "$TARGET_DIR"

# 复制文件
echo "Copying files..."
cp -r scripts references examples .github "$TARGET_DIR/" 2>/dev/null || true
cp README.md LICENSE CHANGELOG.md CONTRIBUTING.md "$TARGET_DIR/" 2>/dev/null || true
cp -r .agents/skills/kimi-autoresearch/* "$TARGET_DIR/" 2>/dev/null || true

# 设置权限
echo "Setting permissions..."
chmod +x "$TARGET_DIR/scripts/"*.py 2>/dev/null || true

# 验证安装
echo ""
echo "Verifying installation..."
if [ -f "$TARGET_DIR/scripts/autoresearch_main.py" ]; then
    echo -e "${GREEN}✓ Installation successful!${NC}"
    echo ""
    echo "Installed to: $TARGET_DIR"
    echo ""
    echo "Quick start:"
    echo "  python $TARGET_DIR/scripts/autoresearch_main.py --help"
    echo ""
    echo "Or in Kimi:"
    echo "  \$kimi-autoresearch"
else
    echo -e "${RED}✗ Installation may have failed.${NC}"
    echo "Please check the target directory."
    exit 1
fi

# 添加到 PATH (可选)
echo ""
read -p "Add to PATH? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    SHELL_RC=""
    if [ -f "$HOME/.bashrc" ]; then
        SHELL_RC="$HOME/.bashrc"
    elif [ -f "$HOME/.zshrc" ]; then
        SHELL_RC="$HOME/.zshrc"
    fi
    
    if [ -n "$SHELL_RC" ]; then
        echo "export PATH=\"\$PATH:$(pwd)/$TARGET_DIR/scripts\"" >> "$SHELL_RC"
        echo -e "${GREEN}✓ Added to $SHELL_RC${NC}"
        echo "Please restart your shell or run: source $SHELL_RC"
    fi
fi

echo ""
echo -e "${GREEN}Installation complete!${NC}"
