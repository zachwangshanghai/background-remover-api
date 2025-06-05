from flask import Flask, request, send_file
from rembg import remove
from PIL import Image
import io
import tempfile
import os
import logging
from rembg.session_factory import new_session
import sys


# 在 app.py 开头添加
import os
os.environ["U2NET_HOME"] = os.path.join(os.path.dirname(__file__), "models")

# 添加当前目录到系统路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)
app.logger.setLevel(logging.INFO)  # 设置日志级别

# 使用 u2netp 模型 (仅 4.7MB) 替代 u2net (176MB)
session = new_session("u2netp")  # 应用启动时加载

@app.route('/remove_bg', methods=['POST'])
def remove_background_api():
    """API接口：接收图片并返回去除背景后的图片"""
    try:
        # 1. 获取上传的图片
        if 'image' not in request.files:
            return {'error': 'No image provided'}, 400

        image_file = request.files['image']

        # 2. 验证图片格式
        if not image_file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            return {'error': 'Invalid image format. Use PNG, JPG or JPEG'}, 400

        app.logger.info(f"Processing image: {image_file.filename}")

        # 3. 读取图片并处理
        input_image = Image.open(image_file.stream)
        output_image = remove(input_image, session=session)  # 调用你的去背景函数

        # 4. 创建临时文件保存结果
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            output_image.save(tmp.name, format='PNG')
            tmp_path = tmp.name

        # 5. 返回处理后的图片
        return send_file(
            tmp_path,
            mimetype='image/png',
            as_attachment=True,
            download_name='no-bg.png'
        )

    except Exception as e:
        app.logger.error(f"处理错误: {str(e)}")
        return {'error': f'Internal server error: {str(e)}'}, 500

    finally:
        # 6. 清理临时文件
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.unlink(tmp_path)


#if __name__ == '__main__':
#    # Vercel 会自动设置 PORT 环境变量
#    port = int(os.environ.get("PORT", 5000))
#    app.run(host='0.0.0.0', port=port, debug=False)
   
    
# 在文件底部添加
if __name__ == '__main__':
    # 测试模型加载
    from rembg.session_factory import new_session
    print("测试模型加载...")
    test_session = new_session("u2netp")
    print("模型加载成功!")
    
    # 运行Flask应用
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)# 在文件底部添加


