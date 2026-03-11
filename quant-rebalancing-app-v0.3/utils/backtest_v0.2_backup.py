"""
回测引擎模块 v0.2
实现策略回测、绩效评估和交易成本管理
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass


@dataclass
class TransactionCost:
    """交易成本配置"""
    buy_cost_pct: float = 0.001  # 买入成本（百分比）
    sell_cost_pct: float = 0.001  # 卖出成本（百分比）
    buy_cost_fixed: float = 0.0  # 买入固定成本
    sell_cost_fixed: float = 0.0  # 卖出固定成本
    slippage_pct: float = 0.0005  # 滑点（百分比）


class BacktestEngine:
    """回测引擎 v0.2"""
    
    def __init__(
        self, 
        returns_df: pd.DataFrame,
        weights: pd.Series,
        baseline_asset: str,
        prices_df: Optional[pd.DataFrame] = None
    ):
        """
        初始化回测引擎
        
        Args:
            returns_df: 收益率数据框
            weights: 资产权重
            baseline_asset: 基准资产名称
            prices_df: 价格数据框（用于计算验算sheet）
        """
        self.returns_df = returns_df
        self.weights = weights
        self.baseline_asset = baseline_asset
        self.prices_df = prices_df
        
        # 验证基准资产存在
        if baseline_asset not in returns_df.columns:
            raise ValueError(f"基准资产 {baseline_asset} 不存在")
        
        # 交易记录
        self.trade_log: List[Dict] = []
        self.position_history: List[pd.Series] = []
    
    def run_backtest(
        self,
        initial_value: float = 100000,
        rebalance_freq: str = '月度',
        transaction_costs: Optional[Dict[str, TransactionCost]] = None
    ) -> Dict:
        """
        运行回测
        
        Args:
            initial_value: 初始资金
            rebalance_freq: 再平衡频率 ('月度', '季度', '年度', '不调仓')
            transaction_costs: 各资产的交易成本配置，key为资产名，value为TransactionCost对象
            
        Returns:
            dict: 回测结果
        """
        # 重置交易记录
        self.trade_log = []
        self.position_history = []
        
        # 获取参与配权的资产
        assets = self.weights.index.tolist()
        
        # 默认交易成本
        if transaction_costs is None:
            transaction_costs = {asset: TransactionCost() for asset in assets}
        
        # 提取这些资产的收益率
        asset_returns = self.returns_df[assets]
        
        # 计算组合收益率
        if rebalance_freq == '不调仓':
            # 不调仓：买入持有
            portfolio_returns, position_series = self._buy_and_hold(
                asset_returns, 
                self.weights,
                initial_value
            )
        else:
            # 定期再平衡
            portfolio_returns, position_series = self._rebalance_periodically(
                asset_returns, 
                self.weights, 
                rebalance_freq,
                transaction_costs,
                initial_value
            )
        
        # 计算累计收益率（用于绘图）
        cumulative_returns = (1 + portfolio_returns).cumprod() - 1
        
        # 基准收益率
        baseline_returns = self.returns_df[self.baseline_asset]
        baseline_cumulative = (1 + baseline_returns).cumprod() - 1
        
        # 计算绩效指标
        metrics = self._calculate_metrics(portfolio_returns, baseline_returns)
        
        # 计算回撤
        drawdown = self._calculate_drawdown(cumulative_returns)
        
        # 准备验算数据
        validation_data = self._prepare_validation_data(
            position_series,
            portfolio_returns,
            cumulative_returns,
            initial_value,
            assets
        )
        
        # 准备结果
        results = {
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
            'position_series': position_series,  # 仓位时间序列
            'trade_log': self.trade_log,  # 交易记录
            'validation_data': validation_data  # 验算数据
        }
        
        return results
    
    def _buy_and_hold(
        self, 
        returns: pd.DataFrame, 
        weights: pd.Series,
        initial_value: float
    ) -> Tuple[pd.Series, pd.DataFrame]:
        """
        买入持有策略
        
        Args:
            returns: 收益率数据框
            weights: 初始权重
            initial_value: 初始资金
            
        Returns:
            tuple: (组合日收益率, 仓位时间序列)
        """
        # 初始仓位
        initial_positions = weights * initial_value
        
        # 组合日收益率 = 加权平均
        portfolio_returns = (returns * weights).sum(axis=1)
        
        # 计算仓位变化
        positions = []
        current_positions = initial_positions.copy()
        
        for date, daily_ret in returns.iterrows():
            # 更新仓位（随收益率变化）
            current_positions = current_positions * (1 + daily_ret)
            positions.append(current_positions.copy())
        
        position_series = pd.DataFrame(positions, index=returns.index)
        
        return portfolio_returns, position_series
    
    def _rebalance_periodically(
        self,
        returns: pd.DataFrame,
        target_weights: pd.Series,
        freq: str,
        transaction_costs: Dict[str, TransactionCost],
        initial_value: float
    ) -> Tuple[pd.Series, pd.DataFrame]:
        """
        定期再平衡策略（带详细交易记录）
        
        Args:
            returns: 收益率数据框
            target_weights: 目标权重
            freq: 再平衡频率
            transaction_costs: 交易成本配置
            initial_value: 初始资金
            
        Returns:
            tuple: (组合日收益率, 仓位时间序列)
        """
        # 确定再平衡频率
        if freq == '月度':
            rebalance_dates = returns.resample('M').first().index
        elif freq == '季度':
            rebalance_dates = returns.resample('Q').first().index
        elif freq == '年度':
            rebalance_dates = returns.resample('Y').first().index
        else:
            rebalance_dates = [returns.index[0]]
        
        # 初始化
        portfolio_returns = []
        current_weights = target_weights.copy()
        current_value = initial_value
        
        # 仓位记录
        positions = []
        
        # 遍历每个交易日
        for date, daily_ret in returns.iterrows():
            # 记录当日开盘时的仓位（调仓前）
            current_positions = current_weights * current_value
            positions.append(current_positions.copy())
            
            # 检查是否需要再平衡
            if date in rebalance_dates:
                # 计算目标仓位
                target_positions = target_weights * current_value
                
                # 计算交易成本
                total_cost = 0.0
                trade_details = []
                
                for asset in target_weights.index:
                    cost_config = transaction_costs.get(asset, TransactionCost())
                    
                    # 计算需要调整的仓位
                    position_change = target_positions[asset] - current_positions[asset]
                    
                    if position_change > 0:  # 买入
                        # 买入成本 = 百分比成本 + 固定成本
                        cost = abs(position_change) * cost_config.buy_cost_pct + cost_config.buy_cost_fixed
                        # 滑点
                        slippage = abs(position_change) * cost_config.slippage_pct
                        total_cost += cost + slippage
                        trade_details.append({
                            'asset': asset,
                            'action': 'BUY',
                            'amount': position_change,
                            'cost': cost + slippage
                        })
                    elif position_change < 0:  # 卖出
                        # 卖出成本 = 百分比成本 + 固定成本
                        cost = abs(position_change) * cost_config.sell_cost_pct + cost_config.sell_cost_fixed
                        # 滑点
                        slippage = abs(position_change) * cost_config.slippage_pct
                        total_cost += cost + slippage
                        trade_details.append({
                            'asset': asset,
                            'action': 'SELL',
                            'amount': abs(position_change),
                            'cost': cost + slippage
                        })
                
                # 记录交易
                self.trade_log.append({
                    'date': date,
                    'type': 'REBALANCE',
                    'total_cost': total_cost,
                    'trades': trade_details,
                    'portfolio_value_before': current_value
                })
                
                # 调整权重
                current_weights = target_weights.copy()
                
                # 扣除交易成本（从组合价值中扣除）
                current_value -= total_cost
                
                # 计算当天收益率（扣除交易成本）
                daily_portfolio_return = (daily_ret * current_weights).sum()
                
                # 记录交易后的组合价值
                current_value *= (1 + daily_portfolio_return)
            else:
                # 正常计算收益率
                daily_portfolio_return = (daily_ret * current_weights).sum()
                
                # 更新组合价值
                current_value *= (1 + daily_portfolio_return)
                
                # 更新权重（随市值变化）
                current_weights = current_weights * (1 + daily_ret)
                current_weights = current_weights / current_weights.sum()
            
            portfolio_returns.append(daily_portfolio_return)
        
        position_series = pd.DataFrame(positions, index=returns.index)
        
        return pd.Series(portfolio_returns, index=returns.index), position_series
    
    def _calculate_metrics(
        self, 
        portfolio_returns: pd.Series,
        baseline_returns: pd.Series
    ) -> Dict[str, float]:
        """
        计算绩效指标
        
        Args:
            portfolio_returns: 组合收益率序列
            baseline_returns: 基准收益率序列
            
        Returns:
            dict: 绩效指标
        """
        # 年化收益率
        annual_return = portfolio_returns.mean() * 252
        
        # 年化波动率
        annual_volatility = portfolio_returns.std() * np.sqrt(252)
        
        # 夏普比率（假设无风险利率3%）
        sharpe_ratio = (annual_return - 0.03) / annual_volatility
        
        # 最大回撤
        cumulative = (1 + portfolio_returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # Calmar比率
        calmar_ratio = annual_return / abs(max_drawdown)
        
        # 基准指标
        baseline_annual_return = baseline_returns.mean() * 252
        baseline_annual_vol = baseline_returns.std() * np.sqrt(252)
        
        # 超额收益
        excess_return = annual_return - baseline_annual_return
        
        # 信息比率
        tracking_error = (portfolio_returns - baseline_returns).std() * np.sqrt(252)
        information_ratio = excess_return / tracking_error if tracking_error != 0 else 0
        
        # 胜率
        win_days = (portfolio_returns > baseline_returns).sum()
        total_days = len(portfolio_returns)
        win_rate = win_days / total_days
        
        # Sortino比率（只考虑下行风险）
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
        """
        计算回撤序列
        
        Args:
            cumulative_returns: 累计收益率序列
            
        Returns:
            pd.Series: 回撤序列
        """
        # 累计净值（假设初始为1）
        nav = 1 + cumulative_returns
        
        # 运行最大值
        running_max = nav.cummax()
        
        # 回撤
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
        """
        准备验算数据
        
        Args:
            position_series: 仓位时间序列
            portfolio_returns: 组合收益率
            cumulative_returns: 累计收益率
            initial_value: 初始资金
            assets: 资产列表
            
        Returns:
            pd.DataFrame: 验算数据表
        """
        # 如果有价格数据，使用真实价格
        if self.prices_df is not None:
            prices = self.prices_df[assets]
            
            # 构建验算表
            validation_data = pd.DataFrame(index=position_series.index)
            
            # 添加价格数据
            for asset in assets:
                validation_data[f'{asset}_开盘价'] = prices[asset]  # 简化处理，用收盘价
                validation_data[f'{asset}_收盘价'] = prices[asset]
            
            # 添加仓位数据
            for asset in assets:
                validation_data[f'{asset}_持仓市值'] = position_series[asset]
                validation_data[f'{asset}_持仓权重'] = position_series[asset] / position_series.sum(axis=1)
            
            # 组合净值
            validation_data['组合净值'] = initial_value * (1 + cumulative_returns)
            validation_data['组合日收益率'] = portfolio_returns
            validation_data['组合累计收益率'] = cumulative_returns
            
            # 标记调仓点
            rebalance_dates = [t['date'] for t in self.trade_log]
            validation_data['调仓标记'] = 0
            validation_data.loc[rebalance_dates, '调仓标记'] = 1
            
        else:
            # 没有价格数据时，只输出仓位和净值
            validation_data = position_series.copy()
            validation_data['组合净值'] = initial_value * (1 + cumulative_returns)
            validation_data['组合日收益率'] = portfolio_returns
            validation_data['组合累计收益率'] = cumulative_returns
            
            # 标记调仓点
            rebalance_dates = [t['date'] for t in self.trade_log]
            validation_data['调仓标记'] = 0
            validation_data.loc[rebalance_dates, '调仓标记'] = 1
        
        return validation_data
    
    def validate_backtest(self) -> Tuple[bool, str]:
        """
        验证回测结果的有效性
        
        Returns:
            tuple: (是否有效, 错误信息)
        """
        try:
            # 运行简单回测
            results = self.run_backtest(initial_value=100000, rebalance_freq='不调仓')
            
            # 检查绩效指标是否合理
            metrics = results['metrics']
            
            # 年化收益率应在合理范围
            if abs(metrics['annual_return']) > 10:
                return False, "年化收益率异常（>1000%）"
            
            # 波动率应为正
            if metrics['annual_volatility'] <= 0:
                return False, "波动率非正"
            
            # 最大回撤应为负
            if metrics['max_drawdown'] > 0:
                return False, "最大回撤为正（计算错误）"
            
            return True, "验证通过"
            
        except Exception as e:
            return False, f"回测失败: {str(e)}"
