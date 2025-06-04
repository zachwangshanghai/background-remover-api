from setuptools import setup, find_packages

setup(
    name="bg-remover",
    version="0.1.0",
    description="一个简单的图片背景去除工具",
    author="AI Assistant",
    packages=find_packages(),
    install_requires=[
        "rembg",
        "Pillow",
    ],
    entry_points={
        'console_scripts': [
            'bg-remove=remove_bg:main',
        ],
    },
    python_requires='>=3.6',
)