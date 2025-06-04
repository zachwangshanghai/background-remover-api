import os
import sys
import argparse
import importlib.util
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

# 检查rembg是否已安装
def check_rembg():
    try:
        if importlib.util.find_spec("rembg") is not None:
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
        try:
            import rembg
            version = getattr(rembg, "__version__", "未知")
            print(f"rembg版本: {version}")
        except:
            print("无法获取rembg版本")
    else:
        print(f"rembg: 未安装 ({error_msg})")
    
    # 检查PIL
    try:
        from PIL import Image, __version__ as pil_version
        print(f"Pillow: 已安装 (版本: {pil_version})")
    except ImportError:
        print("Pillow: 未安装")
    
    # 检查tqdm
    try:
        from tqdm import __version__ as tqdm_version
        print(f"tqdm: 已安装 (版本: {tqdm_version})")
    except ImportError:
        print("tqdm: 未安装")
    
    print("\n如需更详细的诊断，请运行: python diagnose.py")

# 获取rembg状态
REMBG_AVAILABLE, remove_func, Image, error_msg = check_rembg()

def process_image(input_path: Path, output_dir: Path) -> bool:
    """
    处理单张图片，移除背景并保存结果
    
    Args:
        input_path: 输入图片路径
        output_dir: 输出目录路径
    
    Returns:
        bool: 处理是否成功
    """
    if not REMBG_AVAILABLE:
        print(f"错误: {error_msg}")
        return False
        
    try:
        # 准备输出路径
        output_path = output_dir / f"{input_path.stem}_nobg.png"
        
        # 读取并处理图片
        input_image = Image.open(input_path)
        output_image = remove_func(input_image)
        
        # 保存结果
        output_image.save(output_path)
        return True
        
    except FileNotFoundError:
        print(f"\n错误: 找不到文件 '{input_path}'")
        return False
    except PermissionError:
        print(f"\n错误: 没有权限读取或写入文件 '{input_path}'")
        return False
    except Exception as e:
        print(f"\n处理 {input_path.name} 时出错: {str(e)}")
        
        # 添加更多诊断信息
        if "No module named 'rembg'" in str(e):
            print("可能的原因: rembg库未正确安装或在不同的Python环境中")
        elif "No module named" in str(e):
            print("可能的原因: 缺少依赖库")
        elif "memory" in str(e).lower():
            print("可能的原因: 内存不足，尝试减少同时处理的图片数量")
        
        return False

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='批量去除图片背景')
    parser.add_argument('input_dir', type=str, nargs='?', help='输入图片所在目录')
    parser.add_argument('--output-dir', '-o', type=str, help='输出目录（默认为input_dir_nobg）')
    parser.add_argument('--workers', '-w', type=int, default=2, help='同时处理的图片数量（默认为2）')
    parser.add_argument('--check', action='store_true', help='检查环境和依赖')
    parser.add_argument('--install', action='store_true', help='安装rembg库')
    args = parser.parse_args()
    
    # 检查环境
    if args.check:
        check_environment()
        return
    
    # 安装rembg
    if args.install:
        if install_rembg():
            print("请重新运行程序以应用更改。")
        return
    
    # 检查是否提供了输入目录
    if args.input_dir is None:
        parser.print_help()
        return
    
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
    
    # 准备输入输出路径
    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        print(f"错误: 输入目录 '{input_dir}' 不存在")
        return
    
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = input_dir.parent / f"{input_dir.name}_nobg"
    
    # 创建输出目录
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        print(f"错误: 没有权限创建输出目录 '{output_dir}'")
        return
    except Exception as e:
        print(f"创建输出目录时出错: {str(e)}")
        return
    
    # 获取所有支持的图片文件
    supported_formats = {'.png', '.jpg', '.jpeg', '.bmp', '.webp'}
    try:
        image_files = [f for f in input_dir.iterdir() if f.suffix.lower() in supported_formats]
    except PermissionError:
        print(f"错误: 没有权限读取目录 '{input_dir}'")
        return
    except Exception as e:
        print(f"读取目录时出错: {str(e)}")
        return
    
    if not image_files:
        print(f"在 {input_dir} 中没有找到支持的图片文件")
        print(f"支持的格式: {', '.join(supported_formats)}")
        return
    
    print(f"找到 {len(image_files)} 个图片文件")
    print(f"输出目录: {output_dir}")
    print(f"处理线程数: {args.workers}")
    print("\n开始处理...")
    
    # 使用线程池处理图片
    successful = 0
    failed = 0
    
    try:
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            # 创建进度条
            futures = []
            for img_path in image_files:
                future = executor.submit(process_image, img_path, output_dir)
                futures.append(future)
            
            # 显示进度
            for future in tqdm(futures, desc="处理进度", unit="张"):
                if future.result():
                    successful += 1
                else:
                    failed += 1
    except KeyboardInterrupt:
        print("\n处理被用户中断")
        return
    except Exception as e:
        print(f"\n处理过程中出错: {str(e)}")
        return
    
    # 显示处理结果
    print("\n处理完成!")
    print(f"成功: {successful} 张")
    print(f"失败: {failed} 张")
    print(f"处理结果已保存到: {output_dir}")
    
    if failed > 0:
        print("\n如果遇到问题，可以:")
        print("1. 运行 'python diagnose.py' 检查环境")
        print("2. 使用更少的处理线程: --workers 1")
        print("3. 检查图片格式是否支持")
        print("4. 确保有足够的系统内存")

if __name__ == '__main__':
    main()