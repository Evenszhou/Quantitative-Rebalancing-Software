"""
回测引擎模块 v0.3 - 支持滚动配权
修复未来函数问题，实现动态权重计算
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass


@dataclass  
class TransactionCost:
    """交易成本配置"""
    buy_cost_pct: float = 0.001
    sell_cost_pct: float = 0.001
    buy_cost_fixed: float = 0.0
    sell_cost_fixed: float = 0.0
    slippage_pct: float = 0.0005


class BacktestEngine:
    """回测引擎 v0.3 - 支持滚动配权"""
    
    def __init__(
        self, 
        returns_df: pd.DataFrame,
        baseline_asset: str,
        prices_df: Optional[pd.DataFrame] = None
    ):
        self.returns_df = returns_df
        self.baseline_asset = baseline_asset
        self.prices_df = prices_df
        
        if baseline_asset not in returns_df.columns:
            raise ValueError(f"基准资产 {baseline_asset} 不存在")
        
        self.trade_log: List[Dict] = []
    
    def run_backtest(
        self,
        initial_value: float = 100000,
        rebalance_freq: str = '月度',
        transaction_costs: Optional[Dict[str, TransactionCost]] = None,
        use_rolling_weights: bool = False,
        weighting_method: str = '等权',
        warmup_period: int = 252,
        risk_free_rate: float = 0.03,
        allow_short: bool = False,
        static_weights: Optional[pd.Series] = None
    ) -> Dict:
        """
        运行回测（支持滚动配权）
        
        Args:
            initial_value: 初始资金
            rebalance_freq: 再平衡频率
            transaction_costs: 交易成本配置
            use_rolling_weights: 是否使用滚动配权
            weighting_method: 配权方法
            warmup_period: 预热期（天数）
            risk_free_rate: 无风险利率
            allow_short: 是否允许做空
            static_weights: 静态权重（不滚动时使用）
        """
        from .weighting import WeightingEngine
        
        self.trade_log = []
        
        # 确定资产列表
        if static_weights is not None:
            assets = static_weights.index.tolist()
        else:
            assets = [col for col in self.returns_df.columns if col != self.baseline_asset]
        
        if not assets:
            raise ValueError("没有可用资产")
        
        # 默认交易成本
        if transaction_costs is None:
            transaction_costs = {asset: TransactionCost() for asset in assets}
        
        # 获取收益率数据
        asset_returns = self.returns_df[assets]
        
        # 检查数据长度
        if len(asset_returns) < warmup_period:
            raise ValueError(f"数据长度 {len(asset_returns)} 小于预热期 {warmup_period}")
        
        # 根据是否滚动配权选择策略
        if not use_rolling_weights or weighting_method == '等权配权':
            # 使用静态权重
            if static_weights is None:
                # 用预热期数据计算初始权重
                warmup_returns = asset_returns.iloc[:warmup_period]
                engine = WeightingEngine(warmup_returns)
                
                if weighting_method == '等权配权':
                    weights = engine.equal_weight()
                elif weighting_method == '风险平价':
                    weights = engine.risk_parity()
                elif weighting_method == '最小方差':
                    weights = engine.minimum_variance()
                elif weighting_method == '最优夏普':
                    weights = engine.maximum_sharpe(risk_free_rate, allow_short)
                else:
                    weights = engine.equal_weight()
            else:
                weights = static_weights
            
            # 使用静态权重回测
            portfolio_returns, position_series = self._static_weights_backtest(
                asset_returns, weights, initial_value, rebalance_freq, transaction_costs
            )
        else:
            # 滚动配权回测
            portfolio_returns, position_series = self._rolling_weights_backtest(
                asset_returns, 
                weighting_method,
                warmup_period,
                initial_value,
                rebalance_freq,
                transaction_costs,
                risk_free_rate,
                allow_short
            )
        
        # 计算结果
        cumulative_returns = (1 + portfolio_returns).cumprod() - 1
        baseline_returns = self.returns_df[self.baseline_asset]
        baseline_cumulative = (1 + baseline_returns).cumprod() - 1
        
        metrics = self._calculate_metrics(portfolio_returns, baseline_returns)
        drawdown = self._calculate_drawdown(cumulative_returns)
        
        validation_data = self._prepare_validation_data(
            position_series, portfolio_returns, cumulative_returns, initial_value, assets
        )
        
        return {
            'metrics': metrics,
            'returns_series': pd.DataFrame({
                'portfolio': cumulative_returns,
                'baseline': baseline_cumulative
            }),
            'daily_returns': pd.DataFrame({
                'portfolio': portfolio_returns,
                'baseline': baseline_returns
            }),
            'drawdown_series': drawdown,
            'portfolio_value': initial_value * (1 + cumulative_returns),
            'position_series': position_series,
            'trade_log': self.trade_log,
            'validation_data': validation_data
        }
    
    def _static_weights_backtest(
        self,
        returns: pd.DataFrame,
        weights: pd.Series,
        initial_value: float,
        rebalance_freq: str,
        transaction_costs: Dict[str, TransactionCost]
    ) -> Tuple[pd.Series, pd.DataFrame]:
        """静态权重回测"""
        
        # 确定再平衡日期
        if rebalance_freq == '月度':
            rebalance_dates = returns.resample('M').first().index
        elif rebalance_freq == '季度':
            rebalance_dates = returns.resample('Q').first().index
        elif rebalance_freq == '年度':
            rebalance_dates = returns.resample('Y').first().index
        else:
            rebalance_dates = []
        
        portfolio_returns = []
        current_weights = weights.copy()
        current_value = initial_value
        positions = []
        
        for date, daily_ret in returns.iterrows():
            # 记录仓位
            current_positions = current_weights * current_value
            positions.append(current_positions.copy())
            
            # 检查是否需要再平衡
            if date in rebalance_dates:
                # 调整到目标权重
                target_positions = weights * current_value
                total_cost = 0.0
                
                for asset in weights.index:
                    cost_config = transaction_costs.get(asset, TransactionCost())
                    position_change = target_positions[asset] - current_positions[asset]
                    
                    if abs(position_change) > 0:
                        if position_change > 0:  # 买入
                            cost = abs(position_change) * cost_config.buy_cost_pct + cost_config.buy_cost_fixed
                            slippage = abs(position_change) * cost_config.slippage_pct
                        else:  # 卖出
                            cost = abs(position_change) * cost_config.sell_cost_pct + cost_config.sell_cost_fixed
                            slippage = abs(position_change) * cost_config.slippage_pct
                        
                        total_cost += cost + slippage
                
                self.trade_log.append({
                    'date': date,
                    'type': 'REBALANCE',
                    'total_cost': total_cost,
                    'portfolio_value': current_value
                })
                
                current_value -= total_cost
                current_weights = weights.copy()
            
            # 计算当天收益
            daily_return = (daily_ret * current_weights).sum()
            portfolio_returns.append(daily_return)
            current_value *= (1 + daily_return)
            
            # 更新权重漂移
            current_weights = current_weights * (1 + daily_ret)
            current_weights = current_weights / current_weights.sum()
        
        return pd.Series(portfolio_returns, index=returns.index), pd.DataFrame(positions, index=returns.index)
    
    def _rolling_weights_backtest(
        self,
        returns: pd.DataFrame,
        weighting_method: str,
        warmup_period: int,
        initial_value: float,
        rebalance_freq: str,
        transaction_costs: Dict[str, TransactionCost],
        risk_free_rate: float,
        allow_short: bool
    ) -> Tuple[pd.Series, pd.DataFrame]:
        """滚动配权回测（无未来函数）"""
        
        from .weighting import WeightingEngine
        
        # 确定再平衡日期
        if rebalance_freq == '月度':
            rebalance_dates = returns.resample('M').first().index
        elif rebalance_freq == '季度':
            rebalance_dates = returns.resample('Q').first().index
        elif rebalance_freq == '年度':
            rebalance_dates = returns.resample('Y').first().index
        else:
            rebalance_dates = []
        
        portfolio_returns = []
        current_value = initial_value
        positions = []
        
        # 初始权重（用预热期数据）
        warmup_returns = returns.iloc[:warmup_period]
        engine = WeightingEngine(warmup_returns)
        
        if weighting_method == '风险平价':
            current_weights = engine.risk_parity()
        elif weighting_method == '最小方差':
            current_weights = engine.minimum_variance()
        elif weighting_method == '最优夏普':
            current_weights = engine.maximum_sharpe(risk_free_rate, allow_short)
        else:
            current_weights = engine.equal_weight()
        
        # 遍历每个交易日
        for i, (date, daily_ret) in enumerate(returns.iterrows()):
            # 跳过预热期
            if i < warmup_period:
                portfolio_returns.append(0.0)
                positions.append(current_weights * current_value)
                continue
            
            # 记录仓位
            current_positions = current_weights * current_value
            positions.append(current_positions.copy())
            
            # 检查是否需要再平衡
            if date in rebalance_dates:
                # 关键：只用截至当天的历史数据重新计算权重
                historical_returns = returns.iloc[:i+1]  # 包含当天
                engine = WeightingEngine(historical_returns)
                
                if weighting_method == '风险平价':
                    target_weights = engine.risk_parity()
                elif weighting_method == '最小方差':
                    target_weights = engine.minimum_variance()
                elif weighting_method == '最优夏普':
                    target_weights = engine.maximum_sharpe(risk_free_rate, allow_short)
                else:
                    target_weights = engine.equal_weight()
                
                # 计算交易成本
                target_positions = target_weights * current_value
                total_cost = 0.0
                
                for asset in target_weights.index:
                    cost_config = transaction_costs.get(asset, TransactionCost())
                    position_change = target_positions[asset] - current_positions[asset]
                    
                    if abs(position_change) > 0:
                        if position_change > 0:
                            cost = abs(position_change) * cost_config.buy_cost_pct + cost_config.buy_cost_fixed
                            slippage = abs(position_change) * cost_config.slippage_pct
                        else:
                            cost = abs(position_change) * cost_config.sell_cost_pct + cost_config.sell_cost_fixed
                            slippage = abs(position_change) * cost_config.slippage_pct
                        
                        total_cost += cost + slippage
                
                self.trade_log.append({
                    'date': date,
                    'type': 'REBALANCE',
                    'weights': target_weights.to_dict(),  # 记录新权重
                    'total_cost': total_cost,
                    'portfolio_value': current_value
                })
                
                current_value -= total_cost
                current_weights = target_weights.copy()
            
            # 计算当天收益
            daily_return = (daily_ret * current_weights).sum()
            portfolio_returns.append(daily_return)
            current_value *= (1 + daily_return)
            
            # 更新权重漂移
            current_weights = current_weights * (1 + daily_ret)
            current_weights = current_weights / current_weights.sum()
        
        return pd.Series(portfolio_returns, index=returns.index), pd.DataFrame(positions, index=returns.index)
    
    def _calculate_metrics(self, portfolio_returns: pd.Series, baseline_returns: pd.Series) -> Dict:
        """计算绩效指标"""
        annual_return = portfolio_returns.mean() * 252
        annual_volatility = portfolio_returns.std() * np.sqrt(252)
        sharpe_ratio = (annual_return - 0.03) / annual_volatility if annual_volatility > 0 else 0
        
        cumulative = (1 + portfolio_returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()
        
        calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0
        
        baseline_annual_return = baseline_returns.mean() * 252
        baseline_annual_vol = baseline_returns.std() * np.sqrt(252)
        excess_return = annual_return - baseline_annual_return
        
        tracking_error = (portfolio_returns - baseline_returns).std() * np.sqrt(252)
        information_ratio = excess_return / tracking_error if tracking_error != 0 else 0
        
        win_days = (portfolio_returns > baseline_returns).sum()
        total_days = len(portfolio_returns)
        win_rate = win_days / total_days if total_days > 0 else 0
        
        downside_returns = portfolio_returns[portfolio_returns < 0]
        downside_std = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0.001
        sortino_ratio = (annual_return - 0.03) / downside_std
        
        return {
            'annual_return': annual_return,
            'annual_volatility': annual_volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'calmar_ratio': calmar_ratio,
            'sortino_ratio': sortino_ratio,
            'baseline_return': baseline_annual_return,
            'baseline_volatility': baseline_annual_vol,
            'excess_return': excess_return,
            'information_ratio': information_ratio,
            'win_rate': win_rate,
            'total_trades': len(self.trade_log),
            'total_transaction_cost': sum(t['total_cost'] for t in self.trade_log)
        }
    
    def _calculate_drawdown(self, cumulative_returns: pd.Series) -> pd.Series:
        """计算回撤"""
        nav = 1 + cumulative_returns
        running_max = nav.cummax()
        drawdown = (nav - running_max) / running_max
        return drawdown
    
    def _prepare_validation_data(
        self,
        position_series: pd.DataFrame,
        portfolio_returns: pd.Series,
        cumulative_returns: pd.Series,
        initial_value: float,
        assets: List[str]
    ) -> pd.DataFrame:
        """准备验算数据"""
        validation_data = position_series.copy()
        validation_data['组合净值'] = initial_value * (1 + cumulative_returns)
        validation_data['组合日收益率'] = portfolio_returns
        validation_data['组合累计收益率'] = cumulative_returns
        
        # 标记调仓点
        rebalance_dates = [t['date'] for t in self.trade_log]
        validation_data['调仓标记'] = 0
        validation_data.loc[rebalance_dates, '调仓标记'] = 1
        
        return validation_data
