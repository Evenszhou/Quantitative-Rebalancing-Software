"""
Tushare数据加载器使用示例

演示如何使用TushareLoader获取数据并运行Black-Litterman模型
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

from utils.tushare_loader import TushareLoader

def example_basic_usage():
    """示例1: 基本使用"""
    print("=" * 50)
    print("示例1: 获取股票收益率和市值数据")
    print("=" * 50)

    # 初始化加载器（确保设置了环境变量 TUSHARE_TOKEN）
    loader = TushareLoader()

    # 定义股票池
    ts_codes = ['000001.SZ', '600000.SH', '000002.SZ']

    # 获取收益率数据
    print("\n获取收益率数据...")
    returns_df = loader.get_returns(
        ts_codes=ts_codes,
        start_date='2022-01-01',
        end_date='2023-12-31'
    )

    print(f"✅ 获取到{len(returns_df)}天的数据")
    print(f"时间范围: {returns_df.index.min()} 到 {returns_df.index.max()}")
    print(f"\n收益率数据（前5行）:")
    print(returns_df.head())

    # 获取市值数据
    print("\n获取市值数据...")
    market_caps = loader.get_market_caps(ts_codes=ts_codes)

    print("\n市值数据:")
    for code, cap in market_caps.items():
        print(f"  {code}: {cap/1e8:.2f}亿元")

    return returns_df, market_caps


def example_with_bl_model():
    """示例2: 配合BL模型使用"""
    print("\n" + "=" * 50)
    print("示例2: 使用Tushare数据运行BL模型")
    print("=" * 50)

    # 注意：这个示例需要bl_portfolio.py实现后才能运行
    try:
        from utils.bl_portfolio import BlackLittermanEngine

        # 获取数据
        loader = TushareLoader()
        returns_df = loader.get_returns(
            ts_codes=['000001.SZ', '600000.SH', '000002.SZ'],
            start_date='2022-01-01'
        )
        market_caps = loader.get_market_caps(
            ts_codes=['000001.SZ', '600000.SH', '000002.SZ']
        )

        # 创建BL引擎
        bl = BlackLittermanEngine(
            returns_df=returns_df,
            market_caps=market_caps,
            tau=0.05
        )

        # 添加观点
        print("\n添加投研观点...")
        bl.add_absolute_view('000001.SZ', 0.10, confidence=0.7)
        print("  - 观点1: 平安银行预期收益10%，置信度70%")

        # 计算权重
        print("\n计算BL权重...")
        weights = bl.compute_weights()

        print("\n配权结果:")
        for asset, weight in weights.items():
            print(f"  {asset}: {weight:.2%}")

    except ImportError:
        print("\n⚠️  bl_portfolio.py还未实现，请先完成BL模型的编码")


def example_stock_list():
    """示例3: 获取股票列表"""
    print("\n" + "=" * 50)
    print("示例3: 获取股票列表")
    print("=" * 50)

    loader = TushareLoader()

    # 获取所有上市股票
    print("\n获取股票列表...")
    stock_list = loader.get_stock_list(list_status='L')

    print(f"✅ 共{len(stock_list)}只股票")
    print(f"\n前10只股票:")
    print(stock_list.head(10))

    # 按市场统计
    print(f"\n按市场统计:")
    print(stock_list['market'].value_counts())


def example_cache_usage():
    """示例4: 缓存使用"""
    print("\n" + "=" * 50)
    print("示例4: 缓存机制演示")
    print("=" * 50)

    loader = TushareLoader()
    ts_codes = ['000001.SZ']

    # 第一次获取（会调用API）
    print("\n第一次获取数据（调用API）...")
    import time
    start = time.time()
    returns_df = loader.get_returns(ts_codes, '2023-01-01', '2023-12-31')
    time1 = time.time() - start
    print(f"  耗时: {time1:.2f}秒")

    # 第二次获取（从缓存读取）
    print("\n第二次获取数据（从缓存）...")
    start = time.time()
    returns_df = loader.get_returns(ts_codes, '2023-01-01', '2023-12-31')
    time2 = time.time() - start
    print(f"  耗时: {time2:.2f}秒")

    print(f"\n缓存加速: {time1/time2:.1f}x")


def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print(" Tushare数据加载器使用示例".center(60))
    print("=" * 60)

    # 检查token
    import os
    if not os.environ.get('TUSHARE_TOKEN'):
        print("\n⚠️  请先设置环境变量:")
        print("   export TUSHARE_TOKEN='your_token_here'")
        print("\n或者在代码中传入:")
        print("   loader = TushareLoader(token='your_token_here')")
        return

    try:
        # 运行示例
        example_basic_usage()
        # example_with_bl_model()  # 等BL模型实现后再启用
        # example_stock_list()
        # example_cache_usage()

        print("\n" + "=" * 60)
        print(" 所有示例运行完成！")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 运行出错: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
