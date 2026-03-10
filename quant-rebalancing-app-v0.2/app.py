"""
量化配权软件 v0.2 - Streamlit版本
主程序入口
新增功能：
- 最优夏普配权方法
- 灵活的交易成本设置
- 3个sheet的Excel导出（仓位、绩效、验算）
"""
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import sys
from io import BytesIO
from datetime import datetime

# 添加utils到路径
sys.path.append(str(Path(__file__).parent))

from utils.data_loader import DataLoader
from utils.weighting import WeightingEngine
from utils.backtest import BacktestEngine, TransactionCost

# 页面配置
st.set_page_config(
    page_title="量化配权软件 v0.2",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 标题
st.title("📊 量化配权软件 v0.2")
st.markdown("**新增功能**：最优夏普配权 | 灵活交易成本 | 详细验算报告")
st.markdown("---")

# 初始化session state
if 'assets_data' not in st.session_state:
    st.session_state.assets_data = {}
if 'assets_prices' not in st.session_state:
    st.session_state.assets_prices = {}
if 'weights' not in st.session_state:
    st.session_state.weights = None
if 'backtest_results' not in st.session_state:
    st.session_state.backtest_results = None
if 'transaction_costs' not in st.session_state:
    st.session_state.transaction_costs = {}

# 侧边栏 - 导航
st.sidebar.title("功能导航")
page = st.sidebar.radio(
    "选择功能",
    ["1. 数据管理", "2. 配权计算", "3. 交易成本设置", "4. 回测分析", "5. 结果导出"]
)

# 页面1: 数据管理
if page == "1. 数据管理":
    st.header("📁 数据管理")
    
    # 文件上传
    st.subheader("上传资产数据")
    uploaded_files = st.file_uploader(
        "上传多个资产文件（Excel或CSV）",
        type=['xlsx', 'csv'],
        accept_multiple_files=True,
        help="每个文件代表一个资产，文件名将被用作资产名称"
    )
    
    if uploaded_files:
        data_loader = DataLoader()
        
        for file in uploaded_files:
            try:
                # 读取文件
                file_name = Path(file.name).stem
                df = data_loader.load_file(file)
                
                # 存储到session state
                st.session_state.assets_data[file_name] = df
                
                # 如果有价格数据，也存储
                if '收盘价' in df.columns or 'close' in df.columns:
                    st.session_state.assets_prices[file_name] = df
                
                st.success(f"✅ 已加载: {file_name}")
            except Exception as e:
                st.error(f"❌ 加载失败 {file.name}: {str(e)}")
    
    # 数据预览
    if st.session_state.assets_data:
        st.markdown("---")
        st.subheader("数据预览")
        
        # 选择资产查看
        selected_asset = st.selectbox(
            "选择资产查看详情",
            list(st.session_state.assets_data.keys())
        )
        
        if selected_asset:
            df = st.session_state.assets_data[selected_asset]
            
            # 基本统计
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("数据行数", len(df))
            with col2:
                st.metric("数据列数", len(df.columns))
            with col3:
                if '日期' in df.columns or df.index.name == '日期':
                    st.metric("时间跨度", f"{len(df)} 天")
            
            # 数据表格
            st.dataframe(df.head(10), use_container_width=True)
            
            # 数据列信息
            with st.expander("查看列信息"):
                st.write(df.dtypes.to_frame('数据类型'))

# 页面2: 配权计算
elif page == "2. 配权计算":
    st.header("⚖️ 配权计算")
    
    if not st.session_state.assets_data:
        st.warning("⚠️ 请先上传数据")
    else:
        # 选择配权方法
        st.subheader("选择配权方法")
        method = st.selectbox(
            "配权算法",
            ["等权配权 (Equal Weight)", 
             "风险平价 (Risk Parity)", 
             "最小方差 (Minimum Variance)",
             "最优夏普 (Maximum Sharpe) 🆕"]
        )
        
        # 如果选择最优夏普，显示额外参数
        if "最优夏普" in method:
            col1, col2 = st.columns(2)
            with col1:
                risk_free_rate = st.number_input(
                    "无风险利率（年化）",
                    min_value=0.0,
                    max_value=0.1,
                    value=0.03,
                    step=0.005,
                    format="%.3f"
                )
            with col2:
                allow_short = st.checkbox("允许做空", value=False)
        
        # 选择资产
        st.subheader("选择参与配权的资产")
        selected_assets = st.multiselect(
            "勾选资产",
            list(st.session_state.assets_data.keys()),
            default=list(st.session_state.assets_data.keys())
        )
        
        if selected_assets and st.button("开始计算", type="primary"):
            with st.spinner("计算中..."):
                # 准备数据
                data_loader = DataLoader()
                returns_df = data_loader.prepare_returns(
                    {k: st.session_state.assets_data[k] for k in selected_assets}
                )
                
                # 配权计算
                engine = WeightingEngine(returns_df)
                
                if "等权" in method:
                    weights = engine.equal_weight()
                elif "风险平价" in method:
                    weights = engine.risk_parity()
                elif "最小方差" in method:
                    weights = engine.minimum_variance()
                elif "最优夏普" in method:
                    weights = engine.maximum_sharpe(
                        risk_free_rate=risk_free_rate,
                        allow_short=allow_short
                    )
                
                # 保存结果
                st.session_state.weights = weights
                
                # 显示结果
                st.success("✅ 计算完成！")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("权重分配")
                    weights_df = pd.DataFrame({
                        '资产': weights.index,
                        '权重': weights.values
                    })
                    st.dataframe(weights_df, use_container_width=True)
                
                with col2:
                    st.subheader("权重饼图")
                    import plotly.express as px
                    fig = px.pie(weights_df, values='权重', names='资产', title='资产配置权重')
                    st.plotly_chart(fig, use_container_width=True)
                
                # 显示组合指标
                st.subheader("组合指标")
                metrics = engine.get_portfolio_metrics(weights)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("预期年化收益", f"{metrics['annual_return']:.2%}")
                with col2:
                    st.metric("预期年化波动", f"{metrics['annual_volatility']:.2%}")
                with col3:
                    st.metric("预期夏普比率", f"{metrics['sharpe_ratio']:.2f}")

# 页面3: 交易成本设置（新增）
elif page == "3. 交易成本设置":
    st.header("💰 交易成本设置 🆕")
    
    if not st.session_state.weights:
        st.warning("⚠️ 请先进行配权计算")
    else:
        st.markdown("""
        **说明**：为每个资产设置交易成本，包括：
        - **买边成本**：买入时的手续费（百分比或固定金额）
        - **卖边成本**：卖出时的手续费+印花税（百分比或固定金额）
        - **滑点**：交易执行时的价格偏差
        """)
        
        # 全局设置
        st.subheader("全局默认设置")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            default_buy_pct = st.number_input(
                "默认买入成本（%）",
                min_value=0.0,
                max_value=1.0,
                value=0.1,
                step=0.01,
                format="%.3f"
            ) / 100
        with col2:
            default_sell_pct = st.number_input(
                "默认卖出成本（%）",
                min_value=0.0,
                max_value=1.0,
                value=0.13,
                step=0.01,
                format="%.3f"
            ) / 100
        with col3:
            default_slippage = st.number_input(
                "默认滑点（%）",
                min_value=0.0,
                max_value=0.5,
                value=0.05,
                step=0.01,
                format="%.3f"
            ) / 100
        with col4:
            default_fixed = st.number_input(
                "固定成本（元）",
                min_value=0.0,
                value=5.0,
                step=1.0
            )
        
        # 为每个资产单独设置
        st.subheader("各资产成本设置")
        
        assets = st.session_state.weights.index.tolist()
        
        # 使用expander让用户展开设置
        for asset in assets:
            with st.expander(f"📊 {asset}", expanded=False):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    buy_pct = st.number_input(
                        f"{asset} 买入成本（%）",
                        min_value=0.0,
                        max_value=1.0,
                        value=default_buy_pct * 100,
                        step=0.01,
                        format="%.3f",
                        key=f"buy_pct_{asset}"
                    ) / 100
                    
                    buy_fixed = st.number_input(
                        f"{asset} 买入固定成本（元）",
                        min_value=0.0,
                        value=default_fixed,
                        step=1.0,
                        key=f"buy_fixed_{asset}"
                    )
                
                with col2:
                    sell_pct = st.number_input(
                        f"{asset} 卖出成本（%）",
                        min_value=0.0,
                        max_value=1.0,
                        value=default_sell_pct * 100,
                        step=0.01,
                        format="%.3f",
                        key=f"sell_pct_{asset}"
                    ) / 100
                    
                    sell_fixed = st.number_input(
                        f"{asset} 卖出固定成本（元）",
                        min_value=0.0,
                        value=default_fixed,
                        step=1.0,
                        key=f"sell_fixed_{asset}"
                    )
                
                with col3:
                    slippage = st.number_input(
                        f"{asset} 滑点（%）",
                        min_value=0.0,
                        max_value=0.5,
                        value=default_slippage * 100,
                        step=0.01,
                        format="%.3f",
                        key=f"slippage_{asset}"
                    ) / 100
                
                # 保存到session state
                st.session_state.transaction_costs[asset] = TransactionCost(
                    buy_cost_pct=buy_pct,
                    sell_cost_pct=sell_pct,
                    buy_cost_fixed=buy_fixed,
                    sell_cost_fixed=sell_fixed,
                    slippage_pct=slippage
                )
        
        # 显示成本汇总
        st.subheader("成本汇总")
        cost_summary = []
        for asset in assets:
            if asset in st.session_state.transaction_costs:
                cost = st.session_state.transaction_costs[asset]
                cost_summary.append({
                    '资产': asset,
                    '买入成本': f"{cost.buy_cost_pct*100:.2f}%",
                    '卖出成本': f"{cost.sell_cost_pct*100:.2f}%",
                    '滑点': f"{cost.slippage_pct*100:.2f}%",
                    '双边总成本': f"{(cost.buy_cost_pct + cost.sell_cost_pct + cost.slippage_pct*2)*100:.2f}%"
                })
        
        if cost_summary:
            st.dataframe(pd.DataFrame(cost_summary), use_container_width=True)

# 页面4: 回测分析
elif page == "4. 回测分析":
    st.header("📈 回测分析")
    
    if st.session_state.weights is None:
        st.warning("⚠️ 请先进行配权计算")
    else:
        # 选择基准
        st.subheader("选择回测基准")
        baseline_asset = st.selectbox(
            "选择基准资产",
            list(st.session_state.assets_data.keys())
        )
        
        # 回测设置
        col1, col2 = st.columns(2)
        with col1:
            rebalance_freq = st.selectbox(
                "再平衡频率",
                ["月度", "季度", "年度", "不调仓"]
            )
        with col2:
            initial_value = st.number_input(
                "初始资金",
                min_value=10000,
                value=100000,
                step=10000
            )
        
        # 交易成本设置提醒
        if not st.session_state.transaction_costs:
            st.info("💡 提示：建议先在'交易成本设置'页面配置成本参数，使回测更真实")
        
        if st.button("开始回测", type="primary"):
            with st.spinner("回测中..."):
                # 准备数据
                data_loader = DataLoader()
                returns_df = data_loader.prepare_returns(st.session_state.assets_data)
                
                # 准备价格数据（如果有）
                prices_df = None
                if st.session_state.assets_prices:
                    prices_df = data_loader.prepare_returns(st.session_state.assets_prices)
                
                # 回测
                engine = BacktestEngine(
                    returns_df,
                    st.session_state.weights,
                    baseline_asset,
                    prices_df
                )
                
                # 转换transaction_costs格式
                transaction_costs = {}
                for asset in st.session_state.weights.index:
                    if asset in st.session_state.transaction_costs:
                        transaction_costs[asset] = st.session_state.transaction_costs[asset]
                    else:
                        # 使用默认成本
                        transaction_costs[asset] = TransactionCost()
                
                results = engine.run_backtest(
                    initial_value=initial_value,
                    rebalance_freq=rebalance_freq,
                    transaction_costs=transaction_costs
                )
                
                st.session_state.backtest_results = results
                
                # 显示绩效
                st.success("✅ 回测完成！")
                
                # 绩效指标
                st.subheader("绩效指标")
                metrics = results['metrics']
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("年化收益率", f"{metrics['annual_return']:.2%}")
                with col2:
                    st.metric("年化波动率", f"{metrics['annual_volatility']:.2%}")
                with col3:
                    st.metric("夏普比率", f"{metrics['sharpe_ratio']:.2f}")
                with col4:
                    st.metric("最大回撤", f"{metrics['max_drawdown']:.2%}")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Calmar比率", f"{metrics['calmar_ratio']:.2f}")
                with col2:
                    st.metric("Sortino比率", f"{metrics['sortino_ratio']:.2f}")
                with col3:
                    st.metric("总交易次数", f"{metrics['total_trades']}")
                with col4:
                    st.metric("总交易成本", f"¥{metrics['total_transaction_cost']:.2f}")
                
                # 收益率曲线对比
                st.subheader("收益率曲线对比")
                import plotly.graph_objects as go
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=results['returns_series'].index,
                    y=results['returns_series']['portfolio'],
                    mode='lines',
                    name='组合收益率',
                    line=dict(color='blue', width=2)
                ))
                fig.add_trace(go.Scatter(
                    x=results['returns_series'].index,
                    y=results['returns_series']['baseline'],
                    mode='lines',
                    name=f'{baseline_asset}收益率',
                    line=dict(color='red', width=2, dash='dash')
                ))
                
                # 标记调仓点
                if results['trade_log']:
                    rebalance_dates = [t['date'] for t in results['trade_log']]
                    fig.add_trace(go.Scatter(
                        x=rebalance_dates,
                        y=[0] * len(rebalance_dates),
                        mode='markers',
                        name='调仓点',
                        marker=dict(color='green', size=8, symbol='triangle-up')
                    ))
                
                fig.update_layout(
                    title="累计收益率对比",
                    xaxis_title="日期",
                    yaxis_title="累计收益率",
                    hovermode='x unified'
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # 回撤分析
                st.subheader("回撤分析")
                fig2 = go.Figure()
                fig2.add_trace(go.Scatter(
                    x=results['drawdown_series'].index,
                    y=results['drawdown_series'],
                    mode='lines',
                    name='组合回撤',
                    fill='tozeroy',
                    line=dict(color='red')
                ))
                fig2.update_layout(
                    title="组合回撤",
                    xaxis_title="日期",
                    yaxis_title="回撤"
                )
                st.plotly_chart(fig2, use_container_width=True)
                
                # 仓位变化（新增）
                st.subheader("仓位变化 🆕")
                position_series = results['position_series']
                
                fig3 = go.Figure()
                for asset in position_series.columns:
                    fig3.add_trace(go.Scatter(
                        x=position_series.index,
                        y=position_series[asset],
                        mode='lines',
                        name=asset,
                        stackgroup='one'
                    ))
                
                fig3.update_layout(
                    title="资产仓位时间序列",
                    xaxis_title="日期",
                    yaxis_title="市值（元）",
                    hovermode='x unified'
                )
                st.plotly_chart(fig3, use_container_width=True)

# 页面5: 结果导出
elif page == "5. 结果导出":
    st.header("💾 结果导出 🆕")
    
    if st.session_state.weights is None:
        st.warning("⚠️ 没有可导出的结果")
    else:
        st.markdown("""
        **导出内容（3个Sheet）**：
        1. **仓位时间序列**：每个交易日的各资产仓位
        2. **绩效指标**：年化收益、夏普比率、最大回撤等
        3. **验算页面**：价格、仓位、净值变化、调仓标记
        """)
        
        # 准备数据
        weights_df = pd.DataFrame({
            '资产': st.session_state.weights.index,
            '权重': st.session_state.weights.values
        })
        
        # 导出Excel（3个sheet）
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            # Sheet 1: 仓位时间序列
            if st.session_state.backtest_results:
                position_series = st.session_state.backtest_results['position_series']
                
                # 添加日期列
                position_series_export = position_series.copy()
                position_series_export.insert(0, '日期', position_series_export.index)
                
                # 计算权重
                for asset in position_series.columns:
                    position_series_export[f'{asset}_权重'] = (
                        position_series[asset] / position_series.sum(axis=1)
                    )
                
                position_series_export.to_excel(
                    writer, 
                    sheet_name='仓位时间序列', 
                    index=False
                )
            else:
                weights_df.to_excel(writer, sheet_name='仓位时间序列', index=False)
            
            # Sheet 2: 绩效指标
            if st.session_state.backtest_results:
                metrics = st.session_state.backtest_results['metrics']
                metrics_df = pd.DataFrame([
                    {'指标': '年化收益率', '值': f"{metrics['annual_return']:.2%}"},
                    {'指标': '年化波动率', '值': f"{metrics['annual_volatility']:.2%}"},
                    {'指标': '夏普比率', '值': f"{metrics['sharpe_ratio']:.2f}"},
                    {'指标': 'Sortino比率', '值': f"{metrics['sortino_ratio']:.2f}"},
                    {'指标': '最大回撤', '值': f"{metrics['max_drawdown']:.2%}"},
                    {'指标': 'Calmar比率', '值': f"{metrics['calmar_ratio']:.2f}"},
                    {'指标': '基准收益率', '值': f"{metrics['baseline_return']:.2%}"},
                    {'指标': '超额收益', '值': f"{metrics['excess_return']:.2%}"},
                    {'指标': '信息比率', '值': f"{metrics['information_ratio']:.2f}"},
                    {'指标': '胜率', '值': f"{metrics['win_rate']:.2%}"},
                    {'指标': '总交易次数', '值': f"{metrics['total_trades']}"},
                    {'指标': '总交易成本', '值': f"¥{metrics['total_transaction_cost']:.2f}"},
                ])
                metrics_df.to_excel(writer, sheet_name='绩效指标', index=False)
            else:
                pd.DataFrame({'提示': ['请先运行回测分析']}).to_excel(
                    writer, 
                    sheet_name='绩效指标', 
                    index=False
                )
            
            # Sheet 3: 验算页面
            if st.session_state.backtest_results:
                validation_data = st.session_state.backtest_results['validation_data']
                
                # 添加日期列
                validation_data_export = validation_data.copy()
                validation_data_export.insert(0, '日期', validation_data_export.index)
                
                validation_data_export.to_excel(
                    writer, 
                    sheet_name='验算页面', 
                    index=False
                )
            else:
                pd.DataFrame({'提示': ['请先运行回测分析']}).to_excel(
                    writer, 
                    sheet_name='验算页面', 
                    index=False
                )
        
        # 下载按钮
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.download_button(
            label="📥 下载完整Excel报告（3个Sheet）",
            data=buffer.getvalue(),
            file_name=f"portfolio_report_v0.2_{timestamp}.xlsx",
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            type="primary"
        )
        
        # 分项导出
        st.markdown("---")
        st.subheader("分项导出")
        
        col1, col2 = st.columns(2)
        with col1:
            # 导出权重CSV
            csv = weights_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="下载权重CSV",
                data=csv,
                file_name="portfolio_weights.csv",
                mime='text/csv'
            )
        
        with col2:
            # 导出仓位CSV
            if st.session_state.backtest_results:
                position_csv = st.session_state.backtest_results['position_series'].to_csv().encode('utf-8-sig')
                st.download_button(
                    label="下载仓位CSV",
                    data=position_csv,
                    file_name="position_series.csv",
                    mime='text/csv'
                )

# 页脚
st.markdown("---")
st.markdown("💡 **v0.2 新功能**：最优夏普配权 | 灵活交易成本 | 3个Sheet验算报告")
st.markdown("遇到问题请联系开发者")
