#!/bin/bash

# 检查Python环境
if ! command -v python &> /dev/null; then
    echo "错误: 未找到Python，请安装Python后再试"
    exit 1
fi

# 检查pip
if ! command -v pip &> /dev/null; then
    echo "错误: 未找到pip，请安装pip后再试"
    exit 1
fi

# 安装依赖
echo "正在安装依赖..."
pip install -r requirements.txt

# 启动服务器
echo "正在启动API服务器..."
python api_server.py