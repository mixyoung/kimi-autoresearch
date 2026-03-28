#!/bin/bash
#
# Kimi Autoresearch 打包脚本
# 生成 .skill 文件用于分发
#

set -e

VERSION="1.2.3"
PACKAGE_NAME="kimi-autoresearch"
OUTPUT_DIR="dist"

echo "Packaging Kimi Autoresearch v$VERSION..."
echo ""

# 创建输出目录
mkdir -p "$OUTPUT_DIR"

# 清理旧文件
rm -f "$OUTPUT_DIR/${PACKAGE_NAME}-${VERSION}.skill"
rm -f "$OUTPUT_DIR/${PACKAGE_NAME}-latest.skill"

# 创建临时目录
TMP_DIR=$(mktemp -d)
trap "rm -rf $TMP_DIR" EXIT

# 复制文件到临时目录
echo "Copying files..."
mkdir -p "$TMP_DIR/$PACKAGE_NAME"

cp -r scripts references examples .github "$TMP_DIR/$PACKAGE_NAME/"
cp README.md LICENSE CHANGELOG.md CONTRIBUTING.md SKILL.md "$TMP_DIR/$PACKAGE_NAME/"
cp -n GAP_ANALYSIS.md COMPLETION_REPORT.md "$TMP_DIR/$PACKAGE_NAME/" 2>/dev/null || true

# 设置权限
chmod +x "$TMP_DIR/$PACKAGE_NAME/scripts/"*.py
chmod +x "$TMP_DIR/$PACKAGE_NAME/install.sh"

# 创建 .skill 文件 (zip 格式)
echo "Creating .skill package..."
cd "$TMP_DIR"
zip -r "${PACKAGE_NAME}-${VERSION}.skill" "$PACKAGE_NAME" -x "*.pyc" -x "__pycache__/*" -x "*.git*"

# 复制到输出目录
cp "${PACKAGE_NAME}-${VERSION}.skill" "$OUTPUT_DIR/"
cp "${PACKAGE_NAME}-${VERSION}.skill" "$OUTPUT_DIR/${PACKAGE_NAME}-latest.skill"

# 计算校验和
cd "$OUTPUT_DIR"
shasum -a 256 "${PACKAGE_NAME}-${VERSION}.skill" > "${PACKAGE_NAME}-${VERSION}.sha256"

echo ""
echo "✓ Package created successfully!"
echo ""
echo "Output files:"
ls -lh "$OUTPUT_DIR/"
echo ""
echo "Checksum:"
cat "$OUTPUT_DIR/${PACKAGE_NAME}-${VERSION}.sha256"
echo ""
echo "Install with:"
echo "  unzip $OUTPUT_DIR/${PACKAGE_NAME}-${VERSION}.skill -d ~/.agents/skills/"
