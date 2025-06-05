from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from rembg import remove
from PIL import Image
import io
import os
from typing import Dict, Any

# 创建FastAPI应用
app = FastAPI()

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 支持的图片格式
SUPPORTED_FORMATS = {"image/jpeg", "image/png", "image/jpg"}
# 最大文件大小（4MB）
MAX_FILE_SIZE = 4 * 1024 * 1024

class APIResponse:
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

async def validate_image(file: UploadFile) -> None:
    # 检查文件大小
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制，最大允许{MAX_FILE_SIZE/1024/1024}MB"
        )
    
    # 检查文件类型
    if file.content_type not in SUPPORTED_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型：{file.content_type}"
        )
    
    await file.seek(0)

@app.post("/api/remove-background")
async def remove_background(file: UploadFile = File(...)):
    try:
        # 验证图片
        await validate_image(file)
        
        # 读取和处理图片
        contents = await file.read()
        input_image = Image.open(io.BytesIO(contents))
        output_image = remove(input_image)
        
        # 转换为Base64
        img_byte_arr = io.BytesIO()
        output_image.save(img_byte_arr, format='PNG', optimize=True)
        img_byte_arr = img_byte_arr.getvalue()
        import base64
        img_base64 = base64.b64encode(img_byte_arr).decode('utf-8')
        
        return APIResponse(
            code=0,
            message="背景去除成功",
            data={
                "image": img_base64,
                "format": "png"
            }
        ).dict()
        
    except HTTPException as e:
        return APIResponse(
            code=e.status_code,
            message=str(e.detail),
            data=None
        ).dict()
    except Exception as e:
        return APIResponse(
            code=500,
            message="处理图片时发生错误",
            data=None
        ).dict()

@app.get("/api/status")
async def get_status():
    return APIResponse(
        code=0,
        message="服务正常运行",
        data={
            "status": "running",
            "supported_formats": list(SUPPORTED_FORMATS),
            "max_file_size_mb": MAX_FILE_SIZE/1024/1024
        }
    ).dict()

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host=host, port=port)