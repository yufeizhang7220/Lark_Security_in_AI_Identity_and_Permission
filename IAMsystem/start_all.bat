@echo off
chcp 65001 >nul
title IAM系统一键启动
echo ==================================================
echo IAM系统 一键启动脚本
echo ==================================================
echo.

cd /d "%~dp0"

echo 正在启动所有IAM核心模块...
echo.

python start_all.py

pause
