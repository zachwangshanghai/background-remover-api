import argparse
import sys
import importlib.util
import subprocess
from pathlib import Path

# 检查rembg是否已安装
def check_rembg():
    try:
        # 检查模块是否可以导入
        if importlib.util.find_spec("rembg") is not None:
            # 尝试导入
            from rembg import remove
            from PIL import Image
            return True, remove, Image, None
        else:
            return False, None, None, "rembg模块未找到"
    except ImportError as e:
        return False, None, None, f"导入错误: {str(e)}"
    except Exception as e:
        return False, None, None, f"未知错误: {str(e)}"

# 尝试安装rembg
def install_rembg():
    try:
        print("正在安装rembg库，这可能需要几分钟时间...")
        # 使用当前Python解释器安装rembg
        subprocess.check_call([sys.executable, "-m", "pip", "install", "rembg"])
        print("rembg库已成功安装！")
        return True
    except Exception as e:
        print(f"安装rembg库失败: {str(e)}")
        print("请尝试手动安装: pip install rembg")
        return False

# 检查环境
def check_environment():
    print("\n===== 环境检查 =====")
    print(f"Python版本: {sys.version}")
    print(f"Python路径: {sys.executable}")
    
    # 检查rembg
    rembg_available, _, _, error_msg = check_rembg()
    if rembg_available:
        print("rembg: 已安装")
        
        # 检查rembg版本
        try:
            import rembg
            version = getattr(rembg, "__version__", "未知")
            print(f"rembg版本: {version}")
        except:
            print("无法获取rembg版本")
    else:
        print(f"rembg: 未安装 ({error_msg})")
        print("\n要安装rembg，请运行:")
        print(f"{sys.executable} -m pip install rembg")
    
    # 检查PIL
    try:
        from PIL import Image, __version__ as pil_version
        print(f"Pillow: 已安装 (版本: {pil_version})")
    except ImportError:
        print("Pillow: 未安装")
        print("要安装Pillow，请运行:")
        print(f"{sys.executable} -m pip install Pillow")
    
    print("\n如需更详细的诊断，请运行: python diagnose.py")

# 获取rembg状态
REMBG_AVAILABLE, remove_func, Image, error_msg = check_rembg()

def remove_background(input_path: str, output_path: str) -> None:
    """
    从图片中移除背景
    
    Args:
        input_path: 输入图片的路径
        output_path: 输出图片的保存路径
    """
    # 检查rembg是否可用
    if not REMBG_AVAILABLE:
        print(f"错误: {error_msg}")
        print("rembg库未正确安装。")
        
        # 提示安装
        response = input("是否尝试安装rembg库? (y/n): ")
        if response.lower() == 'y':
            if install_rembg():
                print("请重新运行程序以应用更改。")
            return
        else:
            print("请手动安装rembg库后再试。")
            return
    
    try:
        # 读取输入图片
        input_image = Image.open(input_path)
        
        # 移除背景
        output_image = remove_func(input_image)
        
        # 保存结果
        output_image.save(output_path)
        print(f"背景移除成功！结果已保存到: {output_path}")
        
    except FileNotFoundError:
        print(f"错误: 找不到文件 '{input_path}'")
    except PermissionError:
        print(f"错误: 没有权限读取或写入文件")
    except Exception as e:
        print(f"处理图片时出错: {str(e)}")
        
        # 添加更多诊断信息
        if "No module named 'rembg'" in str(e):
            print("\n可能的原因: rembg库未正确安装或在不同的Python环境中")
            print(f"尝试运行: {sys.executable} -m pip install rembg")
        elif "No module named" in str(e):
            print("\n可能的原因: 缺少依赖库，rembg依赖于其他库")
            print(f"尝试运行: {sys.executable} -m pip install --upgrade rembg pillow")

def main():
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='移除图片背景的工具')
    parser.add_argument('input', type=str, nargs='?', help='输入图片的路径')
    parser.add_argument('output', type=str, nargs='?', help='输出图片的保存路径')
    parser.add_argument('--check', action='store_true', help='检查环境和依赖')
    parser.add_argument('--install', action='store_true', help='安装rembg库')
    
    args = parser.parse_args()
    
    # 检查环境
    if args.check:
        check_environment()
        return
    
    # 安装rembg
    if args.install:
        install_rembg()
        return
    
    # 检查是否提供了必要的参数
    if args.input is None or args.output is None:
        parser.print_help()
        return
    
    # 确保输入文件存在
    if not Path(args.input).exists():
        print(f"错误: 输入文件 '{args.input}' 不存在")
        return
    
    # 确保输出目录存在
    output_dir = Path(args.output).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 执行背景移除
    remove_background(args.input, args.output)

if __name__ == '__main__':
    main()