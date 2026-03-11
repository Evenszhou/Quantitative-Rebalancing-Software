"""
数据加载和预处理模块
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Optional


class DataLoader:
    """数据加载器"""
    
    def __init__(self):
        self.date_columns = ['日期', 'date', 'Date', '时间', 'time', 'Time']
        self.price_columns = {
            'close': ['收盘价', 'close', 'Close', '收盘', 'close_price'],
            'open': ['开盘价', 'open', 'Open', '开盘', 'open_price'],
            'high': ['最高价', 'high', 'High', '最高', 'high_price'],
            'low': ['最低价', 'low', 'Low', '最低', 'low_price'],
            'volume': ['成交量', 'volume', 'Volume', 'vol', 'Vol']
        }
    
    def load_file(self, file_obj) -> pd.DataFrame:
        """
        加载Excel或CSV文件
        
        Args:
            file_obj: 上传的文件对象
            
        Returns:
            pd.DataFrame: 标准化后的数据框
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
        """标准化列名"""
        column_mapping = {}
        
        for standard_name, variants in self.price_columns.items(): #  遍历预定义的价格标准列名及其所有变体 standard_name: 标准列名 variants: 该标准列名的所有可能变体
            for col in df.columns: #  遍历读取的数据框中的所有列名
                if col in variants or any(v in col for v in variants): 
                    #  检查当前列名是否在变体列表中，或者是否包含任何变体字典里记载的字符串         
                    column_mapping[col] = standard_name #  如果匹配成功，将标准列名映射到当前列名
                    break #  找到匹配后立即跳出内层循环，继续处理下一个标准列名

        #这里只是通过一个loop实现了从不标准列名到标准列名的字典映射        
        
        # 重命名列，这里才是使用字典映射来更改实际列名的地方
        df = df.rename(columns=column_mapping)
        
        return df
    
    def _process_date(self, df: pd.DataFrame) -> pd.DataFrame:
        """处理日期列"""
        # 查找日期列
        date_col = None
        for col in df.columns:
            if col in self.date_columns or any(d in col for d in self.date_columns): #和处理标准列的逻辑如出一辙
                date_col = col
                break
        
        if date_col:
            # 转换为datetime
            df[date_col] = pd.to_datetime(df[date_col])
            df = df.set_index(date_col)
            df = df.sort_index()
        
        return df
    
    def prepare_returns(
        self, 
        assets_data: Dict[str, pd.DataFrame],
        return_type: str = 'log'
    ) -> pd.DataFrame:
        """
        准备多资产收益率数据
        
        Args:
            assets_data: 字典，键为资产名，值为数据框
            return_type: 'log' 对数收益率, 'simple' 简单收益率
            
        Returns:
            pd.DataFrame: 收益率数据框，列为资产名
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
            
            if return_type == 'log':
                returns = np.log(prices / prices.shift(1))
            else:
                returns = prices.pct_change()
            
            returns_dict[asset_name] = returns
        
        # 合并为DataFrame
        returns_df = pd.DataFrame(returns_dict)
        
        # 删除缺失值
        returns_df = returns_df.dropna()
        
        return returns_df
    
    def validate_data(self, df: pd.DataFrame) -> Dict[str, any]:
        """
        验证数据质量
        
        Args:
            df: 数据框
            
        Returns:
            dict: 验证结果
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
        
        # 检查数据量
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
