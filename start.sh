#!/usr/bin/env bash
# AI股票分析系统 - 一键启动
# 用法: 在任意目录执行 stock 即可启动

PROJECT_DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
cd "$PROJECT_DIR"

# 激活虚拟环境
source "$PROJECT_DIR/venv/bin/activate"

# 启动
exec python run.py "$@"
