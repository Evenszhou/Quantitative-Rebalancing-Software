"""
回测 API 路由

处理配权计算和回测请求。支持：
1. 静态权重回测（基于预热期计算一次权重）
2. 滚动配权回测（每次调仓时重新计算权重）
3. 多种配权方法（等权、风险平价、最小方差、最大夏普）
4. 灵活的交易成本设置
5. 多种调仓频率（月度、季度、年度、不调仓）

【Layer】API 路由层 - 负责请求处理和响应构建
【依赖】services/data_loader.py - 数据加载
【依赖】services/weighting.py - 配权计算
【依赖】services/backtest.py - 回测引擎
【依赖】models/schemas.py - Pydantic 模型
"""
import logging
from datetime import datetime
import pandas as pd
from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    BacktestConfig,
    BacktestResult,
    BacktestMetrics,
    TradeLog,
    ErrorResponse,
)
from app.services.data_loader import DataLoaderService
from app.services.backtest import BacktestService, TransactionCost
from app.utils.helpers import generate_task_id, serialize_for_json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["backtest"])

# ---------------------------------------------------------------------------
# 全局存储引用 - 由 main.py 注入
# ---------------------------------------------------------------------------
_storage = None
_results = {}


def set_storage(storage: dict) -> None:
    global _storage
    _storage = storage


def set_results_store(results: dict) -> None:
    """注入回测结果存储引用（由 main.py 在启动时调用）"""
    global _results
    _results = results


def get_results_store() -> dict:
    return _results


# ---------------------------------------------------------------------------
# 服务实例
# ---------------------------------------------------------------------------
_data_loader = DataLoaderService()


def _build_transaction_costs(
    config_costs: dict,
) -> dict:
    """
    将 Pydantic TransactionCostModel 转换为 BacktestService 的 TransactionCost dataclass。

    Args:
        config_costs: { asset_name: TransactionCostModel } 或空字典

    Returns:
        { asset_name: TransactionCost }
    """
    result = {}
    for asset_name, cost_model in config_costs.items():
        result[asset_name] = TransactionCost(
            buy_cost_pct=cost_model.buy_cost_pct,
            sell_cost_pct=cost_model.sell_cost_pct,
            buy_cost_fixed=cost_model.buy_cost_fixed,
            sell_cost_fixed=cost_model.sell_cost_fixed,
            slippage_pct=cost_model.slippage_pct,
        )
    return result


@router.post(
    "/backtest",
    response_model=BacktestResult,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="运行回测",
    description="""
    根据上传的资产数据和配置，运行完整的回测分析。

    流程：
    1. 从已上传资产中提取价格数据，计算对数收益率
    2. 根据配权方法计算组合权重
    3. 按指定频率调仓，计算交易成本
    4. 返回绩效指标、收益率序列、仓位序列和交易日志
    """,
)
async def run_backtest(config: BacktestConfig):
    """
    运行回测

    - **config**: 回测配置（初始资金、调仓频率、配权方法等）
    - **file_ids**: 通过 query 参数传入已上传文件的 file_id 列表（逗号分隔）

    需要先通过 /api/upload 上传至少一个文件。
    """
    task_id = generate_task_id()
    start_time = datetime.now()

    try:
        # ---------------------------------------------------------------
        # 1. 收集并验证数据
        # ---------------------------------------------------------------
        # file_ids 暂通过请求体中的额外字段传入（或从已上传的资产中自动选取）
        # 这里我们需要一个机制来知道哪些 file_id 参与。
        # 设计决策：在前端上传文件后，前端把 file_id 列表传给 backtest 接口。
        # 但当前 BacktestConfig 没有包含 file_ids，所以我们从 _storage 中获取所有资产。

        if not _storage:
            raise HTTPException(status_code=400, detail="请先上传至少一个资产数据文件")

        # 收集所有已上传资产的数据
        assets_data = {}
        for file_id, info in _storage.items():
            assets_data[info["asset_name"]] = info["dataframe"]

        # 如果指定了 selected_assets，只使用选中的资产
        if config.weighting_config.selected_assets:
            selected = config.weighting_config.selected_assets
            missing = [a for a in selected if a not in assets_data]
            if missing:
                raise HTTPException(
                    status_code=400,
                    detail=f"以下资产未上传: {', '.join(missing)}",
                )
            assets_data = {k: v for k, v in assets_data.items() if k in selected}

        # 验证基准资产存在
        if config.baseline_asset not in assets_data:
            raise HTTPException(
                status_code=400,
                detail=f"基准资产 '{config.baseline_asset}' 不在已上传的资产列表中。"
                f" 可用资产: {', '.join(assets_data.keys())}",
            )

        # ---------------------------------------------------------------
        # 2. 准备收益率数据
        # ---------------------------------------------------------------
        returns_df = _data_loader.prepare_returns(assets_data, return_type="log")

        if len(returns_df) < config.weighting_config.warmup_period:
            raise HTTPException(
                status_code=400,
                detail=f"数据长度 ({len(returns_df)} 行) 小于预热期 "
                f"({config.weighting_config.warmup_period} 天)，请上传更多数据",
            )

        logger.info(
            f"[{task_id}] 开始回测: {len(assets_data)} 个资产, "
            f"{len(returns_df)} 天数据, 方法={config.weighting_config.method.value}"
        )

        # ---------------------------------------------------------------
        # 3. 构建交易成本配置
        # ---------------------------------------------------------------
        transaction_costs = _build_transaction_costs(config.transaction_costs)

        # 为未配置交易成本的资产设置默认值
        for asset in returns_df.columns:
            if asset not in transaction_costs:
                transaction_costs[asset] = TransactionCost()

        # ---------------------------------------------------------------
        # 4. 运行回测
        # ---------------------------------------------------------------
        engine = BacktestService(
            returns_df=returns_df,
            baseline_asset=config.baseline_asset,
        )

        result = engine.run_backtest(
            initial_value=config.initial_value,
            rebalance_freq=config.rebalance_freq.value,
            transaction_costs=transaction_costs,
            use_rolling_weights=config.use_rolling_weights,
            weighting_method=config.weighting_config.method.value,
            warmup_period=config.weighting_config.warmup_period,
            risk_free_rate=config.weighting_config.risk_free_rate,
            allow_short=config.weighting_config.allow_short,
            use_fixed_window=config.use_fixed_window,
            rolling_window=config.rolling_window,
        )

        # ---------------------------------------------------------------
        # 5. 序列化结果为 Pydantic 模型
        # ---------------------------------------------------------------
        metrics = BacktestMetrics(**result["metrics"])

        # 交易日志序列化
        trade_logs = []
        for t in result.get("trade_log", []):
            log_entry = TradeLog(
                date=str(t.get("date", "")),
                type=t.get("type", "REBALANCE"),
                total_cost=float(t.get("total_cost", 0)),
                portfolio_value=float(t.get("portfolio_value", 0)),
                weights=t.get("weights"),
            )
            trade_logs.append(log_entry)

        # 收益率序列序列化（返回给前端的 JSON 格式）
        returns_data = result.get("returns_series", {})
        if isinstance(returns_data, dict):
            returns_series = serialize_for_json(returns_data)
        else:
            returns_series = serialize_for_json(returns_data.to_dict())

        # 仓位序列序列化（返回给前端的 JSON 格式）
        position_data = result.get("position_series")
        if isinstance(position_data, pd.DataFrame):
            position_dict = {}
            for date in position_data.index:
                date_str = date.strftime('%Y-%m-%d')
                position_dict[date_str] = {
                    col: float(position_data.loc[date, col]) for col in position_data.columns
                }
            position_series = position_dict
        else:
            position_series = serialize_for_json(position_data)

        # 验算数据序列化（返回给前端的 JSON 格式）
        validation_data = result.get("validation_data")
        if isinstance(validation_data, pd.DataFrame):
            validation_dict = serialize_for_json(validation_data.to_dict())
        else:
            validation_dict = serialize_for_json(validation_data)

        backtest_result = BacktestResult(
            task_id=task_id,
            metrics=metrics,
            returns_series=returns_series,
            position_series=position_series,
            trade_log=trade_logs,
            validation_data=validation_dict,
            timestamp=datetime.now(),
        )

        # ---------------------------------------------------------------
        # 6. 存储结果
        # ---------------------------------------------------------------
        # 保存完整的原始结果（含 DataFrame）供导出使用
        _results[task_id] = {
            "config": config.model_dump(),
            "raw_result": result,
            "returns_df": returns_df,
            "assets_data": assets_data,
            "created_at": start_time.isoformat(),
        }

        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"[{task_id}] 回测完成，耗时 {elapsed:.2f}s")

        return backtest_result

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[{task_id}] 回测失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"回测失败: {str(e)}")


