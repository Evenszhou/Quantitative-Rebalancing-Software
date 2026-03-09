"""
回测引擎模块
实现策略回测和绩效评估
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple


class BacktestEngine:
    """回测引擎"""
    
    def __init__(
        self, 
        returns_df: pd.DataFrame,
        weights: pd.Series,
        baseline_asset: str
    ):
        """
        初始化回测引擎
        
        Args:
            returns_df: 收益率数据框
            weights: 资产权重
            baseline_asset: 基准资产名称
        """
        self.returns_df = returns_df
        self.weights = weights
        self.baseline_asset = baseline_asset
        
        # 验证基准资产存在
        if baseline_asset not in returns_df.columns:
            raise ValueError(f"基准资产 {baseline_asset} 不存在")
    
    def run_backtest(
        self,
        initial_value: float = 100000,
        rebalance_freq: str = '月度',
        transaction_cost: float = 0.001
    ) -> Dict:
        """
        运行回测
        
        Args:
            initial_value: 初始资金
            rebalance_freq: 再平衡频率 ('月度', '季度', '年度', '不调仓')
            transaction_cost: 交易成本（百分比）
            
        Returns:
            dict: 回测结果
        """
        # 获取参与配权的资产
        assets = self.weights.index.tolist()
        
        # 提取这些资产的收益率
        asset_returns = self.returns_df[assets]
        
        # 计算组合收益率
        if rebalance_freq == '不调仓':
            # 不调仓：买入持有
            portfolio_returns = self._buy_and_hold(asset_returns, self.weights)
        else:
            # 定期再平衡
            portfolio_returns = self._rebalance_periodically(
                asset_returns, 
                self.weights, 
                rebalance_freq,
                transaction_cost
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
            'portfolio_value': initial_value * (1 + cumulative_returns)
        }
        
        return results
    
    def _buy_and_hold(
        self, 
        returns: pd.DataFrame, 
        weights: pd.Series
    ) -> pd.Series:
        """
        买入持有策略
        
        Args:
            returns: 收益率数据框
            weights: 初始权重
            
        Returns:
            pd.Series: 组合日收益率
        """
        # 组合日收益率 = 加权平均
        portfolio_returns = (returns * weights).sum(axis=1)
        
        return portfolio_returns
    
    def _rebalance_periodically(
        self,
        returns: pd.DataFrame,
        target_weights: pd.Series,
        freq: str,
        transaction_cost: float
    ) -> pd.Series:
        """
        定期再平衡策略
        
        Args:
            returns: 收益率数据框
            target_weights: 目标权重
            freq: 再平衡频率
            transaction_cost: 交易成本
            
        Returns:
            pd.Series: 组合日收益率
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
        
        # 遍历每个交易日
        for date, daily_ret in returns.iterrows():
            # 检查是否需要再平衡
            if date in rebalance_dates:
                # 计算再平衡成本
                weight_change = abs(current_weights - target_weights).sum()
                cost = weight_change * transaction_cost
                
                # 调整权重
                current_weights = target_weights.copy()
                
                # 扣除交易成本（体现在当天的收益率上）
                daily_portfolio_return = (daily_ret * current_weights).sum() - cost
            else:
                # 正常计算收益率
                daily_portfolio_return = (daily_ret * current_weights).sum()
                
                # 更新权重（随市值变化）
                current_weights = current_weights * (1 + daily_ret)
                current_weights = current_weights / current_weights.sum()
            
            portfolio_returns.append(daily_portfolio_return)
        
        return pd.Series(portfolio_returns, index=returns.index)
    
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
        
        return {
            'annual_return': annual_return,
            'annual_volatility': annual_volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'calmar_ratio': calmar_ratio,
            'baseline_return': baseline_annual_return,
            'baseline_volatility': baseline_annual_vol,
            'excess_return': excess_return,
            'information_ratio': information_ratio,
            'win_rate': win_rate
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
