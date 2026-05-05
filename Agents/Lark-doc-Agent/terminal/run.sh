#!/bin/bash

# 启动脚本 - run.sh
# 运行飞书文档助手命令行工具

echo "=== 飞书文档助手 - 命令行工具 ==="
echo ""
echo "1. 安装依赖..."
pip install -r ../requirements.txt

echo ""
echo "2. 启动命令行工具..."
python cli.py
