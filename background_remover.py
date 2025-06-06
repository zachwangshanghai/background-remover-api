import numpy as np
import onnxruntime
from PIL import Image
import io
from pathlib import Path

class BackgroundRemover:
    def __init__(self, model_path: str = "models/u2netp.onnx"):
        # 初始化 ONNX 运行时会话
        self.session = onnxruntime.InferenceSession(model_path)
        
        # 获取模型的输入名称
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name
        
        # 模型输入大小
        self.input_size = 320

    def _preprocess(self, image: Image.Image) -> np.ndarray:
        """预处理图像"""
        # 调整图像大小
        image = image.convert('RGB')
        temp_size = max(image.size)
        scale = self.input_size / temp_size
        new_size = tuple([int(x * scale) for x in image.size])
        image = image.resize(new_size, Image.LANCZOS)

        # 创建新的图像并粘贴调整后的图像
        new_image = Image.new("RGB", (self.input_size, self.input_size), (0, 0, 0))
        new_image.paste(image, ((self.input_size - new_size[0]) // 2,
                               (self.input_size - new_size[1]) // 2))

        # 转换为numpy数组并归一化
        image = np.array(new_image)
        image = image.transpose((2, 0, 1))  # 转换为CHW格式
        image = image / 255.0  # 归一化到[0,1]
        image = image.astype(np.float32)
        image = np.expand_dims(image, 0)  # 添加batch维度
        
        return image

    def _postprocess(self, pred: np.ndarray, original_size: tuple) -> Image.Image:
        """后处理预测结果"""
        # 获取预测的mask
        pred = pred.squeeze()
        
        # 调整mask大小以匹配输入图像的尺寸
        mask = Image.fromarray((pred * 255).astype(np.uint8))
        mask = mask.resize(original_size, Image.LANCZOS)
        
        return mask

    def remove_background(self, input_image: Image.Image) -> Image.Image:
        """移除图像背景"""
        # 保存原始尺寸
        original_size = input_image.size
        
        # 预处理
        image = self._preprocess(input_image)
        
        # 运行推理
        pred = self.session.run([self.output_name], {self.input_name: image})[0]
        
        # 后处理获取mask
        mask = self._postprocess(pred, original_size)
        
        # 创建透明背景的输出图像
        output_image = Image.new('RGBA', original_size, (0, 0, 0, 0))
        
        # 将原始图像转换为RGBA
        input_image = input_image.convert('RGBA')
        
        # 应用mask
        pixels = input_image.load()
        mask_pixels = mask.load()
        output_pixels = output_image.load()
        
        for y in range(original_size[1]):
            for x in range(original_size[0]):
                r, g, b, a = pixels[x, y]
                mask_value = mask_pixels[x, y]
                output_pixels[x, y] = (r, g, b, int(mask_value))
        
        return output_image

    @staticmethod
    def from_bytes(image_bytes: bytes) -> Image.Image:
        """从字节数据创建PIL图像"""
        return Image.open(io.BytesIO(image_bytes))

    @staticmethod
    def to_bytes(image: Image.Image, format: str = 'PNG') -> bytes:
        """将PIL图像转换为字节数据"""
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format=format)
        return img_byte_arr.getvalue()