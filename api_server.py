import logging
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware  # 修正导入路径
import uvicorn
from rembg import remove
from PIL import Image
import io
import os
import time
from typing import Dict, Any
from collections import defaultdict
import json

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, calls: int = 60, period: int = 60):
        super().__init__(app)
        self.calls = calls  # 允许的最大请求数
        self.period = period  # 时间窗口（秒）
        self.requests = defaultdict(list)  # 存储请求历史

    async def dispatch(self, request: Request, call_next):
        # 获取客户端IP
        client_ip = request.client.host
        
        # 清理过期的请求记录
        current_time = time.time()
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if current_time - req_time < self.period
        ]
        
        # 检查请求频率
        if len(self.requests[client_ip]) >= self.calls:
            return JSONResponse(
                status_code=429,
                content={
                    "code": 429,
                    "message": "请求过于频繁，请稍后再试",
                    "data": None
                }
            )
        
        # 记录新请求
        self.requests[client_ip].append(current_time)
        
        # 继续处理请求
        return await call_next(request)

class APIResponse:
    """标准API响应格式"""
    def __init__(
        self,
        code: int = 0,
        message: str = "success",
        data: Any = None
    ):
        self.code = code
        self.message = message
        self.data = data

    def dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "data": self.data
        }

# 创建FastAPI应用
app = FastAPI(
    title="背景去除API",
    description="为微信小程序提供图片背景去除服务的REST API",
    version="1.0.0"
)

# 添加中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中需要设置为微信小程序的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加限流中间件（每分钟最多60个请求）
app.add_middleware(RateLimitMiddleware, calls=60, period=60)

# 支持的图片格式
SUPPORTED_FORMATS = {"image/jpeg", "image/png", "image/jpg"}
# 最大文件大小（4MB，适应微信小程序的限制）
MAX_FILE_SIZE = 4 * 1024 * 1024

async def validate_image(file: UploadFile) -> None:
    """
    验证上传的图片文件
    
    Args:
        file: 上传的文件
    Raises:
        HTTPException: 当文件验证失败时
    """
    # 检查文件大小
    file_size = 0
    contents = await file.read()
    file_size = len(contents)
    await file.seek(0)  # 重置文件指针
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制，最大允许{MAX_FILE_SIZE/1024/1024}MB"
        )
    
    # 检查文件类型
    if file.content_type not in SUPPORTED_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型：{file.content_type}。支持的格式：{', '.join(SUPPORTED_FORMATS)}"
        )

@app.post("/api/remove-background")
async def remove_background(file: UploadFile = File(...)):
    """
    接收图片文件并去除背景
    
    Args:
        file: 上传的图片文件
    Returns:
        处理后的图片数据（Base64编码）
    """
    try:
        # 验证图片
        await validate_image(file)
        
        # 记录请求信息
        logger.info(f"处理文件：{file.filename}，类型：{file.content_type}")
        
        # 读取图片
        contents = await file.read()
        input_image = Image.open(io.BytesIO(contents))
        
        # 处理图片
        logger.info("开始去除背景")
        output_image = remove(input_image)
        logger.info("背景去除完成")
        
        # 将处理后的图片转换为Base64
        img_byte_arr = io.BytesIO()
        output_image.save(img_byte_arr, format='PNG', optimize=True)
        img_byte_arr = img_byte_arr.getvalue()
        import base64
        img_base64 = base64.b64encode(img_byte_arr).decode('utf-8')
        
        # 返回处理后的图片数据
        return APIResponse(
            code=0,
            message="背景去除成功",
            data={
                "image": img_base64,
                "format": "png"
            }
        ).dict()
        
    except HTTPException as e:
        # 处理HTTP异常
        return APIResponse(
            code=e.status_code,
            message=str(e.detail),
            data=None
        ).dict()
    except Exception as e:
        # 记录错误并返回500错误
        logger.error(f"处理图片时发生错误：{str(e)}", exc_info=True)
        return APIResponse(
            code=500,
            message="处理图片时发生错误，请稍后重试",
            data=None
        ).dict()

@app.get("/api/status")
async def get_status():
    """
    API状态检查端点
    """
    return APIResponse(
        code=0,
        message="服务正常运行",
        data={
            "status": "running",
            "supported_formats": list(SUPPORTED_FORMATS),
            "max_file_size_mb": MAX_FILE_SIZE/1024/1024
        }
    ).dict()

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    logger.error(f"未处理的异常：{str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=APIResponse(
            code=500,
            message="服务器内部错误",
            data=None
        ).dict()
    )

if __name__ == "__main__":
    # 设置服务器配置
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    # 启动服务器
    logger.info(f"启动服务器 at http://{host}:{port}")
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )