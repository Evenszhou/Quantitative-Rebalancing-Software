"""
Pydantic models for API request/response validation
"""
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class WeightingMethod(str, Enum):
    """Portfolio weighting methods"""
    EQUAL = "equal_weight"
    RISK_PARITY = "risk_parity"
    MIN_VARIANCE = "minimum_variance"
    MAX_SHARPE = "maximum_sharpe"


class RebalanceFreq(str, Enum):
    """Rebalancing frequency"""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    NONE = "none"


class TransactionCostModel(BaseModel):
    """Transaction cost configuration for an asset"""
    buy_cost_pct: float = Field(default=0.001, ge=0, le=1, description="买入成本百分比")
    sell_cost_pct: float = Field(default=0.001, ge=0, le=1, description="卖出成本百分比")
    buy_cost_fixed: float = Field(default=0.0, ge=0, description="买入固定成本（元）")
    sell_cost_fixed: float = Field(default=0.0, ge=0, description="卖出固定成本（元）")
    slippage_pct: float = Field(default=0.0005, ge=0, le=0.1, description="滑点百分比")


class WeightingConfig(BaseModel):
    """Weighting calculation configuration"""
    method: WeightingMethod = Field(default=WeightingMethod.EQUAL, description="配权方法")
    warmup_period: int = Field(default=252, ge=30, le=2000, description="预热期（天）")
    risk_free_rate: float = Field(default=0.03, ge=0, le=0.2, description="无风险利率（年化）")
    allow_short: bool = Field(default=False, description="是否允许做空")
    selected_assets: Optional[List[str]] = Field(default=None, description="参与配权的资产列表")


class BacktestConfig(BaseModel):
    """Backtest configuration"""
    initial_value: float = Field(default=100000, gt=0, description="初始资金")
    rebalance_freq: RebalanceFreq = Field(default=RebalanceFreq.MONTHLY, description="调仓频率")
    baseline_asset: str = Field(description="基准资产名称")
    use_rolling_weights: bool = Field(default=False, description="是否使用滚动配权")
    use_fixed_window: bool = Field(default=False, description="是否使用固定窗口")
    rolling_window: int = Field(default=252, ge=10, le=1000, description="滚动窗口大小")
    transaction_costs: Dict[str, TransactionCostModel] = Field(default_factory=dict, description="各资产交易成本")
    weighting_config: WeightingConfig = Field(description="配权配置")


class UploadResponse(BaseModel):
    """File upload response"""
    success: bool = Field(description="是否成功")
    message: str = Field(description="消息")
    file_id: str = Field(description="文件ID")
    asset_name: str = Field(description="资产名称")
    rows: int = Field(description="数据行数")
    columns: List[str] = Field(description="列名列表")
    date_range: Optional[str] = Field(default=None, description="日期范围")


class WeightsResult(BaseModel):
    """Weighting calculation result"""
    assets: List[str] = Field(description="资产列表")
    weights: Dict[str, float] = Field(description="权重字典")
    metrics: Dict[str, float] = Field(description="组合指标")
    timestamp: datetime = Field(default_factory=datetime.now, description="计算时间")


class BacktestMetrics(BaseModel):
    """Backtest performance metrics"""
    annual_return: float = Field(description="年化收益率")
    annual_volatility: float = Field(description="年化波动率")
    sharpe_ratio: float = Field(description="夏普比率")
    max_drawdown: float = Field(description="最大回撤")
    calmar_ratio: float = Field(description="Calmar比率")
    sortino_ratio: float = Field(description="Sortino比率")
    baseline_return: float = Field(description="基准收益率")
    baseline_volatility: float = Field(default=0.0, description="基准波动率")
    excess_return: float = Field(description="超额收益")
    information_ratio: float = Field(description="信息比率")
    win_rate: float = Field(description="胜率")
    total_trades: int = Field(description="总交易次数")
    total_transaction_cost: float = Field(description="总交易成本")


class TradeLog(BaseModel):
    """Trade log entry"""
    date: str = Field(description="交易日期")
    type: str = Field(description="交易类型")
    total_cost: float = Field(description="总成本")
    portfolio_value: float = Field(default=0, description="组合价值")
    weights: Optional[Dict[str, float]] = Field(default=None, description="调仓后权重")


class BacktestResult(BaseModel):
    """Backtest result"""
    task_id: str = Field(description="任务ID")
    metrics: BacktestMetrics = Field(description="绩效指标")
    returns_series: Dict[str, Dict[str, float]] = Field(description="收益率序列 {date: {portfolio, baseline}}")
    position_series: Dict[str, Dict[str, float]] = Field(description="仓位序列 {date: {asset: value}}")
    trade_log: List[TradeLog] = Field(description="交易日志")
    validation_data: Optional[Dict[str, Any]] = Field(default=None, description="验算数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="计算时间")


class ErrorResponse(BaseModel):
    """Error response"""
    error: str = Field(description="错误类型")
    detail: Optional[str] = Field(default=None, description="错误详情")
    timestamp: datetime = Field(default_factory=datetime.now)


class AssetInfo(BaseModel):
    """Asset information"""
    asset_name: str = Field(description="资产名称")
    file_id: str = Field(description="文件ID")
    rows: int = Field(description="数据行数")
    columns: List[str] = Field(description="列名")
    has_close: bool = Field(description="是否有收盘价")
    date_range: Optional[str] = Field(default=None, description="日期范围")


class DataValidationResult(BaseModel):
    """Data validation result"""
    valid: bool = Field(description="是否有效")
    issues: List[str] = Field(default_factory=list, description="问题列表")
    stats: Dict[str, Any] = Field(default_factory=dict, description="统计信息")
