"""
Tushare Pro数据加载器
为Black-Litterman模型提供数据支持

使用方法：
    from utils.tushare_loader import TushareLoader

    loader = TushareLoader()
    returns_df = loader.get_returns(['000001.SZ', '600000.SH'], '2020-01-01')
    market_caps = loader.get_market_caps(['000001.SZ', '600000.SH'])
"""
import tushare as ts
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional
import warnings
import time
import os


class TushareLoader:
    """Tushare Pro数据加载器"""

    def __init__(
        self,
        token: Optional[str] = None,
        cache_dir: str = './data/cache',
        cache_expire: int = 86400  # 24小时
    ):
        """
        初始化加载器

        Args:
            token: Tushare Pro token（如果不提供，从环境变量读取）
            cache_dir: 缓存目录
            cache_expire: 缓存过期时间（秒）
        """
        # 设置token
        if token is None:
            token = self._get_token_from_env()

        if token is None:
            raise ValueError(
                "Tushare token未设置。请：\n"
                "1. 传入token参数\n"
                "2. 或设置环境变量: export TUSHARE_TOKEN='your_token'\n"
                "3. 或在~/.tushare文件中配置"
            )

        ts.set_token(token)
        self.pro = ts.pro_api()

        # 缓存配置
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_expire = cache_expire

    def _get_token_from_env(self) -> Optional[str]:
        """从环境变量获取token"""
        return os.environ.get('TUSHARE_TOKEN')

    def get_returns(
        self,
        ts_codes: List[str],
        start_date: str,
        end_date: Optional[str] = None,
        freq: str = 'daily'
    ) -> pd.DataFrame:
        """
        获取股票收益率数据

        Args:
            ts_codes: 股票代码列表，如['000001.SZ', '600000.SH']
            start_date: 开始日期，'2020-01-01'
            end_date: 结束日期，默认为今天
            freq: 频率，'daily'或'weekly'

        Returns:
            DataFrame: 收益率数据，索引为日期，列为股票代码
        """
        if end_date is None:
            end_date = pd.Timestamp.today().strftime('%Y%m%d')

        # 检查缓存
        cache_file = self._get_cache_file('returns', ts_codes, start_date, end_date)
        cached_data = self._load_cache(cache_file)
        if cached_data is not None:
            return cached_data

        # 获取数据
        all_data = []
        for code in ts_codes:
            try:
                # 获取日线数据
                df = self.pro.daily(
                    ts_code=code,
                    start_date=start_date.replace('-', ''),
                    end_date=end_date.replace('-', '')
                )

                if df.empty:
                    warnings.warn(f"股票{code}没有数据")
                    continue

                # 计算：使用收盘价的前收盘价计算收益率
                df = df.sort_values('trade_date')
                df['return'] = df['close'].pct_change()

                # 保留需要的列
                df = df[['trade_date', 'return']].copy()
                df['ts_code'] = code

                all_data.append(df)

                # 避免API限流
                time.sleep(0.1)

            except Exception as e:
                warnings.warn(f"获取{code}数据失败: {str(e)}")
                continue

        if not all_data:
            raise ValueError("没有获取到任何数据")

        # 合并数据
        result = pd.concat(all_data, ignore_index=True)
        result = result.pivot(index='trade_date', columns='ts_code', values='return')

        # 删除第一行（NaN）
        result = result.iloc[1:]

        # 转换索引为日期格式
        result.index = pd.to_datetime(result.index)

        # 保存缓存
        self._save_cache(cache_file, result)

        return result

    def get_market_caps(
        self,
        ts_codes: List[str],
        trade_date: Optional[str] = None
    ) -> Dict[str, float]:
        """
        获取市值数据

        Args:
            ts_codes: 股票代码列表
            trade_date: 交易日期，默认为最新

        Returns:
            dict: {股票代码: 市值（元）}
        """
        if trade_date is None:
            trade_date = pd.Timestamp.today().strftime('%Y%m%d')

        # 检查缓存
        cache_file = self._get_cache_file('market_caps', ts_codes, trade_date)
        cached_data = self._load_cache(cache_file)
        if cached_data is not None:
            return cached_data

        # 获取数据
        market_caps = {}
        for code in ts_codes:
            try:
                df = self.pro.daily_basic(
                    ts_code=code,
                    trade_date=trade_date,
                    fields='ts_code,total_mv'  # 总市值（万元）
                )

                if df.empty:
                    # 尝试获取最近的
                    df = self.pro.daily_basic(
                        ts_code=code,
                        fields='ts_code,trade_date,total_mv'
                    )
                    df = df.sort_values('trade_date').tail(1)

                if not df.empty:
                    # 转换为元（万元→元）
                    market_caps[code] = df['total_mv'].values[0] * 10000

                time.sleep(0.1)

            except Exception as e:
                warnings.warn(f"获取{code}市值失败: {str(e)}")
                continue

        if not market_caps:
            raise ValueError("没有获取到任何市值数据")

        # 保存缓存
        self._save_cache(cache_file, market_caps)

        return market_caps

    def get_stock_list(
        self,
        market: Optional[str] = None,
        list_status: str = 'L'
    ) -> pd.DataFrame:
        """
        获取股票列表

        Args:
            market: 市场类型，None表示所有
            list_status: 上市状态 'L'上市 'D'退市 'P'暂停上市

        Returns:
            DataFrame: 股票列表
        """
        # 检查缓存
        cache_file = self.cache_dir / f'stock_list_{market}_{list_status}.pkl'
        cached_data = self._load_cache(cache_file)
        if cached_data is not None:
            return cached_data

        # 获取数据
        df = self.pro.stock_basic(
            exchange='',
            list_status=list_status,
            fields='ts_code,symbol,name,area,industry,market,list_date'
        )

        if market is not None:
            df = df[df['market'] == market]

        # 保存缓存
        self._save_cache(cache_file, df)

        return df

    def _get_cache_file(self, data_type: str, *args) -> Path:
        """生成缓存文件名"""
        # 将参数哈希化作为文件名
        key = f"{data_type}_{'_'.join(str(arg) for arg in args)}"
        import hashlib
        hash_key = hashlib.md5(key.encode()).hexdigest()[:8]
        return self.cache_dir / f"{data_type}_{hash_key}.pkl"

    def _load_cache(self, cache_file: Path):
        """加载缓存"""
        if not cache_file.exists():
            return None

        # 检查是否过期
        if time.time() - cache_file.stat().st_mtime > self.cache_expire:
            return None

        try:
            import pickle
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        except:
            return None

    def _save_cache(self, cache_file: Path, data):
        """保存缓存"""
        try:
            import pickle
            with open(cache_file, 'wb') as f:
                pickle.dump(data, f)
        except:
            warnings.warn(f"保存缓存失败: {cache_file}")

    def clear_cache(self):
        """清空缓存"""
        import shutil
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
