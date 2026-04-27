"""
Data loader service - handles file loading and preprocessing
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
from pathlib import Path
import io


class DataLoaderService:
    """Service for loading and preprocessing financial data"""
    
    def __init__(self):
        self.date_columns = ['日期', 'date', 'Date', '时间', 'time', 'Time']
        self.price_columns = {
            'close': ['收盘价', 'close', 'Close', '收盘', 'close_price'],
            'open': ['开盘价', 'open', 'Open', '开盘', 'open_price'],
            'high': ['最高价', 'high', 'High', '最高', 'high_price'],
            'low': ['最低价', 'low', 'Low', '最低', 'low_price'],
            'volume': ['成交量', 'volume', 'Volume', 'vol', 'Vol']
        }
    
    def load_file(self, file_bytes: bytes, filename: str) -> Tuple[pd.DataFrame, str]:
        """
        Load Excel or CSV file from bytes
        
        Args:
            file_bytes: Raw file bytes
            filename: Original filename
            
        Returns:
            Tuple of (DataFrame, asset_name)
        """
        filename_lower = filename.lower()
        asset_name = Path(filename).stem
        
        if filename_lower.endswith('.xlsx') or filename_lower.endswith('.xls'):
            df = pd.read_excel(io.BytesIO(file_bytes), sheet_name=0)
        elif filename_lower.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(file_bytes))
        else:
            raise ValueError(f"Unsupported file format: {filename}")
        
        df = self._standardize_columns(df)
        df = self._process_date(df)
        
        return df, asset_name
    
    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize column names to English standard"""
        column_mapping = {}
        
        for standard_name, variants in self.price_columns.items():
            for col in df.columns:
                if col in variants or any(v in col for v in variants):
                    column_mapping[col] = standard_name
                    break
        
        return df.rename(columns=column_mapping)
    
    def _process_date(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process date column and set as index"""
        date_col = None
        for col in df.columns:
            if col in self.date_columns or any(d in col for d in self.date_columns):
                date_col = col
                break
        
        if date_col:
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
        Prepare multi-asset returns DataFrame
        
        Args:
            assets_data: Dict mapping asset name to DataFrame
            return_type: 'log' or 'simple'
            
        Returns:
            DataFrame with asset returns
        """
        returns_dict = {}
        
        for asset_name, df in assets_data.items():
            price_col = None
            
            if 'close' in df.columns:
                price_col = 'close'
            else:
                for col in df.columns:
                    if col in self.price_columns['close'] or any(v in col for v in self.price_columns['close']):
                        price_col = col
                        break
            
            if price_col is None:
                raise ValueError(f"Asset {asset_name} missing close price column")
            
            prices = df[price_col]
            
            if return_type == 'log':
                returns = np.log(prices / prices.shift(1))
            else:
                returns = prices.pct_change()
            
            returns_dict[asset_name] = returns
        
        returns_df = pd.DataFrame(returns_dict)
        returns_df = returns_df.dropna()
        
        # 确保索引为 DatetimeIndex（resample 需要）
        if not isinstance(returns_df.index, pd.DatetimeIndex):
            try:
                returns_df.index = pd.to_datetime(returns_df.index)
            except Exception:
                pass
        
        return returns_df
    
    def validate_data(self, df: pd.DataFrame) -> Dict[str, any]:
        """
        Validate data quality
        
        Returns:
            Validation result dict
        """
        result = {
            'valid': True,
            'issues': [],
            'stats': {}
        }
        
        required_cols = ['close']
        for col in required_cols:
            if col not in df.columns:
                result['valid'] = False
                result['issues'].append(f"Missing required column: {col}")
        
        if len(df) < 30:
            result['issues'].append("Insufficient data (<30 rows)")
        
        missing_ratio = df.isnull().sum().sum() / (len(df) * len(df.columns))
        if missing_ratio > 0.1:
            result['issues'].append(f"High missing ratio: {missing_ratio:.1%}")
        
        result['stats'] = {
            'rows': len(df),
            'columns': len(df.columns),
            'missing_ratio': missing_ratio,
            'date_range': f"{df.index.min()} to {df.index.max()}" if hasattr(df.index, 'min') else 'N/A'
        }
        
        return result
    
    def get_asset_info(self, df: pd.DataFrame, asset_name: str, file_id: str) -> Dict:
        """Get asset information dict"""
        has_close = 'close' in df.columns
        date_range = None
        if hasattr(df.index, 'min') and len(df) > 0:
            date_range = f"{df.index.min().strftime('%Y-%m-%d')} to {df.index.max().strftime('%Y-%m-%d')}"
        
        return {
            'asset_name': asset_name,
            'file_id': file_id,
            'rows': len(df),
            'columns': df.columns.tolist(),
            'has_close': has_close,
            'date_range': date_range
        }
