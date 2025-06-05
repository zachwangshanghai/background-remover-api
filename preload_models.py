from rembg.session_factory import new_session

def preload_models():
    print("预加载模型...")
    models = ["u2net", "u2netp", "u2net_human_seg"]
    for model in models:
        print(f"加载 {model} 模型")
        try:
            new_session(model)
        except Exception as e:
            print(f"加载 {model} 失败: {str(e)}")
    print("模型预加载完成")

if __name__ == "__main__":
    preload_models()
