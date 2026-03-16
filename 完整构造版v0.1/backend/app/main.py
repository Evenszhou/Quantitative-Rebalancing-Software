"""
量化配权系统 v1.0 - FastAPI 后端入口

【启动方式】
    python -m app.main          # 开发模式
    uvicorn app.main:app --reload  # 热重载开发
    uvicorn app.main:app --host 0.0.0.0 --port 8000  # 生产模式

【API 文档】
    启动后访问 http://localhost:8000/docs 查看 Swagger UI

【架构】
    main.py          → FastAPI 入口，挂载路由，注入存储
    api/upload.py    → 文件上传路由
    api/backtest.py  → 回测路由
    api/export.py    → Excel 导出路由
    services/        → 业务逻辑（配权、回测、数据加载）
    models/          → Pydantic 数据模型
"""
import logging
from typing import Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime

from app.config import Settings, init_directories

# ---------------------------------------------------------------------------
# 日志配置
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 设置
# ---------------------------------------------------------------------------
settings = Settings()
init_directories()

# ---------------------------------------------------------------------------
# 内存存储
# ---------------------------------------------------------------------------
# uploaded_files: { file_id: { asset_name, dataframe, validation, filename } }
uploaded_files: Dict[str, Dict] = {}
# backtest_results: { task_id: { config, raw_result, returns_df, assets_data, created_at } }
backtest_results: Dict[str, Dict] = {}

# ---------------------------------------------------------------------------
# FastAPI 应用
# ---------------------------------------------------------------------------
app = FastAPI(
    title="量化配权系统 API",
    description="""
    ## 量化配权与回测分析系统 v1.0

    ### 功能
    - 📁 **文件上传**: 上传 Excel/CSV 资产数据文件
    - ⚖️ **配权计算**: 等权、风险平价、最小方差、最大夏普
    - 📈 **回测分析**: 支持滚动配权、多种调仓频率、交易成本
    - 💾 **结果导出**: 3 Sheet Excel 报告（仓位、绩效、验算）

    ### 工作流程
    1. 调用 `POST /api/upload` 上传资产数据文件
    2. 调用 `POST /api/backtest` 运行回测
    3. 调用 `GET /api/results/{task_id}` 查看结果
    4. 调用 `GET /api/export/{task_id}` 导出 Excel
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS 中间件
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# 全局异常处理
# ---------------------------------------------------------------------------
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """统一 HTTP 异常响应格式"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": type(exc).__name__,
            "detail": exc.detail,
            "timestamp": datetime.now().isoformat(),
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    """兜底异常处理"""
    logger.error(f"未捕获异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "detail": f"服务器内部错误: {str(exc)}",
            "timestamp": datetime.now().isoformat(),
        },
    )

# ---------------------------------------------------------------------------
# 注册路由（延迟导入避免循环依赖）
# ---------------------------------------------------------------------------
def register_routers():
    """注册所有 API 路由，并注入内存存储引用"""
    from app.api.upload import router as upload_router, set_storage as set_upload_storage
    from app.api.backtest import router as backtest_router, set_storage as set_backtest_storage, set_results_store as set_backtest_results
    from app.api.export import router as export_router, set_results_store

    # 注入存储引用
    set_upload_storage(uploaded_files)
    set_backtest_storage(uploaded_files)
    set_backtest_results(backtest_results)
    set_results_store(backtest_results)

    # 注册路由
    app.include_router(upload_router)
    app.include_router(backtest_router)
    app.include_router(export_router)


register_routers()

# ---------------------------------------------------------------------------
# 健康检查端点
# ---------------------------------------------------------------------------
@app.get("/", tags=["system"])
async def root():
    """根路径 - API 状态检查"""
    return {
        "name": "量化配权系统 API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "uploaded_assets": len(uploaded_files),
        "backtest_tasks": len(backtest_results),
    }


@app.get("/api/health", tags=["system"])
async def health_check():
    """健康检查"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# ---------------------------------------------------------------------------
# 启动入口
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
