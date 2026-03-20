@echo off
REM Force UTF-8 to avoid garbled Chinese output in cmd
chcp 65001 >nul
setlocal EnableExtensions

REM Windows环境一键启动脚本
REM 自动创建虚拟环境、安装依赖并启动AI股票分析系统

color 0A

REM 获取脚本所在目录
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

echo =====================================
echo AI股票分析系统一键启动脚本
echo =====================================
echo.

REM 1. 检查Python 3是否安装
echo 1. 检查Python 3是否安装...
python --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo [OK] Python 3已安装: %PYTHON_VERSION%
) else (
    echo [ERROR] Python 3未安装，请先安装Python 3.8或更高版本
    pause
    exit /b 1
)

REM 2. 检查pip是否安装
echo 2. 检查pip是否安装...
pip --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=2" %%i in ('pip --version 2^>^&1') do set PIP_VERSION=%%i
    echo [OK] pip已安装: %PIP_VERSION%
) else (
    echo pip未安装，尝试安装...
    python -m ensurepip --upgrade
    echo [OK] pip安装成功
)

REM 3. 检查虚拟环境是否存在，不存在则创建
echo 3. 检查虚拟环境是否存在...
set VENV_DIR=%SCRIPT_DIR%venv
if exist "%VENV_DIR%" (
    echo [OK] 虚拟环境已存在: %VENV_DIR%
) else (
    echo 虚拟环境不存在，正在创建...
    python -m venv "%VENV_DIR%"
    if %errorlevel% equ 0 (
        echo [OK] 虚拟环境创建成功: %VENV_DIR%
    ) else (
        echo [ERROR] 虚拟环境创建失败
        pause
        exit /b 1
    )
)

REM 4. 激活虚拟环境
echo 4. 激活虚拟环境...
call "%VENV_DIR%\Scripts\activate"
if %errorlevel% neq 0 (
    echo [ERROR] 虚拟环境激活失败
    pause
    exit /b 1
)
echo [OK] 虚拟环境已激活

REM 5. 升级pip
echo 5. 升级pip...
pip install --upgrade pip >nul 2>&1
echo [OK] pip升级完成

REM 6. 检查Chrome/Edge浏览器（用于PDF生成）
echo 6. 检查浏览器（用于PDF生成）...
set BROWSER_FOUND=0
REM 检查Chrome
reg query "HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon" /v version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=2" %%i in ('reg query "HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon" /v version 2^>nul') do set CHROME_VERSION=%%i
    echo [OK] Chrome已安装: %CHROME_VERSION%
    set BROWSER_FOUND=1
)
REM 检查Edge
if %BROWSER_FOUND% equ 0 (
    reg query "HKEY_CURRENT_USER\Software\Microsoft\Edge\BLBeacon" /v version >nul 2>&1
    if %errorlevel% equ 0 (
        for /f "tokens=2" %%i in ('reg query "HKEY_CURRENT_USER\Software\Microsoft\Edge\BLBeacon" /v version 2^>nul') do set EDGE_VERSION=%%i
        echo [OK] Edge已安装: %EDGE_VERSION%
        set BROWSER_FOUND=1
    )
)
if %BROWSER_FOUND% equ 0 (
    echo [WARN] 未检测到Chrome或Edge浏览器，PDF生成功能可能受限
)

REM 7. 安装Python依赖
echo 7. 检查并安装Python依赖...
if exist "%SCRIPT_DIR%requirements.txt" (
    pip install -r "%SCRIPT_DIR%requirements.txt" -q
    if %errorlevel% equ 0 (
        echo [OK] Python依赖安装完成
    ) else (
        echo [ERROR] Python依赖安装失败
        pause
        exit /b 1
    )
) else (
    echo [ERROR] requirements.txt文件未找到
    pause
    exit /b 1
)

REM 8. 检查.env配置文件
echo 8. 检查配置文件...
if not exist "%SCRIPT_DIR%.env" (
    echo [WARN] .env文件不存在，请确保已配置API密钥
    if exist "%SCRIPT_DIR%.env.example" (
        echo       可以复制 .env.example 为 .env 并填入配置
    )
)

REM 9. 启动应用
echo.
echo =====================================
echo 环境配置完成，正在启动应用...
echo =====================================
echo 访问地址: http://localhost:8503
echo 按 Ctrl+C 停止应用
echo.

REM 使用streamlit运行应用
cd /d "%SCRIPT_DIR%"
streamlit run app.py --server.port 8503 --server.address 0.0.0.0