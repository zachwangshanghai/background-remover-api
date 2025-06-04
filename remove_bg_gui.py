import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import threading
import subprocess
from pathlib import Path
import importlib.util

# 检查rembg是否已安装
def check_rembg():
    try:
        # 检查模块是否可以导入
        if importlib.util.find_spec("rembg") is not None:
            # 尝试导入
            from rembg import remove
            return True, remove, None
        else:
            return False, None, "rembg模块未找到"
    except ImportError as e:
        return False, None, f"导入错误: {str(e)}"
    except Exception as e:
        return False, None, f"未知错误: {str(e)}"

# 尝试安装rembg
def install_rembg():
    try:
        messagebox.showinfo("安装", "正在安装rembg库，这可能需要几分钟时间...\n安装完成后会自动通知您。")
        # 使用当前Python解释器安装rembg
        subprocess.check_call([sys.executable, "-m", "pip", "install", "rembg"])
        messagebox.showinfo("安装成功", "rembg库已成功安装！请重启应用。")
        return True
    except Exception as e:
        messagebox.showerror("安装失败", f"安装rembg库失败: {str(e)}\n\n请尝试手动安装: pip install rembg")
        return False

# 检查rembg状态
REMBG_AVAILABLE, remove_func, error_msg = check_rembg()

class BackgroundRemoverApp:
    def __init__(self, root):
        self.root = root
        self.root.title("图片背景去除工具")
        self.root.geometry("800x600")
        self.root.configure(bg="#f0f0f0")
        
        self.input_image_path = None
        self.output_image_path = None
        self.input_image = None
        self.output_image = None
        self.processing = False
        self.remove_func = remove_func
        
        self.create_widgets()
        
        # 检查rembg是否已安装
        if not REMBG_AVAILABLE:
            result = messagebox.askquestion("依赖缺失", 
                                  f"未检测到rembg库或导入失败。\n\n错误信息: {error_msg}\n\n是否尝试自动安装rembg库？")
            if result == 'yes':
                install_rembg()
    
    def create_widgets(self):
        # 顶部框架 - 按钮区域
        top_frame = tk.Frame(self.root, bg="#f0f0f0")
        top_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.select_btn = tk.Button(top_frame, text="选择图片", command=self.select_image, 
                                   bg="#4CAF50", fg="white", font=("Arial", 12), padx=10)
        self.select_btn.pack(side=tk.LEFT, padx=5)
        
        self.process_btn = tk.Button(top_frame, text="去除背景", command=self.process_image,
                                    bg="#2196F3", fg="white", font=("Arial", 12), padx=10,
                                    state=tk.DISABLED)
        self.process_btn.pack(side=tk.LEFT, padx=5)
        
        self.save_btn = tk.Button(top_frame, text="保存图片", command=self.save_image,
                                 bg="#FF9800", fg="white", font=("Arial", 12), padx=10,
                                 state=tk.DISABLED)
        self.save_btn.pack(side=tk.LEFT, padx=5)
        
        # 状态标签
        self.status_label = tk.Label(top_frame, text="请选择一张图片", bg="#f0f0f0", font=("Arial", 10))
        self.status_label.pack(side=tk.RIGHT, padx=5)
        
        # 中间框架 - 图片显示区域
        middle_frame = tk.Frame(self.root, bg="#f0f0f0")
        middle_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 输入图片框架
        input_frame = tk.LabelFrame(middle_frame, text="原始图片", bg="#f0f0f0", font=("Arial", 12))
        input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        self.input_canvas = tk.Canvas(input_frame, bg="white", bd=1, relief=tk.SUNKEN)
        self.input_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 输出图片框架
        output_frame = tk.LabelFrame(middle_frame, text="处理结果", bg="#f0f0f0", font=("Arial", 12))
        output_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        self.output_canvas = tk.Canvas(output_frame, bg="white", bd=1, relief=tk.SUNKEN)
        self.output_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 配置网格权重
        middle_frame.grid_columnconfigure(0, weight=1)
        middle_frame.grid_columnconfigure(1, weight=1)
        middle_frame.grid_rowconfigure(0, weight=1)
        
        # 底部框架 - 信息区域
        bottom_frame = tk.Frame(self.root, bg="#f0f0f0")
        bottom_frame.pack(fill=tk.X, padx=10, pady=10)
        
        info_label = tk.Label(bottom_frame, 
                             text="提示: 此工具使用rembg库去除图片背景，处理大图片可能需要一些时间。",
                             bg="#f0f0f0", font=("Arial", 10))
        info_label.pack(pady=5)
    
    def select_image(self):
        file_path = filedialog.askopenfilename(
            title="选择图片",
            filetypes=[("图片文件", "*.png *.jpg *.jpeg *.bmp *.webp")]
        )
        
        if file_path:
            try:
                self.input_image_path = file_path
                self.input_image = Image.open(file_path)
                self.display_image(self.input_image, self.input_canvas)
                self.process_btn.config(state=tk.NORMAL)
                self.status_label.config(text=f"已加载图片: {os.path.basename(file_path)}")
                self.output_image = None
                self.save_btn.config(state=tk.DISABLED)
                self.clear_canvas(self.output_canvas)
            except Exception as e:
                messagebox.showerror("错误", f"无法打开图片: {str(e)}")
    
    def process_image(self):
        # 再次检查rembg是否可用
        if not REMBG_AVAILABLE or self.remove_func is None:
            result = messagebox.askquestion("错误", "未检测到rembg库或导入失败。是否尝试安装？")
            if result == 'yes':
                if install_rembg():
                    messagebox.showinfo("提示", "请重启应用以应用更改")
            return
            
        if self.input_image and not self.processing:
            self.processing = True
            self.process_btn.config(state=tk.DISABLED)
            self.select_btn.config(state=tk.DISABLED)
            self.status_label.config(text="正在处理图片...")
            
            # 在新线程中处理图片，避免界面卡死
            threading.Thread(target=self._process_image_thread).start()
    
    def _process_image_thread(self):
        try:
            # 移除背景
            self.output_image = self.remove_func(self.input_image)
            
            # 在主线程中更新UI
            self.root.after(0, self._update_ui_after_processing)
        except Exception as e:
            # 在主线程中显示错误
            error_message = f"处理图片时出错: {str(e)}"
            
            # 添加更多诊断信息
            if "No module named 'rembg'" in str(e):
                error_message += "\n\n可能的原因: rembg库未正确安装或在不同的Python环境中"
            elif "No module named" in str(e):
                error_message += "\n\n可能的原因: 缺少依赖库，rembg依赖于其他库"
            
            self.root.after(0, lambda: self._show_error(error_message))
    
    def _update_ui_after_processing(self):
        self.display_image(self.output_image, self.output_canvas)
        self.save_btn.config(state=tk.NORMAL)
        self.select_btn.config(state=tk.NORMAL)
        self.process_btn.config(state=tk.NORMAL)
        self.status_label.config(text="背景去除完成")
        self.processing = False
    
    def _show_error(self, message):
        messagebox.showerror("错误", message)
        self.select_btn.config(state=tk.NORMAL)
        self.process_btn.config(state=tk.NORMAL)
        self.status_label.config(text="处理失败")
        self.processing = False
    
    def save_image(self):
        if self.output_image:
            file_path = filedialog.asksaveasfilename(
                title="保存图片",
                defaultextension=".png",
                filetypes=[("PNG图片", "*.png"), ("所有文件", "*.*")]
            )
            
            if file_path:
                try:
                    self.output_image.save(file_path)
                    self.status_label.config(text=f"图片已保存: {os.path.basename(file_path)}")
                    messagebox.showinfo("成功", f"图片已成功保存到:\n{file_path}")
                except Exception as e:
                    messagebox.showerror("错误", f"保存图片时出错: {str(e)}")
    
    def display_image(self, img, canvas):
        self.clear_canvas(canvas)
        
        # 获取画布尺寸
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()
        
        # 如果画布尺寸为0（初始化时），使用默认尺寸
        if canvas_width <= 1 or canvas_height <= 1:
            canvas_width = 350
            canvas_height = 350
        
        # 调整图片大小以适应画布
        img_width, img_height = img.size
        scale = min(canvas_width/img_width, canvas_height/img_height)
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        # 调整图片大小
        resized_img = img.resize((new_width, new_height), Image.LANCZOS)
        
        # 转换为PhotoImage
        photo = ImageTk.PhotoImage(resized_img)
        
        # 保存引用，防止垃圾回收
        canvas.image = photo
        
        # 在画布中央显示图片
        canvas.create_image(canvas_width//2, canvas_height//2, image=photo, anchor=tk.CENTER)
    
    def clear_canvas(self, canvas):
        canvas.delete("all")

def main():
    root = tk.Tk()
    
    # 添加菜单栏
    menu_bar = tk.Menu(root)
    root.config(menu=menu_bar)
    
    # 创建帮助菜单
    help_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="帮助", menu=help_menu)
    
    # 添加诊断选项
    help_menu.add_command(label="安装rembg", command=install_rembg)
    help_menu.add_command(label="显示Python路径", 
                         command=lambda: messagebox.showinfo("Python路径", 
                                                           f"当前Python解释器: {sys.executable}\n"
                                                           f"Python版本: {sys.version}"))
    help_menu.add_separator()
    help_menu.add_command(label="关于", 
                         command=lambda: messagebox.showinfo("关于", 
                                                           "图片背景去除工具\n\n"
                                                           "使用rembg库实现自动背景去除"))
    
    app = BackgroundRemoverApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()