#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
IAM Agents 所有服务一键启动脚本
支持同时启动企业内部数据Agent、飞书文档Agent、外部检索Agent三个核心服务
兼容Windows/Linux/macOS
"""
import os
import sys
import time
import signal
import subprocess
from typing import List, Dict

# 解决Windows控制台中文编码问题
if sys.platform.startswith('win'):
    import ctypes
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleOutputCP(65001)  # 设置控制台输出编码为UTF-8
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# 模块配置
MODULES = [
    {
        "name": "企业内部数据Agent",
        "dir": "Agent_indata",
        "port": 9300,
        "entry_file": "app.py",
        "health_check": "/health",
        "description": "负责访问和处理企业内部敏感数据，访问地址: http://localhost:9300"
    },
    {
        "name": "飞书文档Agent",
        "dir": "Lark-doc-Agent",
        "port": 9100,
        "entry_file": "main.py",
        "health_check": "/health",
        "description": "提供飞书云文档全生命周期管理能力，前端地址: http://localhost:9100"
    },
    {
        "name": "外部检索Agent",
        "dir": "web_search",
        "port": 9200,
        "entry_file": "server.py",
        "health_check": "/health",
        "description": "提供外部公开信息检索服务，前端地址: http://localhost:9200"
    }
]

processes: List[subprocess.Popen] = []

def signal_handler(signum, frame):
    """捕获终止信号，停止所有子进程"""
    print("\n\n收到停止信号，正在关闭所有Agent服务...")
    for p in processes:
        if p.poll() is None:  # 进程仍在运行
            p.terminate()
            p.wait()
    print("所有Agent服务已停止，退出成功")
    sys.exit(0)

def run_module(module_config: Dict) -> subprocess.Popen:
    """启动单个Agent模块，使用独立子进程"""
    project_root = os.path.dirname(os.path.abspath(__file__))
    module_dir = os.path.join(project_root, module_config["dir"])
    entry_path = os.path.join(module_dir, module_config["entry_file"])
    
    # 设置环境变量，确保编码为UTF-8
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    
    try:
        # 启动独立Python进程，工作目录为对应Agent目录
        process = subprocess.Popen(
            [sys.executable, entry_path],
            cwd=module_dir,
            env=env,
            text=True,
            encoding='utf-8'
        )
        return process
    except Exception as e:
        import traceback
        print(f"❌ {module_config['name']} 启动失败: {str(e)}", file=sys.stderr)
        print("详细错误信息:", traceback.format_exc(), file=sys.stderr)
        return None

def main():
    print("=" * 60)
    print("IAM Agents 一键启动脚本")
    print("=" * 60)
    print(f"共有 {len(MODULES)} 个核心Agent待启动\n")
    print("⚠️  注意：请确保已先启动IAMsystem服务，所有Agent依赖IAM系统认证\n")

    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 启动所有模块
    for module in MODULES:
        process = run_module(module)
        if process:
            processes.append(process)
            time.sleep(2)  # 间隔启动避免端口冲突和日志混乱
            # 检查进程是否正常运行
            if process.poll() is None:
                print(f"✅ {module['name']} 启动成功")
                print(f"   访问地址: http://localhost:{module['port']}")
                print(f"   健康检查: http://localhost:{module['port']}{module['health_check']}")
                print(f"   描述: {module['description']}\n")
            else:
                print(f"❌ {module['name']} 启动失败，进程已退出，退出码: {process.returncode}\n")
        else:
            print(f"❌ {module['name']} 启动失败，无法创建进程\n")

    print("\n" + "=" * 60)
    print("所有Agent服务已启动完成，按 Ctrl+C 停止所有服务")
    print("=" * 60 + "\n")

    # 等待所有进程结束
    try:
        for p in processes:
            if p.poll() is None:
                p.wait()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
