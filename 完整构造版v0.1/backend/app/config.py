"""
配置管理

使用 Pydantic Settings 管理应用配置，支持环境变量和 .env 文件覆盖。

【Layer】基础设施层
【依赖】pydantic-settings（可选，降级为手动解析）
"""
import os
from typing import List, Optional


class Settings:
    """应用配置（不依赖 pydantic-settings，保持最小依赖）"""

    # CORS 允许的源
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "*",  # 开发阶段允许所有源
    ]

    # 文件存储目录
    UPLOAD_DIR: str = "./data/uploads"

    # API 前缀
    API_PREFIX: str = "/api"

    # 日志级别
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    def __init__(self):
        """从环境变量加载配置"""
        # CORS_ORIGINS 环境变量（逗号分隔）
        cors_env = os.getenv("CORS_ORIGINS")
        if cors_env:
            self.CORS_ORIGINS = [s.strip() for s in cors_env.split(",")]

        # UPLOAD_DIR 环境变量
        upload_dir = os.getenv("UPLOAD_DIR")
        if upload_dir:
            self.UPLOAD_DIR = upload_dir

        # API_PREFIX 环境变量
        api_prefix = os.getenv("API_PREFIX")
        if api_prefix:
            self.API_PREFIX = api_prefix


def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


def init_directories():
    """初始化必要的目录"""
    settings = get_settings()
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs("./data", exist_ok=True)
