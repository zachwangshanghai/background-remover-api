from flask import Flask, request, send_file
from rembg import remove
from PIL import Image
import io
import tempfile
import os
import logging

app = Flask(__name__)
app.logger.setLevel(logging.INFO)  # 设置日志级别


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
        output_image = remove(input_image)  # 调用你的去背景函数

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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)