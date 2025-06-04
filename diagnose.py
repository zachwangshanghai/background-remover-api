#!/usr/bin/env python3
"""
诊断脚本 - 检查环境和依赖
"""

import os
import sys
import platform
import subprocess
import importlib.util
from pathlib import Path

def print_header(title):
    """打印带格式的标题"""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)

def check_module(module_name):
    """检查模块是否已安装"""
    spec = importlib.util.find_spec(module_name)
    if spec is not None:
        try:
            module = importlib.import_module(module_name)
            version = getattr(module, "__version__", "未知")
            return True, version
        except ImportError:
            return False, "导入失败"
    return False, "未找到"

def run_command(command):
    """运行命令并返回输出"""
    try:
        result = subprocess.run(
            command, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True,
            shell=True
        )
        return result.stdout.strip()
    except Exception as e:
        return f"错误: {str(e)}"

def main():
    print_header("系统信息")
    print(f"操作系统: {platform.system()} {platform.release()} ({platform.version()})")
    print(f"Python版本: {sys.version}")
    print(f"Python路径: {sys.executable}")
    
    print_header("依赖检查")
    
    # 检查关键依赖
    dependencies = ["rembg", "PIL", "numpy", "torch", "onnxruntime"]
    for dep in dependencies:
        installed, version = check_module(dep)
        status = f"已安装 (版本: {version})" if installed else "未安装"
        print(f"{dep}: {status}")
    
    # 检查PIL/Pillow
    try:
        from PIL import Image, __version__ as pil_version
        print(f"Pillow版本: {pil_version}")
    except ImportError:
        print("Pillow: 未安装或导入失败")
    
    print_header("rembg详细信息")
    
    # 检查rembg
    if importlib.util.find_spec("rembg") is not None:
        try:
            from rembg import remove
            print("rembg导入成功")
            
            # 检查rembg依赖
            rembg_deps = ["onnxruntime", "numpy", "pillow", "pooch"]
            print("\nrembg依赖检查:")
            for dep in rembg_deps:
                installed, version = check_module(dep)
                status = f"已安装 (版本: {version})" if installed else "未安装"
                print(f"  - {dep}: {status}")
                
            # 检查模型文件
            try:
                import pooch
                from rembg.session_factory import new_session
                print("\n尝试加载rembg模型...")
                session = new_session("u2net")
                print("模型加载成功!")
            except Exception as e:
                print(f"模型加载失败: {str(e)}")
                
        except ImportError as e:
            print(f"rembg导入失败: {str(e)}")
    else:
        print("rembg未安装")
        
        # 检查pip是否可用
        pip_path = f"{os.path.dirname(sys.executable)}/pip"
        if not os.path.exists(pip_path):
            pip_path = f"{os.path.dirname(sys.executable)}/pip3"
        
        if os.path.exists(pip_path):
            print(f"\nPip可用: {pip_path}")
            print("\n安装建议: 运行以下命令安装rembg")
            print(f"{sys.executable} -m pip install rembg")
        else:
            print("\nPip不可用或未找到")
            print("请安装pip后再安装rembg")
    
    print_header("安装建议")
    print("如果遇到问题，请尝试以下命令:")
    print(f"1. 安装/更新rembg: {sys.executable} -m pip install --upgrade rembg")
    print(f"2. 安装所有依赖: {sys.executable} -m pip install --upgrade rembg pillow numpy")
    print("3. 如果安装后仍然提示未安装，可能是因为您有多个Python环境")
    print("   请确保使用正确的Python环境运行程序")
    
    print("\n如果问题仍然存在，请运行以下命令并提供输出:")
    print(f"{sys.executable} -m pip list")

if __name__ == "__main__":
    main()
    
    # 等待用户按键退出
    print("\n按Enter键退出...")
    input()