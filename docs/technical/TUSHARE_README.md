# Tushare Pro数据集成

## 📋 概述

已为项目集成Tushare Pro数据源，可以：
- ✅ 自动获取股票日线行情
- ✅ 获取市值数据（用于BL模型）
- ✅ 获取股票列表
- ✅ 本地缓存（减少API调用）

---

## 🚀 快速开始

### 1. 设置Token

**方式A: 环境变量（推荐）**
```bash
# 在~/.bashrc或~/.zshrc中添加
export TUSHARE_TOKEN='dbf81e30b51100a7cb4ba5517286a1755a10c21602e130a15264f1b1'

# 重新加载配置
source ~/.bashrc
```

**方式B: 临时设置**
```bash
# 当前会话
export TUSHARE_TOKEN='dbf81e30b51100a7cb4ba5517286a1755a10c21602e130a15264f1b1'
```

### 2. 使用示例

```python
from utils.tushare_loader import TushareLoader

# 初始化（自动读取环境变量）
loader = TushareLoader()

# 获取收益率数据
returns_df = loader.get_returns(
    ts_codes=['000001.SZ', '600000.SH', '000002.SZ'],
    start_date='2022-01-01',
    end_date='2023-12-31'
)

# 获取市值数据
market_caps = loader.get_market_caps(
    ts_codes=['000001.SZ', '600000.SH', '000002.SZ']
)

print(returns_df.head())
print(market_caps)
```

---

## 📊 在BL模型中使用

```python
from utils.tushare_loader import TushareLoader
from utils.bl_portfolio import BlackLittermanEngine

# 1. 获取数据
loader = TushareLoader()
returns_df = loader.get_returns(['000001.SZ', '600000.SH'], '2020-01-01')
market_caps = loader.get_market_caps(['000001.SZ', '600000.SH'])

# 2. 创建BL引擎
bl = BlackLittermanEngine(returns_df, market_caps)

# 3. 添加观点
bl.add_absolute_view('000001.SZ', 0.10, confidence=0.7)

# 4. 计算权重
weights = bl.compute_weights()
```

---

## 🎯 在Streamlit中使用

新增了Tushare数据源页面：

```python
# app.py中添加新页面
elif page == "0. Tushare数据源":
    st.header("📡 Tushare数据源")

    # Token输入
    token = st.text_input("Tushare Token", type="password")

    # 股票代码输入
    codes = st.text_area("股票代码（每行一个）", "000001.SZ\n600000.SH")
    start_date = st.date_input("开始日期")

    # 获取数据
    if st.button("获取数据"):
        loader = TushareLoader(token=token if token else None)
        ts_codes = [c.strip() for c in codes.split('\n')]

        with st.spinner("获取中..."):
            returns_df = loader.get_returns(ts_codes, start_date.strftime('%Y-%m-%d'))
            market_caps = loader.get_market_caps(ts_codes)

        st.success("✅ 获取成功")
        st.dataframe(returns_df.head())
```

---

## ⚙️ 配置选项

```python
loader = TushareLoader(
    token='your_token',           # 可选，默认从环境变量读取
    cache_dir='./data/cache',     # 缓存目录
    cache_expire=86400            # 缓存过期时间（秒），默认24小时
)
```

---

## 🔧 常用功能

### 1. 获取股票列表
```python
loader = TushareLoader()
stock_list = loader.get_stock_list(list_status='L')  # 只获取上市股票
print(stock_list)
```

### 2. 清空缓存
```python
loader.clear_cache()
```

### 3. 检查数据质量
```python
returns_df = loader.get_returns(...)
print(f"缺失值: {returns_df.isnull().sum().sum()}")
print(f"数据天数: {len(returns_df)}")
```

---

## 🚨 注意事项

### 1. Token安全
- ⚠️ **不要将token硬编码在代码中**
- ⚠️ **config/tushare.yaml已加入.gitignore**
- ✅ 使用环境变量

### 2. API限制
- Tushare有积分限制
- 建议使用缓存减少调用
- 批量获取时加延时（已自动处理）

### 3. 数据质量
- 检查数据缺失
- 处理异常值
- 验证日期范围

---

## 📝 示例代码

完整示例见：`examples/tushare_example.py`

运行：
```bash
cd quant-rebalancing-app-v0.3
python examples/tushare_example.py
```

---

## 🔗 相关文档

- [Tushare官方文档](https://tushare.pro/document/2)
- [API接口文档](https://tushare.pro/document/2)
- [项目集成方案](./TUSHARE_INTEGRATION_PLAN.md)

---

## ✅ 已完成的集成

- [x] TushareLoader核心类
- [x] 获取收益率数据
- [x] 获取市值数据
- [x] 获取股票列表
- [x] 本地缓存机制
- [x] 使用示例代码
- [x] .gitignore配置
- [ ] Streamlit界面集成（待BL模型完成后）
- [ ] 单元测试（待补充）

---

**最后更新**: 2026-04-27
**维护者**: AI助手
