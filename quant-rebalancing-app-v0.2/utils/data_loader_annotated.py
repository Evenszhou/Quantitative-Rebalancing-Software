"""
数据加载和预处理模块

【模块概述】
这是整个配权系统的"地基"模块，负责把外部数据（Excel/CSV）读进来，
转换成系统内部统一的数据格式，为后续的配权计算和回测提供干净的数据。

【依赖关系】
- Layer 1 (基础层): 只依赖外部库 pandas、numpy
- 没有依赖其他自定义模块

【新手教学】
想象你在Excel里打开一个文件，看到很多列：日期、开盘价、收盘价、成交量等。
DataLoader就像一个智能助手，帮你：
1. 自动打开文件（不管是Excel还是CSV）
2. 自动识别哪一列是日期、哪一列是价格
3. 自动清理缺失数据
4. 把数据整理成整齐的表格，方便后续分析
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Optional


class DataLoader:
    """
    【类说明】
    Layer 1 类 - 数据加载器
    
    【依赖】
    - pandas: 用于数据处理
    - numpy: 用于数值计算
    
    【职责】
    1. 读取Excel/CSV文件
    2. 标准化列名（中英文都能识别）
    3. 处理日期列
    4. 准备收益率数据
    5. 验证数据质量
    
    【新手教学】
    DataLoader就像一个翻译官：
    - 你给它一个Excel文件，里面有"收盘价"、"日期"等中文列名
    - 它自动翻译成系统内部的"close"、"date"等标准英文名
    - 这样后面的模块就不用管原始数据长什么样，统一处理就行了
    """
    
    def __init__(self):
        """
        【方法说明】
        Layer 1 方法 - 初始化数据加载器
        
        【依赖】
        无，纯初始化
        
        【功能】
        设置一些配置信息，告诉系统：
        - 哪些列名代表日期（"日期"、"date"、"Date"等）
        - 哪些列名代表价格（"收盘价"、"close"、"Close"等）
        
        【新手教学】
        就像你刚开始学Excel，老师告诉你：
        - "日期"、"时间"都是时间列
        - "收盘价"、"close"都是价格列
        这里就是把这类知识提前设置好，方便后面自动识别
        """
        # Layer 1 属性 - 日期列候选名单
        # 用途：系统会尝试在这些列名中找日期
        self.date_columns = ['日期', 'date', 'Date', '时间', 'time', 'Time']
        
        # Layer 1 属性 - 价格列候选名单（字典格式）
        # 用途：告诉系统"收盘价"、"close"都对应标准名'close'
        self.price_columns = {
            'close': ['收盘价', 'close', 'Close', '收盘', 'close_price'],
            'open': ['开盘价', 'open', 'Open', '开盘', 'open_price'],
            'high': ['最高价', 'high', 'High', '最高', 'high_price'],
            'low': ['最低价', 'low', 'Low', '最低', 'low_price'],
            'volume': ['成交量', 'volume', 'Volume', 'vol', 'Vol']
        }
    
    def load_file(self, file_obj) -> pd.DataFrame:
        """
        【方法说明】
        Layer 1 方法 - 加载文件
        
        【依赖】
        - pandas.read_excel(): 读取Excel
        - pandas.read_csv(): 读取CSV
        - self._standardize_columns(): 标准化列名（Layer 1内部方法）
        - self._process_date(): 处理日期（Layer 1内部方法）
        
        【输入】
        file_obj: 上传的文件对象（Streamlit的UploadedFile对象）
        
        【输出】
        pd.DataFrame: 标准化后的数据框
        
        【流程】
        1. 判断文件类型（Excel还是CSV）
        2. 用对应的pandas函数读取
        3. 标准化列名（把"收盘价"改成"close"）
        4. 处理日期列（把"日期"列设为索引）
        
        【新手教学】
        就像你在Excel里：
        1. 文件→打开，选择文件
        2. Excel自动识别是.xlsx还是.csv
        3. 你手动把列名改成英文（系统自动做）
        4. 你把日期列设为索引（系统自动做）
        
        【示例】
        >>> loader = DataLoader()
        >>> df = loader.load_file(uploaded_file)
        >>> print(df.columns)  # ['close', 'open', 'high', 'low', 'volume']
        """
        # 判断文件类型
        file_name = file_obj.name.lower()
        
        if file_name.endswith('.xlsx') or file_name.endswith('.xls'):
            # 读取Excel第一个sheet
            df = pd.read_excel(file_obj, sheet_name=0)
        elif file_name.endswith('.csv'):
            # 读取CSV
            df = pd.read_csv(file_obj)
        else:
            raise ValueError(f"不支持的文件格式: {file_name}")
        
        # 标准化列名
        df = self._standardize_columns(df)
        
        # 处理日期列
        df = self._process_date(df)
        
        return df
    
    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        【方法说明】
        Layer 1 内部方法 - 标准化列名
        
        【依赖】
        - self.price_columns: 价格列候选名单（Layer 1属性）
        - pandas.DataFrame.rename(): 重命名列
        
        【功能】
        把各种中文/英文列名统一改成标准英文名：
        - "收盘价"、"close"、"Close" → "close"
        - "开盘价"、"open"、"Open" → "open"
        - "最高价"、"high" → "high"
        - "最低价"、"low" → "low"
        - "成交量"、"volume" → "volume"
        
        【新手教学】
        想象你在整理一份混合中英文的Excel表格：
        - 有人写了"收盘价"，有人写了"Close"，有人写了"close"
        - 这个方法就是自动把它们都改成"close"
        - 这样后面的代码就不用管原始列名是什么，统一用"close"就行了
        
        【为什么要标准化？】
        1. 统一接口：后续模块不需要知道原始列名是什么
        2. 容错性强：用户上传"收盘价"或"Close"都能识别
        3. 代码简洁：后续代码统一写 df['close']，而不是 if '收盘价' in df.columns...
        """
        column_mapping = {}
        
        # 遍历所有价格列类型（close/open/high/low/volume）
        for standard_name, variants in self.price_columns.items():
            # 在数据框的列中查找匹配的列名
            for col in df.columns:
                # 如果列名完全匹配，或者包含关键词
                if col in variants or any(v in col for v in variants):
                    column_mapping[col] = standard_name
                    break
        
        # 重命名列
        df = df.rename(columns=column_mapping)
        
        return df
    
    def _process_date(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        【方法说明】
        Layer 1 内部方法 - 处理日期列
        
        【依赖】
        - self.date_columns: 日期列候选名单（Layer 1属性）
        - pandas.to_datetime(): 转换日期格式
        - pandas.DataFrame.set_index(): 设置索引
        
        【功能】
        1. 找到日期列（可能在"日期"、"date"、"时间"等列）
        2. 转换成pandas的datetime格式
        3. 设为数据框的索引
        4. 按日期排序
        
        【新手教学】
        想象你在处理时间序列数据（比如股票价格）：
        - 原始数据：日期是一列普通列，和"收盘价"、"成交量"混在一起
        - 处理后：日期变成索引（行标签），每行代表某一天的数据
        - 好处：
          1. 方便按日期筛选：df['2024-01-01':'2024-12-31']
          2. 方便按日期排序：df.sort_index()
          3. 方便画图：matplotlib会自动识别日期
        
        【为什么要把日期设为索引？】
        pandas处理时间序列数据的最佳实践：
        1. 时间序列分析需要日期作为索引
        2. 可以快速切片：df['2024'] 取2024年数据
        3. 可以重采样：df.resample('M').mean() 按月聚合
        4. 可以对齐多个资产：按日期索引自动对齐
        """
        # 查找日期列
        date_col = None
        for col in df.columns:
            if col in self.date_columns or any(d in col for d in self.date_columns):
                date_col = col
                break
        
        if date_col:
            # 转换为datetime
            df[date_col] = pd.to_datetime(df[date_col])
            # 设为索引
            df = df.set_index(date_col)
            # 按日期排序（升序）
            df = df.sort_index()
        
        return df
    
    def prepare_returns(
        self, 
        assets_data: Dict[str, pd.DataFrame],
        return_type: str = 'log'
    ) -> pd.DataFrame:
        """
        【方法说明】
        Layer 1 方法 - 准备多资产收益率数据
        
        【依赖】
        - numpy.log(): 计算对数收益率
        - pandas.DataFrame.pct_change(): 计算简单收益率
        - self.price_columns: 价格列候选名单（Layer 1属性）
        
        【输入】
        assets_data: 字典，键是资产名，值是该资产的价格数据框
            示例：{
                '创业板ETF': DataFrame(日期, 收盘价, ...),
                '沪深300ETF': DataFrame(日期, 收盘价, ...),
            }
        return_type: 'log' 对数收益率（默认）, 'simple' 简单收益率
        
        【输出】
        pd.DataFrame: 收益率数据框
            - 行：日期索引
            - 列：各资产的收益率
            - 示例：
                    创业板ETF  沪深300ETF
                2024-01-02   0.015    0.012
                2024-01-03  -0.008   -0.005
        
        【功能】
        1. 从每个资产的价格数据中提取收盘价
        2. 计算收益率（对数或简单）
        3. 合并所有资产的收益率为一个数据框
        4. 删除缺失值（对齐日期）
        
        【新手教学】
        假设你有两个ETF的价格数据：
        - 创业板ETF: [100, 101, 99, 102] (4天价格)
        - 沪深300ETF: [200, 202, 201, 205] (4天价格)
        
        计算收益率：
        - 简单收益率：(今天价格 - 昨天价格) / 昨天价格
          示例：第二天收益率 = (101-100)/100 = 0.01 (1%)
        
        - 对数收益率：ln(今天价格 / 昨天价格)
          示例：ln(101/100) ≈ 0.00995 (约1%)
        
        为什么要用收益率而不是价格？
        1. 可比性：创业板ETF价格100，沪深300ETF价格200，无法直接比较
        2. 标准化：收益率是百分比，不同资产可以比较
        3. 配权需要：配权算法基于收益率计算，不是价格
        
        【对数 vs 简单收益率】
        - 简单收益率：(P1-P0)/P0，直观但数学性质差
        - 对数收益率：ln(P1/P0)，数学性质好（可加性）
        - 在配权计算中，对数收益率更常用
        
        【示例】
        >>> loader = DataLoader()
        >>> assets = {
        ...     'Asset1': df1,
        ...     'Asset2': df2
        ... }
        >>> returns = loader.prepare_returns(assets, return_type='log')
        >>> print(returns.head())
        """
        returns_dict = {}
        
        for asset_name, df in assets_data.items():
            # 尝试找到收盘价列
            price_col = None
            
            # 先尝试标准列名
            if 'close' in df.columns:
                price_col = 'close'
            else:
                # 尝试中文列名
                for col in df.columns:
                    if col in self.price_columns['close'] or any(v in col for v in self.price_columns['close']):
                        price_col = col
                        break
            
            if price_col is None:
                raise ValueError(f"资产 {asset_name} 缺少收盘价列")
            
            prices = df[price_col]
            
            # 计算收益率
            if return_type == 'log':
                # 对数收益率：ln(P_t / P_{t-1})
                returns = np.log(prices / prices.shift(1))
            else:
                # 简单收益率：(P_t - P_{t-1}) / P_{t-1}
                returns = prices.pct_change()
            
            returns_dict[asset_name] = returns
        
        # 合并为DataFrame
        returns_df = pd.DataFrame(returns_dict)
        
        # 删除缺失值（第一天的收益率是NaN，需要删除）
        returns_df = returns_df.dropna()
        
        return returns_df
    
    def validate_data(self, df: pd.DataFrame) -> Dict[str, any]:
        """
        【方法说明】
        Layer 1 方法 - 验证数据质量
        
        【依赖】
        - pandas.DataFrame.isnull(): 检查缺失值
        - pandas.DataFrame.index: 获取日期索引
        
        【输入】
        df: 待验证的数据框
        
        【输出】
        dict: 验证结果
            {
                'valid': bool,  # 是否有效
                'issues': list, # 问题列表
                'stats': dict   # 统计信息
            }
        
        【功能】
        1. 检查必需列是否存在（如'close'）
        2. 检查数据量是否充足（建议≥30行）
        3. 检查缺失值比例（应<10%）
        4. 统计基本信息（行数、列数、时间范围）
        
        【新手教学】
        就像考试前的检查：
        1. 必需的文具带了吗？（必需列）
        2. 答题卡填满了吗？（数据量）
        3. 有没有漏题？（缺失值）
        4. 考试时间多长？（时间范围）
        
        【为什么要验证数据？】
        1. 提前发现问题：数据质量差会导致配权结果错误
        2. 友好提示：告诉用户数据哪里有问题
        3. 防止崩溃：避免后续计算时出现意外错误
        
        【示例】
        >>> loader = DataLoader()
        >>> df = loader.load_file(file)
        >>> result = loader.validate_data(df)
        >>> if not result['valid']:
        ...     print("数据有问题:", result['issues'])
        """
        result = {
            'valid': True,
            'issues': [],
            'stats': {}
        }
        
        # 检查必需列
        required_cols = ['close']
        for col in required_cols:
            if col not in df.columns:
                result['valid'] = False
                result['issues'].append(f"缺少必需列: {col}")
        
        # 检查数据量（统计学建议样本量≥30）
        if len(df) < 30:
            result['issues'].append("数据量不足30行，可能影响分析")
        
        # 检查缺失值
        missing_ratio = df.isnull().sum().sum() / (len(df) * len(df.columns))
        if missing_ratio > 0.1:
            result['issues'].append(f"缺失值比例过高: {missing_ratio:.1%}")
        
        # 统计信息
        result['stats'] = {
            'rows': len(df),
            'columns': len(df.columns),
            'missing_ratio': missing_ratio,
            'date_range': f"{df.index.min()} 到 {df.index.max()}" if hasattr(df.index, 'min') else 'N/A'
        }
        
        return result
