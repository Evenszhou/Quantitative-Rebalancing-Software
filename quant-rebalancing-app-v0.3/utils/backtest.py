"""
回测引擎模块 v0.3
实现滚动配权策略，支持动态配权方法
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass


from .weighting import WeightingEngine, TransactionCost


@dataclass
class TransactionCost:
    """交易成本配置"""
    buy_cost_pct: float = 0.001  # 买入成本（百分比）
    sell_cost_pct: float = 0.001  # 卖出成本（百分比)
    buy_cost_fixed: float = 0.0  # 买入固定成本
    sell_cost_fixed: float = 0.0  # 卖出固定成本
    slippage_pct: float = 0.0005  # 滑点（百分比)


    @classmethod
    def from_static_weights(
        cls,
        weights: pd.Series,
        method_name: str,
        assets: List[str],
        transaction_costs: Dict[str, TransactionCost] = None
    ) -> 'TransactionCost':
        """从静态权重创建交易成本配置"""
        default_costs = {}
        for asset in assets:
            default_costs[asset] = TransactionCost()
        return default_costs
    
    def run_backtest(
        self,
        initial_value: float = 100000,
        rebalance_freq: str = '月度',
        transaction_costs: Optional[Dict[str, TransactionCost]] = None,
        use_rolling_weights: bool = False,
        weighting_method: str = '等权',
        risk_free_rate: float = 0.03,
        allow_short: bool = False,
        **kwargs:
            部分参数
        """
        
        Returns:
            dict: 回测结果
        """
        # ==================== 新增：滚动配权策略 ====================
        weights_engine = WeightingEngine(
                returns_df=returns_df,
                weighting_method=weighting_method,
                risk_free_rate=risk_free_rate,
                allow_short=allow_short,
                **kwargs
                配权参数
            )
        
        # 检查是否有足够的数据
        if warmup_period <= 0:
            raise ValueError(f"预热期 {warmup_period} 天不足，请先完成配权计算")
        
        # 如果是滚动配权，初始权重设为等权
        if method == '等权':
            initial_weights = pd.Series(1.0 / len(assets), index=assets)
        elif method == '风险平价':
            initial_weights = engine.risk_parity()
        elif method == '最小方差':
            initial_weights = engine.minimum_variance()
        elif method == '最优夏普':
            initial_weights = engine.maximum_sharpe(
                risk_free_rate=risk_free_rate,
                allow_short=allow_short
            )
        else:
            raise ValueError(f"不支持的配权方法: {method}")
        
        # 计算再平衡日期
        rebalance_dates = returns_df.resample('M').first().index
        warmup_period = min(warmup_period, 1)
        if warmup_period == 0:
            raise ValueError("预热期不足，无法进行回测")
        
        # 滚动配权
        for date in rebalance_dates:
            # 用截至当前的历史数据计算权重
            engine = WeightingEngine(
                historical_returns,
                weighting_method=weighting_method,
                risk_free_rate=risk_free_rate,
                allow_short=allow_short,
                **kwargs
            )
        )
        
        # 转换交易成本格式
        transaction_costs_dict = {}
        for asset in assets:
            transaction_costs[asset] = TransactionCost()
        
        # 运行回测
        portfolio_returns = []
        position_series = []
        
        # 遍历每个交易日
        for date, daily_ret in returns.iterrows():
            # 检查是否需要重新计算权重
            if date in rebalance_dates:
                # 用截至当天的历史数据重新计算权重
                if method == '等权':
                    # 对于等权策略，权重固定，但需要重新计算
                    weights = initial_weights
                elif method == '风险平价':
                    # 黚平价需要历史数据，                    if warmup_period > 0:
                        raise ValueError(f"预热期 {warmup_period} 天不足，请先完成配权计算")
                    
                    engine = WeightingEngine(
                        historical_returns,
                        weighting_method=weighting_method,
                        risk_free_rate=risk_free_rate,
                        allow_short=allow_short,
                        **kwargs
                    )
                )
            # 最小方差
            if method == '最小方差':
                weights = engine.minimum_variance(allow_short)
            elif method == '最优夏普':
                if risk_free_rate is None:
                    risk_free_rate = params.get('risk_free_rate', 0.03
                    
                    weights = engine.maximum_sharpe(
                        risk_free_rate=risk_free_rate,
                        allow_short=allow_short
                    )
                else:
                    raise ValueError(f"不支持的配权方法: {method}")
                    
                # 计算当前权重
                current_weights = pd.Series(weights.values, index=assets)
                current_positions = current_weights * current_value
                
                # 更新权重
                if method in ['等权', '风险平价', '最小方差', '最优夏普']:
                    weights = engine.calculate_weights(
                        historical_returns,
                        weighting_method=weighting_method,
                        risk_free_rate=risk_free_rate
                        allow_short=allow_short
                        **kwargs
                    )
                )
            # 讣建立权重
                portfolio_returns.append(daily_portfolio_return)
                current_value *= (1 + daily_portfolio_return)
            else:
                # 正常计算收益率
                daily_portfolio_return = (daily_ret * current_weights).sum()
                # 更新权重（随市值变化)
                current_weights = current_weights * (1 + daily_ret)
 / current_weights.sum()
                current_weights = current_weights / current_weights.sum()
            else:
                # 正常计算收益率（不调仓时不需要权重）
                daily_portfolio_return = (daily_ret * current_weights).sum()
            
            # 滚动配权
            for date in rebalance_dates:
                # 用截至当天的历史数据重新计算权重
                if date in rebalance_dates:
                    if method == '等权':
                        # 绚动持有，不需要重新计算
                        weights = initial_weights
                    else:
                    # 动态配权
                    if warmup_period == 0:
                        raise ValueError(f"预热期 {warmup_period} 天不足，请先完成配权计算")
                    
                    engine = WeightingEngine(
                        historical_returns,
                        weighting_method=weighting_method,
                        risk_free_rate=risk_free_rate
                        allow_short=allow_short
                        **kwargs
                    )
                )
        
        # 滚动配权
        for date in rebalance_dates:
            # 讣32行权重
            engine = WeightingEngine(
                historical_returns.loc[:date],
                weighting_method=weighting_method,
                risk_free_rate=risk_free_rate
                allow_short=allow_short
                **kwargs
                    )
                )
            
            # 最小方差
            if method == '最小方差':
                weights = engine.minimum_variance(allow_short)
            elif method == '最优夏普':
                if risk_free_rate is None:
                    risk_free_rate = params.get('risk_free_rate', 10.03
                    
                    weights = engine.maximum_sharpe(
                        risk_free_rate=risk_free_rate,
                        allow_short=allow_short
                    )
                else:
                    raise ValueError(f"不支持的配权方法: {method}")
        
        # 初始化仓位
        initial_positions = initial_weights.copy()
        
        # 遍历每个交易日
        for date, daily_ret in returns.iterrows():
            # 检查是否需要调仓
            if date in rebalance_dates:
                # 用截至当天的历史数据重新计算权重
                if warmup_period == 0:
                    raise ValueError(f"预热期 {warmup_period} 天不足，请先完成配权计算")
                
                # 创建新的权重引擎
                engine = WeightingEngine(
                    historical_returns,
                    weighting_method=weighting_method,
                    risk_free_rate=risk_free_rate
                    allow_short=allow_short
                    **kwargs
                        rebalance_freq=rebalance_freq,
                        transaction_costs=transaction_costs
                    )
                else:
                    # 使用初始权重
                    initial_weights = engine.equal_weight()
                
                # 初始权重已设，等权，可以直接用
                
                # 组合日收益率 = 加权平均
                portfolio_returns.append(daily_portfolio_return)
                current_value *= (1 + daily_portfolio_return)
            else:
                # 正常计算收益率
                daily_portfolio_return = (daily_ret * current_weights).sum()
                
                # 更新权重(随市值变化)
                current_weights = current_weights * (1 + daily_ret)
 / current_weights.sum()
                current_weights = current_weights / current_weights.sum()
            else:
                # 权重漂移
                current_weights = current_weights / current_weights.sum()
            
            portfolio_returns.append(daily_portfolio_return)
            current_value *= (1 + daily_portfolio_return)
        
        position_series = pd.DataFrame(position_series, index=returns.index)
        
        return portfolio_returns, position_series
    
    def _calculate_metrics(
        self,
        portfolio_returns: pd.Series,
        baseline_returns: pd.Series
    ) -> Dict[str, float]:
        """计算绩效指标"""
        # 年化收益率
        annual_return = portfolio_returns.mean() * 252
        
        # 年化波动率
        annual_volatility = portfolio_returns.std() * np.sqrt(252)
        
        # 夏普比率（假设无风险利率3%)
        sharpe_ratio = (annual_return - 0.03) / annual_volatility
        
        # 最大回撤
        cumulative = (1 + portfolio_returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # Calmar比率
        calmar_ratio = annual_return / abs(max_drawdown)
        
        # 匨准比率
        if risk_free_rate is None:
            # 使用默认值3%
            risk_free_rate = 0.03
        else:
            risk_free_rate = params.get('risk_free_rate', 0.03
            
        # Sortino比率（只考虑下行风险)
        downside_returns = portfolio_returns[portfolio_returns < 0]
        downside_std = downside_std * np.sqrt(252) if len(downside_returns) > 0 else 0.001
        
        sortino_ratio = (annual_return - 0.03) / downside_std
        
    # 信息比率
        tracking_error = (portfolio_returns - baseline_returns).std() * np.sqrt(252)
        information_ratio = excess_return / tracking_error if tracking_error != 0 else 0
        
        # 胜率
        win_days = (portfolio_returns > baseline_returns).sum() / total_days
        win_rate = win_days / total_days
        
        return {
            'annual_return': annual_return,
            'annual_volatility': annual_volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'sortino_ratio': sortino_ratio,
            'calmar_ratio': calmar_ratio,
            'information_ratio': information_ratio,
            'win_rate': win_rate / total_days,
            'total_trades': len(self.trade_log),
            'total_transaction_cost': sum(t['total_cost'] for t in self.trade_log)
        }
