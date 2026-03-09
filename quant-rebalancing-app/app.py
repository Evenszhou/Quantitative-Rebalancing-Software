"""
量化配权软件 - Streamlit版本
主程序入口
"""
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# 添加utils到路径
sys.path.append(str(Path(__file__).parent))

from utils.data_loader import DataLoader
from utils.weighting import WeightingEngine
from utils.backtest import BacktestEngine

# 页面配置
st.set_page_config(
    page_title="量化配权软件",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 标题
st.title("📊 量化配权软件")
st.markdown("---")

# 初始化session state
if 'assets_data' not in st.session_state:
    st.session_state.assets_data = {}
if 'weights' not in st.session_state:
    st.session_state.weights = None
if 'backtest_results' not in st.session_state:
    st.session_state.backtest_results = None

# 侧边栏 - 导航
st.sidebar.title("功能导航")
page = st.sidebar.radio(
    "选择功能",
    ["1. 数据管理", "2. 配权计算", "3. 回测分析", "4. 结果导出"]
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
             "最小方差 (Minimum Variance)"]
        )
        
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

# 页面3: 回测分析
elif page == "3. 回测分析":
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
        
        if st.button("开始回测", type="primary"):
            with st.spinner("回测中..."):
                # 准备数据
                data_loader = DataLoader()
                returns_df = data_loader.prepare_returns(st.session_state.assets_data)
                
                # 回测
                engine = BacktestEngine(
                    returns_df,
                    st.session_state.weights,
                    baseline_asset
                )
                
                results = engine.run_backtest(
                    initial_value=initial_value,
                    rebalance_freq=rebalance_freq
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

# 页面4: 结果导出
elif page == "4. 结果导出":
    st.header("💾 结果导出")
    
    if st.session_state.weights is None:
        st.warning("⚠️ 没有可导出的结果")
    else:
        # 导出权重
        st.subheader("导出配权结果")
        weights_df = pd.DataFrame({
            '资产': st.session_state.weights.index,
            '权重': st.session_state.weights.values
        })
        
        col1, col2 = st.columns(2)
        with col1:
            csv = weights_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="下载权重CSV",
                data=csv,
                file_name="portfolio_weights.csv",
                mime='text/csv'
            )
        
        with col2:
            from io import BytesIO
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                weights_df.to_excel(writer, sheet_name='权重', index=False)
                if st.session_state.backtest_results:
                    metrics_df = pd.DataFrame(
                        st.session_state.backtest_results['metrics'],
                        index=['值']
                    ).T
                    metrics_df.to_excel(writer, sheet_name='绩效指标')
            
            st.download_button(
                label="下载Excel报告",
                data=buffer.getvalue(),
                file_name="portfolio_report.xlsx",
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )

# 页脚
st.markdown("---")
st.markdown("💡 提示：遇到问题请联系开发者")