@router.get(
    "/results/{task_id}",
    response_model=BacktestResult,
    responses={404: {"model": ErrorResponse}},
    summary="获取回测结果",
    description="根据 task_id 获取之前运行的回测结果。结果包含绩效指标、收益率序列、仓位序列和交易日志。",
)
async def get_results(task_id: str):
    """获取指定任务 ID 的回测结果"""
    if task_id not in _results:
        raise HTTPException(status_code=404, detail=f"任务 {task_id} 不存在")

    stored = _results[task_id]
    raw = stored["raw_result"]

    # 重新序列化为 BacktestResult
    metrics = BacktestMetrics(**raw["metrics"])

    trade_logs = []
    for t in raw.get("trade_log", []):
        trade_logs.append(TradeLog(
            date=str(t.get("date", "")),
            type=t.get("type", "REBALANCE"),
            total_cost=float(t.get("total_cost", 0)),
            portfolio_value=float(t.get("portfolio_value", 0)),
            weights=t.get("weights"),
        ))

    # 收益率序列
    returns_data = raw.get("returns_series", {})
    if isinstance(returns_data, dict):
        returns_series = serialize_for_json(returns_data)
    else:
        returns_series = serialize_for_json(returns_data.to_dict())

    # 仓位序列
    position_data = raw.get("position_series")
    if isinstance(position_data, pd.DataFrame):
        position_dict = {}
        for date in position_data.index:
            date_str = date.strftime('%Y-%m-%d')
            position_dict[date_str] = {
                col: float(position_data.loc[date, col]) for col in position_data.columns
            }
        position_series = position_dict
    else:
        position_series = serialize_for_json(position_data)

    # 验算数据
    validation_data = raw.get("validation_data")
    if isinstance(validation_data, pd.DataFrame):
        validation_dict = serialize_for_json(validation_data.to_dict())
    else:
        validation_dict = serialize_for_json(validation_data)

    return BacktestResult(
        task_id=task_id,
        metrics=metrics,
        returns_series=returns_series,
        position_series=position_series,
        trade_log=trade_logs,
        validation_data=validation_dict,
        timestamp=datetime.now(),
    )


@router.delete(
    "/results/{task_id}",
    summary="删除回测结果",
    description="从内存中移除指定任务的回测结果。",
)
async def delete_results(task_id: str):
    """删除指定任务的回测结果"""
    if task_id not in _results:
        raise HTTPException(status_code=404, detail=f"任务 {task_id} 不存在")
    del _results[task_id]
    return {"success": True, "message": f"已删除任务 {task_id}"}
