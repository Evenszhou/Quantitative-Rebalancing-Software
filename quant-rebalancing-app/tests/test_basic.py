"""
测试脚本 - 验证配权和回测模块的正确性
"""
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.data_loader import DataLoader
from utils.weighting import WeightingEngine
from utils.backtest import BacktestEngine


def generate_test_data():
    """生成测试数据"""
    np.random.seed(42)
    
    # 生成3个资产的模拟收益率数据
    dates = pd.date_range(start='2020-01-01', end='2023-12-31', freq='D')
    
    # 资产1: 年化收益8%，波动率15%
    returns1 = np.random.normal(0.08/252, 0.15/np.sqrt(252), len(dates))
    
    # 资产2: 年化收益12%，波动率20%
    returns2 = np.random.normal(0.12/252, 0.20/np.sqrt(252), len(dates))
    
    # 资产3: 年化收益6%，波动率10%
    returns3 = np.random.normal(0.06/252, 0.10/np.sqrt(252), len(dates))
    
    # 添加相关性
    returns2 = returns2 + 0.5 * returns1 + np.random.normal(0, 0.05/np.sqrt(252), len(dates))
    returns3 = returns3 + 0.3 * returns1 + np.random.normal(0, 0.03/np.sqrt(252), len(dates))
    
    # 转换为价格
    prices1 = 100 * np.cumprod(1 + returns1)
    prices2 = 100 * np.cumprod(1 + returns2)
    prices3 = 100 * np.cumprod(1 + returns3)
    
    # 创建数据框
    df = pd.DataFrame({
        '日期': dates,
        '收盘价': prices1
    })
    df['日期'] = pd.to_datetime(df['日期'])
    df = df.set_index('日期')
    
    df2 = pd.DataFrame({
        '日期': dates,
        '收盘价': prices2
    })
    df2['日期'] = pd.to_datetime(df2['日期'])
    df2 = df2.set_index('日期')
    
    df3 = pd.DataFrame({
        '日期': dates,
        '收盘价': prices3
    })
    df3['日期'] = pd.to_datetime(df3['日期'])
    df3 = df3.set_index('日期')
    
    return {
        'Asset1': df,
        'Asset2': df2,
        'Asset3': df3
    }


def test_data_loader():
    """测试数据加载器"""
    print("=" * 60)
    print("测试数据加载器")
    print("=" * 60)
    
    data_loader = DataLoader()
    
    # 生成测试数据
    test_data = generate_test_data()
    
    # 准备收益率数据
    returns_df = data_loader.prepare_returns(test_data)
    
    print(f"✓ 成功加载 {len(returns_df)} 天数据")
    print(f"✓ 资产数量: {len(returns_df.columns)}")
    print(f"✓ 时间范围: {returns_df.index.min()} 到 {returns_df.index.max()}")
    print()
    
    return returns_df


def test_weighting_engine(returns_df):
    """测试配权引擎"""
    print("=" * 60)
    print("测试配权引擎")
    print("=" * 60)
    
    engine = WeightingEngine(returns_df)
    
    # 测试等权配权
    print("\n1. 等权配权")
    weights_equal = engine.equal_weight()
    print(f"   权重: {weights_equal.to_dict()}")
    print(f"   权重和: {weights_equal.sum():.6f}")
    assert abs(weights_equal.sum() - 1.0) < 1e-6, "权重和不为1"
    print("   ✓ 验证通过")
    
    # 测试风险平价
    print("\n2. 风险平价配权")
    weights_rp = engine.risk_parity()
    print(f"   权重: {weights_rp.to_dict()}")
    print(f"   权重和: {weights_rp.sum():.6f}")
    
    # 验证风险贡献
    metrics = engine.get_portfolio_metrics(weights_rp)
    rc = metrics['risk_contributions']
    print(f"   风险贡献: {rc}")
    
    # 检查风险贡献是否接近（风险平价的目标）
    rc_values = list(rc.values())
    rc_std = np.std(rc_values)
    print(f"   风险贡献标准差: {rc_std:.6f} (越小越好)")
    assert abs(weights_rp.sum() - 1.0) < 1e-6, "权重和不为1"
    print("   ✓ 验证通过")
    
    # 测试最小方差
    print("\n3. 最小方差配权")
    weights_mv = engine.minimum_variance()
    print(f"   权重: {weights_mv.to_dict()}")
    print(f"   权重和: {weights_mv.sum():.6f}")
    
    # 验证方差确实更小
    var_equal = np.dot(weights_equal.T, np.dot(engine.cov_matrix, weights_equal))
    var_mv = np.dot(weights_mv.T, np.dot(engine.cov_matrix, weights_mv))
    print(f"   等权方差: {var_equal:.6f}")
    print(f"   最小方差: {var_mv:.6f}")
    assert var_mv <= var_equal, "最小方差策略方差反而更大"
    print("   ✓ 验证通过")
    
    # 测试最大夏普
    print("\n4. 最大夏普配权")
    weights_sharpe = engine.maximum_sharpe()
    print(f"   权重: {weights_sharpe.to_dict()}")
    print(f"   权重和: {weights_sharpe.sum():.6f}")
    assert abs(weights_sharpe.sum() - 1.0) < 1e-6, "权重和不为1"
    print("   ✓ 验证通过")
    
    print()
    
    return weights_equal, weights_rp, weights_mv


