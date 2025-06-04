import requests
import base64
from PIL import Image
import io
import os
import time

class APITester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.test_image_path = "test_images"
        
        # 创建测试图片目录
        os.makedirs(self.test_image_path, exist_ok=True)
        
        # 创建测试用的图片
        self.create_test_images()

    def create_test_images(self):
        """创建测试用的图片文件"""
        # 创建一个有效的测试图片
        img = Image.new('RGB', (100, 100), color='red')
        img.save(os.path.join(self.test_image_path, "valid.jpg"))
        
        # 创建一个大文件（>4MB）
        large_img = Image.new('RGB', (2000, 2000), color='blue')
        large_img.save(os.path.join(self.test_image_path, "too_large.jpg"), quality=100)

    def test_server_status(self):
        """测试服务器状态"""
        print("\n1. 测试服务器状态")
        print("-" * 50)
        
        try:
            response = requests.get(f"{self.base_url}/api/status")
            print(f"状态码: {response.status_code}")
            print(f"响应内容: {response.json()}")
            assert response.status_code == 200, "服务器状态检查失败"
            print("✅ 服务器状态检查通过")
        except Exception as e:
            print(f"❌ 测试失败: {str(e)}")

    def test_remove_background(self):
        """测试背景去除功能"""
        print("\n2. 测试背景去除功能")
        print("-" * 50)
        
        test_image = os.path.join(self.test_image_path, "valid.jpg")
        
        try:
            with open(test_image, 'rb') as f:
                files = {'file': ('test.jpg', f, 'image/jpeg')}
                print("正在上传图片...")
                response = requests.post(
                    f"{self.base_url}/api/remove-background",
                    files=files
                )
                
                print(f"状态码: {response.status_code}")
                result = response.json()
                print(f"响应消息: {result['message']}")
                
                if result['code'] == 0 and result['data']['image']:
                    # 保存处理后的图片
                    img_data = base64.b64decode(result['data']['image'])
                    output_path = os.path.join(self.test_image_path, "result.png")
                    with open(output_path, 'wb') as f:
                        f.write(img_data)
                    print(f"✅ 背景去除成功，结果保存在: {output_path}")
                else:
                    print("❌ 背景去除失败")
        except Exception as e:
            print(f"❌ 测试失败: {str(e)}")

    def test_file_size_limit(self):
        """测试文件大小限制"""
        print("\n3. 测试文件大小限制")
        print("-" * 50)
        
        test_image = os.path.join(self.test_image_path, "too_large.jpg")
        
        try:
            with open(test_image, 'rb') as f:
                files = {'file': ('large.jpg', f, 'image/jpeg')}
                print("正在上传大文件...")
                response = requests.post(
                    f"{self.base_url}/api/remove-background",
                    files=files
                )
                
                print(f"状态码: {response.status_code}")
                result = response.json()
                print(f"响应消息: {result['message']}")
                
                assert result['code'] == 400, "应该拒绝过大的文件"
                print("✅ 文件大小限制测试通过")
        except Exception as e:
            print(f"❌ 测试失败: {str(e)}")

    def test_invalid_format(self):
        """测试无效的文件格式"""
        print("\n4. 测试无效的文件格式")
        print("-" * 50)
        
        # 创建一个文本文件
        test_file = os.path.join(self.test_image_path, "invalid.txt")
        with open(test_file, 'w') as f:
            f.write("This is not an image")
        
        try:
            with open(test_file, 'rb') as f:
                files = {'file': ('test.txt', f, 'text/plain')}
                print("正在上传无效格式文件...")
                response = requests.post(
                    f"{self.base_url}/api/remove-background",
                    files=files
                )
                
                print(f"状态码: {response.status_code}")
                result = response.json()
                print(f"响应消息: {result['message']}")
                
                assert result['code'] == 400, "应该拒绝无效的文件格式"
                print("✅ 文件格式验证测试通过")
        except Exception as e:
            print(f"❌ 测试失败: {str(e)}")

    def run_all_tests(self):
        """运行所有测试"""
        print("开始API测试...\n")
        
        self.test_server_status()
        time.sleep(1)  # 添加短暂延迟，避免请求过快
        
        self.test_remove_background()
        time.sleep(1)
        
        self.test_file_size_limit()
        time.sleep(1)
        
        self.test_invalid_format()
        
        print("\n测试完成!")

if __name__ == "__main__":
    tester = APITester()
    tester.run_all_tests()