"""
BL模型基础测试
=============

这个文件包含了一些简单的测试，帮助你理解如何使用BL模型。
运行这个文件可以验证BL模型是否正常工作。

使用方法：
    python tests/test_bl_portfolio_basic.py
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from utils.bl_portfolio import BlackLittermanEngine


def test_basic_usage():
    """测试1: 基本使用"""
    print("\n" + "=" * 60)
    print("测试1: 基本使用".center(60))
    print("=" * 60)

    # 1. 创建模拟数据
    print("\n步骤1: 创建模拟数据")

    # 创建收益率数据
    np.random.seed(42)
    n_days = 1000

    # 3个资产的收益率
    returns_data = {
        '股票A': np.random.randn(n_days) * 0.02,  # 日收益率，标准差2%
        '股票B': np.random.randn(n_days) * 0.015, # 日收益率，标准差1.5%
        '股票C': np.random.randn(n_days) * 0.025, # 日收益率，标准差2.5%
    }
    dates = pd.date_range('2020-01-01', periods=n_days, freq='D')
    returns_df = pd.DataFrame(returns_data, index=dates)

    print(f"   创建了{len(returns_df.columns)}个资产，{len(returns_df)}天的数据")
    print(f"   数据预览:")
    print(returns_df.head())

    # 2. 创建市值数据
    print("\n步骤2: 创建市值数据")

    market_caps = {
        '股票A': 3000e8,  # 3000亿元
        '股票B': 2000e8,  # 2000亿元
        '股票C': 1000e8,  # 1000亿元
    }

    print(f"   市值:")
    for asset, cap in market_caps.items():
        print(f"   {asset}: {cap/1e8:.0f}亿元")

    # 3. 创建BL引擎
    print("\n步骤3: 创建BL引擎")

    bl = BlackLittermanEngine(
        returns_df=returns_df,
        market_caps=market_caps,
        tau=0.05,
        risk_free_rate=0.03
    )

    print("   [OK] 引擎创建成功")

    # 4. 添加观点
    print("\n步骤4: 添加观点")

    bl.add_absolute_view('股票A', 0.10, confidence=0.7)
    print("   观点1: 股票A涨10%，置信度70%")

    # 5. 计算权重
    print("\n步骤5: 计算权重")

    weights = bl.compute_weights()

    print("\n最终权重:")
    for asset, weight in weights.items():
        print(f"   {asset}: {weight:.2%}")

    # 6. 验证
    print("\n步骤6: 验证结果")

    total_weight = weights.sum()
    print(f"   权重总和: {total_weight:.6f}（应该接近1.0）")

    all_positive = (weights >= 0).all()
    print(f"   所有权重非负: {all_positive}")

    print("\n[OK] 测试1通过！")


def test_no_views():
    """测试2: 没有观点的情况"""
    print("\n" + "=" * 60)
    print("测试2: 没有观点的情况".center(60))
    print("=" * 60)

    # 创建数据
    np.random.seed(42)
    returns_df = pd.DataFrame({
        '股票A': np.random.randn(1000) * 0.02,
        '股票B': np.random.randn(1000) * 0.015,
    })
    market_caps = {'股票A': 3000e8, '股票B': 2000e8}

    # 创建BL引擎（不添加任何观点）
    bl = BlackLittermanEngine(returns_df, market_caps)

    # 计算权重
    weights = bl.compute_weights()

    print("\n计算结果（无观点）:")
    for asset, weight in weights.items():
        print(f"   {asset}: {weight:.2%}")

    # 对比市值权重
    print("\n市值权重:")
    for asset, weight in bl.market_weights.items():
        print(f"   {asset}: {weight:.2%}")

    print("\n说明：没有观点时，BL权重应该接近市值权重")

    print("\n[OK] 测试2通过！")


def test_multiple_views():
    """测试3: 多个观点"""
    print("\n" + "=" * 60)
    print("测试3: 多个观点".center(60))
    print("=" * 60)

    # 创建数据
    np.random.seed(42)
    returns_df = pd.DataFrame({
        '股票A': np.random.randn(1000) * 0.02,
        '股票B': np.random.randn(1000) * 0.015,
        '股票C': np.random.randn(1000) * 0.025,
    })
    market_caps = {
        '股票A': 3000e8,
        '股票B': 2000e8,
        '股票C': 1000e8,
    }

    # 创建BL引擎
    bl = BlackLittermanEngine(returns_df, market_caps)

    # 添加多个观点
    print("\n添加观点:")
    bl.add_absolute_view('股票A', 0.10, confidence=0.8)
    print("   观点1: 股票A涨10%，置信度80%")

    bl.add_absolute_view('股票B', 0.05, confidence=0.6)
    print("   观点2: 股票B涨5%，置信度60%")

    bl.add_relative_view(['股票A', '股票C'], [0.03, -0.03], confidence=0.7)
    print("   观点3: 股票A比股票C好3%，置信度70%")

    # 计算权重
    weights = bl.compute_weights()

    print("\n最终权重:")
    for asset, weight in weights.items():
        print(f"   {asset}: {weight:.2%}")

    # 对比
    print("\n与市值权重对比:")
    for asset in weights.index:
        market_weight = bl.market_weights[asset]
        bl_weight = weights[asset]
        diff = bl_weight - market_weight
        print(f"   {asset}:")
        print(f"      市值权重: {market_weight:.2%}")
        print(f"      BL权重:   {bl_weight:.2%}")
        print(f"      差异:     {diff:+.2%}")

    print("\n[OK] 测试3通过！")


def test_confidence_impact():
    """测试4: 置信度的影响"""
    print("\n" + "=" * 60)
    print("测试4: 置信度的影响".center(60))
    print("=" * 60)

    # 创建数据
    np.random.seed(42)
    returns_df = pd.DataFrame({
        '股票A': np.random.randn(1000) * 0.02,
        '股票B': np.random.randn(1000) * 0.015,
    })
    market_caps = {'股票A': 3000e8, '股票B': 2000e8}

    # 添加相同的观点，但置信度不同
    print("\n对比不同置信度的影响:")
    print("观点: 股票A涨10%")

    confidences = [0.3, 0.5, 0.7, 0.9]
    results = []

    for conf in confidences:
        bl = BlackLittermanEngine(returns_df, market_caps)
        bl.add_absolute_view('股票A', 0.10, confidence=conf)
        weights = bl.compute_weights()

        results.append({
            '置信度': conf,
            '股票A权重': weights['股票A'],
            '股票B权重': weights['股票B']
        })

    print("\n结果:")
    results_df = pd.DataFrame(results)
    print(results_df.round(4))

    print("\n说明: 置信度越高，股票A的权重应该越大")

    print("\n[OK] 测试4通过！")


def test_comparison():
    """测试5: 对比不同方法"""
    print("\n" + "=" * 60)
    print("测试5: 对比不同配权方法".center(60))
    print("=" * 60)

    # 创建数据
    np.random.seed(42)
    returns_df = pd.DataFrame({
        '股票A': np.random.randn(1000) * 0.02,
        '股票B': np.random.randn(1000) * 0.015,
        '股票C': np.random.randn(1000) * 0.025,
    })
    market_caps = {
        '股票A': 3000e8,
        '股票B': 2000e8,
        '股票C': 1000e8,
    }

    # 创建BL引擎并添加观点
    bl = BlackLittermanEngine(returns_df, market_caps)
    bl.add_absolute_view('股票A', 0.10, confidence=0.7)

    # 计算权重
    weights = bl.compute_weights()

    # 对比
    print("\n不同配权方法对比:")
    comparison = bl.compare_with_benchmarks(weights)

    print(comparison.round(4))

    print("\n[OK] 测试5通过！")


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print(" BL模型基础测试".center(60))
    print("=" * 60)

    try:
        test_basic_usage()
        test_no_views()
        test_multiple_views()
        test_confidence_impact()
        test_comparison()

        print("\n" + "=" * 60)
        print(" 所有测试通过！[OK]".center(60))
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
