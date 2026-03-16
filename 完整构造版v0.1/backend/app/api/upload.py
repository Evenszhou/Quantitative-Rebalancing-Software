"""
文件上传 API 路由

处理资产数据文件（Excel/CSV）的上传、验证和预处理。
上传的文件被解析为标准化的 DataFrame，存入内存存储，
供后续的配权计算和回测使用。

【Layer】API 路由层 - 负责请求处理和响应构建
【依赖】services/data_loader.py - 数据加载业务逻辑
【依赖】models/schemas.py - Pydantic 请求/响应模型
"""
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Dict

from app.models.schemas import UploadResponse, ErrorResponse, AssetInfo
from app.services.data_loader import DataLoaderService
from app.utils.helpers import generate_file_id, serialize_for_json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["upload"])

# ---------------------------------------------------------------------------
# 全局内存存储 - 上传的资产数据
# 结构: { file_id: { "asset_name": str, "dataframe": pd.DataFrame } }
# ---------------------------------------------------------------------------
# 由 main.py 注入，通过 set_storage() 设置
_storage: Dict[str, Dict] = {}


def set_storage(storage: Dict[str, Dict]) -> None:
    """注入内存存储引用（由 main.py 在启动时调用）"""
    global _storage
    _storage = storage


def get_storage() -> Dict[str, Dict]:
    """获取内存存储引用"""
    return _storage


# ---------------------------------------------------------------------------
# 服务实例
# ---------------------------------------------------------------------------
_data_loader = DataLoaderService()


@router.post(
    "/upload",
    response_model=UploadResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="上传资产数据文件",
    description="""
    上传单个资产数据文件（Excel .xlsx/.xls 或 CSV .csv）。
    
    系统会自动：
    1. 识别并标准化列名（中英文均可）
    2. 解析日期列并设为索引
    3. 验证数据质量（缺失值、必需列等）
    
    返回文件 ID，用于后续的配权和回测。
    """
)
async def upload_file(file: UploadFile = File(...)):
    """
    上传资产数据文件

    - **file**: Excel 或 CSV 文件，文件名将作为资产名称
    """
    try:
        # --- 读取文件字节 ---
        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(status_code=400, detail="上传的文件为空")

        filename = file.filename or "unknown"
        file_id = generate_file_id()

        logger.info(f"上传文件: {filename} ({len(file_bytes)} bytes), file_id={file_id}")

        # --- 调用 DataLoader 解析文件 ---
        df, asset_name = _data_loader.load_file(file_bytes, filename)

        # --- 数据验证 ---
        validation = _data_loader.validate_data(df)

        if not validation["valid"]:
            raise HTTPException(
                status_code=400,
                detail=f"数据验证失败: {'; '.join(validation['issues'])}"
            )

        # --- 存入内存 ---
        _storage[file_id] = {
            "asset_name": asset_name,
            "dataframe": df,
            "validation": validation,
            "filename": filename,
        }

        # --- 构建响应 ---
        asset_info = _data_loader.get_asset_info(df, asset_name, file_id)

        return UploadResponse(
            success=True,
            message=f"成功加载 {asset_name}，共 {len(df)} 行数据",
            file_id=file_id,
            asset_name=asset_name,
            rows=len(df),
            columns=serialize_for_json(df.columns.tolist()),
            date_range=asset_info.get("date_range"),
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"文件上传失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")


@router.get(
    "/assets",
    summary="获取已上传资产列表",
    description="返回所有已上传的资产信息，包括资产名、行数、列名、日期范围等。",
)
async def list_assets():
    """获取已上传的所有资产信息列表"""
    assets = []
    for file_id, info in _storage.items():
        df = info["dataframe"]
        asset_info = _data_loader.get_asset_info(df, info["asset_name"], file_id)
        assets.append(AssetInfo(**asset_info))
    return {"assets": assets, "count": len(assets)}


@router.delete(
    "/assets/{file_id}",
    summary="删除已上传资产",
    description="从内存中移除指定资产。",
)
async def delete_asset(file_id: str):
    """删除指定资产"""
    if file_id not in _storage:
        raise HTTPException(status_code=404, detail=f"资产 {file_id} 不存在")
    asset_name = _storage[file_id]["asset_name"]
    del _storage[file_id]
    return {"success": True, "message": f"已删除 {asset_name}"}


@router.get(
    "/assets/{file_id}/preview",
    summary="预览资产数据",
    description="返回指定资产的前 N 行数据预览。",
)
async def preview_asset(file_id: str, rows: int = 10):
    """预览资产数据"""
    if file_id not in _storage:
        raise HTTPException(status_code=404, detail=f"资产 {file_id} 不存在")

    df = _storage[file_id]["dataframe"]
    preview_df = df.head(rows)

    return {
        "asset_name": _storage[file_id]["asset_name"],
        "total_rows": len(df),
        "preview": serialize_for_json(preview_df.reset_index().to_dict(orient="records")),
    }
