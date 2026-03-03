#!/bin/bash

# Linux环境一键启动脚本
# 自动创建虚拟环境、安装依赖并启动AI股票分析系统

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}AI股票分析系统一键启动脚本${NC}"
echo -e "${GREEN}=====================================${NC}"

# 1. 检查Python 3是否安装
echo -e "${YELLOW}1. 检查Python 3是否安装...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    echo -e "${GREEN}✓ Python 3已安装: $PYTHON_VERSION${NC}"
else
    echo -e "${RED}✗ Python 3未安装，请先安装Python 3.8或更高版本${NC}"
    exit 1
fi

# 2. 检查pip是否安装
echo -e "${YELLOW}2. 检查pip是否安装...${NC}"
if command -v pip3 &> /dev/null; then
    PIP_VERSION=$(pip3 --version 2>&1 | awk '{print $2}')
    echo -e "${GREEN}✓ pip已安装: $PIP_VERSION${NC}"
else
    echo -e "${YELLOW}pip未安装，尝试安装...${NC}"
    python3 -m ensurepip --upgrade
    echo -e "${GREEN}✓ pip安装成功${NC}"
fi

# 3. 检查虚拟环境是否存在，不存在则创建
echo -e "${YELLOW}3. 检查虚拟环境是否存在...${NC}"
VENV_DIR="$SCRIPT_DIR/venv"
if [ -d "$VENV_DIR" ]; then
    echo -e "${GREEN}✓ 虚拟环境已存在: $VENV_DIR${NC}"
else
    echo -e "${YELLOW}虚拟环境不存在，正在创建...${NC}"
    python3 -m venv "$VENV_DIR"
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ 虚拟环境创建成功: $VENV_DIR${NC}"
    else
        echo -e "${RED}✗ 虚拟环境创建失败${NC}"
        exit 1
    fi
fi

# 4. 激活虚拟环境
echo -e "${YELLOW}4. 激活虚拟环境...${NC}"
source "$VENV_DIR/bin/activate"
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ 虚拟环境激活失败${NC}"
    exit 1
fi
echo -e "${GREEN}✓ 虚拟环境已激活${NC}"

# 5. 升级pip
echo -e "${YELLOW}5. 升级pip...${NC}"
pip install --upgrade pip -q

# 6. 检查并安装chromium-browser（用于PDF生成）
echo -e "${YELLOW}6. 检查chromium-browser是否安装...${NC}"
if command -v chromium-browser &> /dev/null; then
    echo -e "${GREEN}✓ chromium-browser已安装${NC}"
else
    echo -e "${YELLOW}chromium-browser未安装，正在安装（需要sudo权限）...${NC}"
    sudo apt-get update -qq
    sudo apt-get install -y chromium-browser
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ chromium-browser安装成功${NC}"
    else
        echo -e "${YELLOW}! chromium-browser安装失败，PDF生成功能可能受限${NC}"
    fi
fi

# 7. 安装Python依赖
echo -e "${YELLOW}7. 检查并安装Python依赖...${NC}"
if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    pip install -r "$SCRIPT_DIR/requirements.txt" -q
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Python依赖安装完成${NC}"
    else
        echo -e "${RED}✗ Python依赖安装失败${NC}"
        exit 1
    fi
else
    echo -e "${RED}✗ requirements.txt文件未找到${NC}"
    exit 1
fi

# 8. 检查.env配置文件
echo -e "${YELLOW}8. 检查配置文件...${NC}"
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo -e "${YELLOW}! .env文件不存在，请确保已配置API密钥${NC}"
    if [ -f "$SCRIPT_DIR/.env.example" ]; then
        echo -e "${YELLOW}  可以复制 .env.example 为 .env 并填入配置${NC}"
    fi
fi

# 9. 启动应用
echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}环境配置完成，正在启动应用...${NC}"
echo -e "${GREEN}=====================================${NC}"
echo -e "${YELLOW}访问地址: http://localhost:8503${NC}"
echo -e "${YELLOW}按 Ctrl+C 停止应用${NC}"
echo ""

# 使用streamlit运行应用
cd "$SCRIPT_DIR"
streamlit run app.py --server.port 8503 --server.address 0.0.0.0