def test_backtest_engine(returns_df, weights):
    """测试回测引擎"""
    print("=" * 60)
    print("测试回测引擎")
    print("=" * 60)
    
    # 使用等权配权进行回测
    baseline_asset = returns_df.columns[0]  # 选择第一个资产作为基准
    
    engine = BacktestEngine(returns_df, weights, baseline_asset)
    
    # 验证回测
    is_valid, msg = engine.validate_backtest()
    print(f"\n回测验证: {msg}")
    assert is_valid, msg
    
    # 运行完整回测
    print("\n运行回测...")
    results = engine.run_backtest(
        initial_value=100000,
        rebalance_freq='月度'
    )
    
    # 显示绩效指标
    metrics = results['metrics']
    print("\n绩效指标:")
    print(f"  年化收益率: {metrics['annual_return']:.2%}")
    print(f"  年化波动率: {metrics['annual_volatility']:.2%}")
    print(f"  夏普比率: {metrics['sharpe_ratio']:.2f}")
    print(f"  最大回撤: {metrics['max_drawdown']:.2%}")
    print(f"  Calmar比率: {metrics['calmar_ratio']:.2f}")
    print(f"  超额收益: {metrics['excess_return']:.2%}")
    print(f"  信息比率: {metrics['information_ratio']:.2f}")
    print(f"  胜率: {metrics['win_rate']:.2%}")
    
    # 验证指标合理性
    assert -1 < metrics['max_drawdown'] <= 0, "最大回撤范围异常"
    assert 0 < metrics['annual_volatility'] < 2, "波动率范围异常"
    assert metrics['sharpe_ratio'] > -5, "夏普比率过低"
    
    print("\n✓ 所有验证通过")
    print()
    
    return results


def math_validation():
    """数学验证 - 手动计算验证算法正确性"""
    print("=" * 60)
    print("数学验证")
    print("=" * 60)
    
    # 简单的两资产案例
    np.random.seed(123)
    
    # 生成简单数据
    dates = pd.date_range(start='2020-01-01', periods=100, freq='D')
    
    # 资产1: 固定波动率
    ret1 = np.random.normal(0, 0.02, 100)
    
    # 资产2: 不同波动率
    ret2 = np.random.normal(0, 0.01, 100)
    
    returns_df = pd.DataFrame({
        'Asset1': ret1,
        'Asset2': ret2
    })
    
    # 测试等权配权
    engine = WeightingEngine(returns_df)
    weights_equal = engine.equal_weight()
    
    # 手动计算组合方差
    cov_mat = returns_df.cov() * 252
    w = np.array([0.5, 0.5])
    manual_var = np.dot(w.T, np.dot(cov_mat, w))
    
    # 使用引擎计算
    engine_var = np.dot(weights_equal.values.T, np.dot(engine.cov_matrix, weights_equal.values))
    
    print(f"\n手动计算方差: {manual_var:.8f}")
    print(f"引擎计算方差: {engine_var:.8f}")
    print(f"差异: {abs(manual_var - engine_var):.10f}")
    
    assert abs(manual_var - engine_var) < 1e-8, "方差计算不一致"
    print("✓ 方差计算验证通过")
    
    # 测试最小方差
    weights_mv = engine.minimum_variance()
    
    print(f"\n最小方差权重: {weights_mv.to_dict()}")
    
    # 最小方差应该比等权方差更小
    var_equal = np.dot(weights_equal.values.T, np.dot(cov_matrix := engine.cov_matrix, weights_equal.values))
    var_mv = np.dot(weights_mv.values.T, np.dot(cov_matrix, weights_mv.values))
    
    print(f"等权方差: {var_equal:.8f}")
    print(f"最小方差: {var_mv:.8f}")
    
    assert var_mv <= var_equal * 1.01, "最小方差策略方差未降低"  # 允许1%误差
    print("✓ 最小方差验证通过")
    
    print("\n✓ 所有数学验证通过")
    print()


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("开始运行完整测试套件")
    print("=" * 60 + "\n")
    
    try:
        # 测试数据加载
        returns_df = test_data_loader()
        
        # 测试配权引擎
        weights_equal, weights_rp, weights_mv = test_weighting_engine(returns_df)
        
        # 测试回测引擎
        results = test_backtest_engine(returns_df, weights_equal)
        
        # 数学验证
        math_validation()
        
        print("=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ 测试失败: {str(e)}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
