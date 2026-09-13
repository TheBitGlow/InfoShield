@echo off
chcp 65001 > nul
title InfoShield 启动中...

echo ========================================================
echo        InfoShield - 离线轻量化脱敏工具
echo ========================================================
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python 环境，请先安装 Python 3.8 或更高版本。
    pause
    exit /b
)

echo [1/2] 正在检查依赖...
python -c "import PySide6, docx, openpyxl" >nul 2>nul
if %errorlevel% neq 0 (
    echo 正在安装必要依赖包...
    python -m pip install -r requirements.txt
)

echo [2/2] 正在启动程序...
start "" pythonw main.py
if %errorlevel% neq 0 (
    python main.py
)

exit
