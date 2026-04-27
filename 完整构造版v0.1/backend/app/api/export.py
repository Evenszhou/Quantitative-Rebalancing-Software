"""
Excel 导出 API 路由

将回测结果导出为包含 3 个 Sheet 的 Excel 文件：
1. 仓位时间序列 - 每日各资产持仓市值和权重
2. 绩效指标 - 年化收益、夏普比率、最大回撤等
3. 验算页面 - 详细验算数据（价格、仓位、净值、调仓标记）

【Layer】API 路由层 - 负责请求处理和响应构建
【依赖】services/ 导出的回测结果数据
【依赖】models/schemas.py - Pydantic 模型
"""
import io
import logging
from datetime import datetime
import pandas as pd
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.utils.helpers import serialize_for_json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["export"])

# ---------------------------------------------------------------------------
# 全局存储引用 - 由 main.py 注入
# ---------------------------------------------------------------------------
_results = None


def set_results_store(results: dict) -> None:
    global _results
    _results = results


@router.get(
    "/export/{task_id}",
    summary="导出回测结果为 Excel",
    description="""
    将指定任务的回测结果导出为 Excel 文件（.xlsx），包含 3 个 Sheet：
    
    - **仓位时间序列**: 每日各资产的持仓市值和权重
    - **绩效指标**: 年化收益、波动率、夏普比率、最大回撤等关键指标
    - **验算页面**: 详细验算数据（仓位、净值变化、调仓标记）
    """,
    responses={404: {"model": "object"}},
)
async def export_excel(task_id: str):
    """
    导出回测结果为 Excel 文件

    - **task_id**: 回测任务 ID（从 /api/backtest 返回）
    """
    if not _results or task_id not in _results:
        raise HTTPException(status_code=404, detail=f"任务 {task_id} 不存在，无法导出")

    stored = _results[task_id]
    raw = stored["raw_result"]

    try:
        buffer = io.BytesIO()

        # 使用 openpyxl 引擎写入 Excel
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:

            # ============================================================
            # Sheet 1: 仓位时间序列
            # ============================================================
            position_series = raw.get("position_series")
            if position_series is not None and (isinstance(position_series, pd.DataFrame) and not position_series.empty):
                if isinstance(position_series, pd.DataFrame):
                    export_df = position_series.copy()
                    # 添加日期列
                    export_df.insert(0, "日期", export_df.index.strftime("%Y-%m-%d"))
                    # 计算权重列
                    for col in position_series.columns:
                        export_df[f"{col}_权重"] = (
                            position_series[col] / position_series.sum(axis=1)
                        ).round(6)
                    export_df.to_excel(
                        writer, sheet_name="仓位时间序列", index=False
                    )
                elif isinstance(position_series, dict):
                    # 字典格式，转为 DataFrame
                    records = []
                    for date_str, positions in position_series.items():
                        row = {"日期": date_str}
                        row.update(positions)
                        records.append(row)
                    export_df = pd.DataFrame(records)
                    export_df.to_excel(
                        writer, sheet_name="仓位时间序列", index=False
                    )
            else:
                pd.DataFrame({"提示": ["无仓位数据"]}).to_excel(
                    writer, sheet_name="仓位时间序列", index=False
                )

            # ============================================================
            # Sheet 2: 绩效指标
            # ============================================================
            metrics = raw.get("metrics", {})
            if metrics:
                metrics_records = [
                    {"指标": "年化收益率", "值": f"{metrics['annual_return']:.2%}"},
                    {"指标": "年化波动率", "值": f"{metrics['annual_volatility']:.2%}"},
                    {"指标": "夏普比率", "值": f"{metrics['sharpe_ratio']:.4f}"},
                    {"指标": "Sortino比率", "值": f"{metrics['sortino_ratio']:.4f}"},
                    {"指标": "最大回撤", "值": f"{metrics['max_drawdown']:.2%}"},
                    {"指标": "Calmar比率", "值": f"{metrics['calmar_ratio']:.4f}"},
                    {"指标": "基准收益率", "值": f"{metrics['baseline_return']:.2%}"},
                    {"指标": "基准波动率", "值": f"{metrics['baseline_volatility']:.2%}"},
                    {"指标": "超额收益", "值": f"{metrics['excess_return']:.2%}"},
                    {"指标": "信息比率", "值": f"{metrics['information_ratio']:.4f}"},
                    {"指标": "胜率", "值": f"{metrics['win_rate']:.2%}"},
                    {"指标": "总交易次数", "值": str(metrics["total_trades"])},
                    {
                        "指标": "总交易成本",
                        "值": f"¥{metrics['total_transaction_cost']:.2f}",
                    },
                ]
                pd.DataFrame(metrics_records).to_excel(
                    writer, sheet_name="绩效指标", index=False
                )
            else:
                pd.DataFrame({"提示": ["无绩效数据"]}).to_excel(
                    writer, sheet_name="绩效指标", index=False
                )

            # ============================================================
            # Sheet 3: 验算页面
            # ============================================================
            validation_data = raw.get("validation_data")
            if validation_data is not None and (isinstance(validation_data, pd.DataFrame) and not validation_data.empty):
                if isinstance(validation_data, pd.DataFrame):
                    export_val = validation_data.copy()
                    export_val.insert(
                        0, "日期", export_val.index.strftime("%Y-%m-%d")
                    )
                    export_val.to_excel(
                        writer, sheet_name="验算页面", index=False
                    )
                elif isinstance(validation_data, dict):
                    # 字典格式转为 DataFrame
                    val_df = pd.DataFrame.from_dict(validation_data, orient="index")
                    val_df.index.name = "日期"
                    val_df.reset_index(inplace=True)
                    val_df.to_excel(writer, sheet_name="验算页面", index=False)
            else:
                pd.DataFrame({"提示": ["无验算数据"]}).to_excel(
                    writer, sheet_name="验算页面", index=False
                )

        # 准备下载
        buffer.seek(0)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"portfolio_report_{timestamp}.xlsx"

        logger.info(f"导出 Excel: task_id={task_id}, file={filename}")

        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            },
        )

    except Exception as e:
        logger.error(f"导出失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"导出 Excel 失败: {str(e)}")
