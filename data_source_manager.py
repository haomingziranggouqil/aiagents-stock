"""
数据源管理器
实现akshare(腾讯)和tushare的自动切换机制，支持本地缓存

@File: data_source_manager.py
@Contains: [DataSourceManager]
@Responsibilities:
    - 管理多个股票数据源（腾讯、Tushare）
    - 实现数据源自动切换和降级
    - 本地数据缓存管理
@Non-Responsibilities:
    - 不负责技术指标计算
    - 不负责AI分析
@Input: 股票代码、日期范围
@Output: 标准化的股票历史数据DataFrame
"""

import os
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class DataSourceManager:
    """数据源管理器 - 实现腾讯、tushare自动切换与本地缓存"""

    def __init__(self):
        self.tushare_token = os.getenv('TUSHARE_TOKEN', '')
        self.tushare_available = False
        self.tushare_api = None

        # 本地缓存数据库路径
        self.cache_db_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'stock_data_cache.db'
        )

        # 初始化tushare
        if self.tushare_token:
            try:
                import tushare as ts
                ts.set_token(self.tushare_token)
                self.tushare_api = ts.pro_api()
                self.tushare_available = True
                print("✅ Tushare数据源初始化成功")
            except Exception as e:
                print(f"⚠️ Tushare数据源初始化失败: {e}")
                self.tushare_available = False
        else:
            print("ℹ️ 未配置Tushare Token，将使用腾讯数据源和本地缓存")

        # 初始化本地缓存数据库
        self._init_cache_db()

    def _init_cache_db(self):
        """初始化本地缓存数据库"""
        try:
            conn = sqlite3.connect(self.cache_db_path)
            cursor = conn.cursor()

            # 历史数据缓存表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stock_hist_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    data_date TEXT NOT NULL,
                    open REAL,
                    close REAL,
                    high REAL,
                    low REAL,
                    volume REAL,
                    amount REAL,
                    source TEXT,
                    cached_at TEXT,
                    UNIQUE(symbol, data_date)
                )
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_hist_symbol ON stock_hist_cache(symbol)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_hist_date ON stock_hist_cache(data_date)')

            # 基本信息缓存表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stock_info_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL UNIQUE,
                    name TEXT,
                    industry TEXT,
                    market TEXT,
                    list_date TEXT,
                    cached_at TEXT
                )
            ''')

            conn.commit()
            conn.close()
            print("✅ 本地缓存数据库初始化成功")
        except Exception as e:
            print(f"⚠️ 缓存数据库初始化失败: {e}")

    def _convert_to_tx_code(self, symbol):
        """
        将6位股票代码转换为腾讯格式（带市场前缀）
        如：000001 -> sz000001, 600036 -> sh600036
        """
        if not symbol or len(symbol) != 6:
            return symbol
        if symbol.startswith('6'):
            return f"sh{symbol}"  # 上海主板/科创板
        elif symbol.startswith(('0', '3')):
            return f"sz{symbol}"  # 深圳主板/创业板
        elif symbol.startswith(('8', '4')):
            return f"bj{symbol}"  # 北交所
        return f"sz{symbol}"

    def _convert_to_ts_code(self, symbol):
        """
        将6位股票代码转换为tushare格式（带市场后缀）

        Args:
            symbol: 6位股票代码

        Returns:
            str: tushare格式代码（如：000001.SZ）
        """
        if not symbol or len(symbol) != 6:
            return symbol

        # 根据代码判断市场
        if symbol.startswith('6'):
            # 上海主板
            return f"{symbol}.SH"
        elif symbol.startswith('0') or symbol.startswith('3'):
            # 深圳主板和创业板
            return f"{symbol}.SZ"
        elif symbol.startswith('8') or symbol.startswith('4'):
            # 北交所
            return f"{symbol}.BJ"
        else:
            # 默认深圳
            return f"{symbol}.SZ"

    def _convert_from_ts_code(self, ts_code):
        """
        将tushare格式代码转换为6位代码

        Args:
            ts_code: tushare格式代码（如：000001.SZ）

        Returns:
            str: 6位股票代码
        """
        if '.' in ts_code:
            return ts_code.split('.')[0]
        return ts_code

    def _save_hist_cache(self, symbol, df, source):
        """
        保存历史数据到本地缓存

        Args:
            symbol: 股票代码
            df: 历史数据DataFrame
            source: 数据来源标识
        """
        try:
            conn = sqlite3.connect(self.cache_db_path)
            cursor = conn.cursor()
            cached_at = datetime.now().isoformat()

            for _, row in df.iterrows():
                date_str = row['date'].strftime('%Y-%m-%d') if isinstance(row['date'], pd.Timestamp) else str(row['date'])
                cursor.execute('''
                    INSERT OR REPLACE INTO stock_hist_cache
                    (symbol, data_date, open, close, high, low, volume, amount, source, cached_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    symbol, date_str,
                    row.get('open'), row.get('close'), row.get('high'), row.get('low'),
                    row.get('volume'), row.get('amount'), source, cached_at
                ))

            conn.commit()
            conn.close()
            print(f"[缓存] ✅ 已保存 {len(df)} 条数据到本地缓存")
        except Exception as e:
            print(f"[缓存] ❌ 保存失败: {e}")

    def _load_hist_cache(self, symbol, start_date=None, end_date=None):
        """
        从本地缓存加载历史数据

        Args:
            symbol: 股票代码
            start_date: 开始日期（格式：'20240101'）
            end_date: 结束日期

        Returns:
            DataFrame: 历史数据，如果无缓存返回None
        """
        try:
            conn = sqlite3.connect(self.cache_db_path)

            query = "SELECT * FROM stock_hist_cache WHERE symbol = ?"
            params = [symbol]

            if start_date:
                query += " AND data_date >= ?"
                params.append(f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}")
            if end_date:
                query += " AND data_date <= ?"
                params.append(f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}")

            query += " ORDER BY data_date"

            df = pd.read_sql_query(query, conn, params=params)
            conn.close()

            if df.empty:
                return None

            # 转换数据格式
            df['date'] = pd.to_datetime(df['data_date'])
            df = df[['date', 'open', 'close', 'high', 'low', 'volume', 'amount']]

            return df
        except Exception as e:
            print(f"[缓存] ❌ 读取失败: {e}")
            return None

    def get_stock_hist_data(self, symbol, start_date=None, end_date=None, adjust='qfq'):
        """
        获取股票历史数据（优先腾讯，失败时使用tushare，最后使用本地缓存）

        Args:
            symbol: 股票代码（6位数字）
            start_date: 开始日期（格式：'20240101'或'2024-01-01'）
            end_date: 结束日期
            adjust: 复权类型（'qfq'前复权, 'hfq'后复权, ''不复权）

        Returns:
            DataFrame: 包含日期、开盘、收盘、最高、最低、成交量等列
        """
        # 标准化日期格式
        if start_date:
            start_date = start_date.replace('-', '')
        if end_date:
            end_date = end_date.replace('-', '')
        else:
            end_date = datetime.now().strftime('%Y%m%d')

        # 1. 优先使用腾讯数据源
        try:
            import akshare as ak
            tx_code = self._convert_to_tx_code(symbol)
            print(f"[腾讯] 正在获取 {symbol} 的历史数据...")

            df = ak.stock_zh_a_hist_tx(
                symbol=tx_code,
                start_date=start_date,
                end_date=end_date,
                adjust=adjust
            )

            if df is not None and not df.empty:
                # 标准化列名（腾讯接口返回的amount是成交量，单位：手）
                df = df.rename(columns={'amount': 'volume'})
                df['date'] = pd.to_datetime(df['date'])
                # 成交量单位转换：手 -> 股
                df['volume'] = df['volume'] * 100
                # 添加成交额列（腾讯接口不提供，设为NaN）
                df['amount'] = None
                print(f"[腾讯] ✅ 成功获取 {len(df)} 条数据")
                return df
        except Exception as e:
            print(f"[腾讯] ❌ 获取失败: {e}")

        # 2. 腾讯失败，尝试tushare
        if self.tushare_available:
            try:
                print(f"[Tushare] 正在获取 {symbol} 的历史数据（备用数据源）...")

                # 转换股票代码格式（添加市场后缀）
                ts_code = self._convert_to_ts_code(symbol)

                # 转换复权类型
                adj_dict = {'qfq': 'qfq', 'hfq': 'hfq', '': None}
                adj = adj_dict.get(adjust, 'qfq')

                # 格式化日期
                start = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}" if start_date else None
                end = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}" if end_date else None

                # 获取数据
                df = self.tushare_api.daily(
                    ts_code=ts_code,
                    start_date=start,
                    end_date=end,
                    adj=adj
                )

                if df is not None and not df.empty:
                    # 标准化列名和数据格式
                    df = df.rename(columns={
                        'trade_date': 'date',
                        'vol': 'volume',
                        'amount': 'amount'
                    })
                    df['date'] = pd.to_datetime(df['date'])
                    df = df.sort_values('date')

                    # 转换成交量单位（tushare单位是手，转换为股）
                    df['volume'] = df['volume'] * 100
                    # 转换成交额单位（tushare单位是千元，转换为元）
                    df['amount'] = df['amount'] * 1000

                    # 保存到本地缓存
                    self._save_hist_cache(symbol, df, 'tushare')

                    print(f"[Tushare] ✅ 成功获取 {len(df)} 条数据")
                    return df
            except Exception as e:
                print(f"[Tushare] ❌ 获取失败: {e}")

        # 3. 所有数据源失败，尝试本地缓存
        print(f"[缓存] 尝试从本地缓存读取 {symbol} 的历史数据...")
        cached_df = self._load_hist_cache(symbol, start_date, end_date)
        if cached_df is not None and not cached_df.empty:
            print(f"[缓存] ✅ 从缓存获取 {len(cached_df)} 条数据")
            return cached_df

        # 所有数据源都失败且无缓存
        print("❌ 所有数据源均获取失败且无缓存数据")
        return None

    def get_stock_basic_info(self, symbol):
        """
        获取股票基本信息（优先腾讯，失败时使用tushare，最后使用本地缓存）

        Args:
            symbol: 股票代码

        Returns:
            dict: 股票基本信息
        """
        info = {
            "symbol": symbol,
            "name": "未知",
            "industry": "未知",
            "market": "未知"
        }

        # 1. 尝试从缓存获取
        cached_info = self._load_info_cache(symbol)
        if cached_info:
            print(f"[缓存] ✅ 使用缓存的基本信息")
            return cached_info

        # 2. 尝试使用akshare东方财富接口（基本信息腾讯接口不支持）
        try:
            import akshare as ak
            print(f"[Akshare] 正在获取 {symbol} 的基本信息...")

            stock_info = ak.stock_individual_info_em(symbol=symbol)
            if stock_info is not None and not stock_info.empty:
                for _, row in stock_info.iterrows():
                    key = row['item']
                    value = row['value']

                    if key == '股票简称':
                        info['name'] = value
                    elif key == '所处行业':
                        info['industry'] = value
                    elif key == '上市时间':
                        info['list_date'] = value
                    elif key == '总市值':
                        info['market_cap'] = value
                    elif key == '流通市值':
                        info['circulating_market_cap'] = value

                # 保存到缓存
                self._save_info_cache(symbol, info)
                print(f"[Akshare] ✅ 成功获取基本信息")
                return info
        except Exception as e:
            print(f"[Akshare] ❌ 获取失败: {e}")

        # 3. akshare失败，尝试tushare
        if self.tushare_available:
            try:
                print(f"[Tushare] 正在获取 {symbol} 的基本信息（备用数据源）...")

                ts_code = self._convert_to_ts_code(symbol)
                df = self.tushare_api.stock_basic(
                    ts_code=ts_code,
                    fields='ts_code,name,area,industry,market,list_date'
                )

                if df is not None and not df.empty:
                    info['name'] = df.iloc[0]['name']
                    info['industry'] = df.iloc[0]['industry']
                    info['market'] = df.iloc[0]['market']
                    info['list_date'] = df.iloc[0]['list_date']

                    # 保存到缓存
                    self._save_info_cache(symbol, info)
                    print(f"[Tushare] ✅ 成功获取基本信息")
                    return info
            except Exception as e:
                print(f"[Tushare] ❌ 获取失败: {e}")

        return info

    def _save_info_cache(self, symbol, info):
        """保存基本信息到缓存"""
        try:
            conn = sqlite3.connect(self.cache_db_path)
            cursor = conn.cursor()
            cached_at = datetime.now().isoformat()

            cursor.execute('''
                INSERT OR REPLACE INTO stock_info_cache
                (symbol, name, industry, market, list_date, cached_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                symbol, info.get('name'), info.get('industry'),
                info.get('market'), info.get('list_date'), cached_at
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[缓存] 保存基本信息失败: {e}")

    def _load_info_cache(self, symbol):
        """从缓存加载基本信息"""
        try:
            conn = sqlite3.connect(self.cache_db_path)
            cursor = conn.cursor()

            cursor.execute(
                'SELECT name, industry, market, list_date FROM stock_info_cache WHERE symbol = ?',
                (symbol,)
            )
            row = cursor.fetchone()
            conn.close()

            if row:
                return {
                    'symbol': symbol,
                    'name': row[0] or '未知',
                    'industry': row[1] or '未知',
                    'market': row[2] or '未知',
                    'list_date': row[3]
                }
            return None
        except Exception as e:
            print(f"[缓存] 读取基本信息失败: {e}")
            return None

    def get_realtime_quotes(self, symbol):
        """
        获取实时行情数据（优先akshare，失败时使用tushare）

        Args:
            symbol: 股票代码

        Returns:
            dict: 实时行情数据
        """
        quotes = {}

        # 优先使用akshare
        try:
            import akshare as ak
            print(f"[Akshare] 正在获取 {symbol} 的实时行情...")

            df = ak.stock_zh_a_spot_em()
            stock_df = df[df['代码'] == symbol]

            if not stock_df.empty:
                row = stock_df.iloc[0]
                quotes = {
                    'symbol': symbol,
                    'name': row['名称'],
                    'price': row['最新价'],
                    'change_percent': row['涨跌幅'],
                    'change': row['涨跌额'],
                    'volume': row['成交量'],
                    'amount': row['成交额'],
                    'high': row['最高'],
                    'low': row['最低'],
                    'open': row['今开'],
                    'pre_close': row['昨收']
                }
                print(f"[Akshare] ✅ 成功获取实时行情")
                return quotes
        except Exception as e:
            print(f"[Akshare] ❌ 获取失败: {e}")

        # akshare失败，尝试tushare
        if self.tushare_available:
            try:
                print(f"[Tushare] 正在获取 {symbol} 的实时行情（备用数据源）...")

                ts_code = self._convert_to_ts_code(symbol)
                df = self.tushare_api.daily(
                    ts_code=ts_code,
                    start_date=datetime.now().strftime('%Y%m%d'),
                    end_date=datetime.now().strftime('%Y%m%d')
                )

                if df is not None and not df.empty:
                    row = df.iloc[0]
                    quotes = {
                        'symbol': symbol,
                        'price': row['close'],
                        'change_percent': row['pct_chg'],
                        'volume': row['vol'] * 100,
                        'amount': row['amount'] * 1000,
                        'high': row['high'],
                        'low': row['low'],
                        'open': row['open'],
                        'pre_close': row['pre_close']
                    }
                    print(f"[Tushare] ✅ 成功获取实时行情")
                    return quotes
            except Exception as e:
                print(f"[Tushare] ❌ 获取失败: {e}")

        return quotes

    def get_financial_data(self, symbol, report_type='income'):
        """
        获取财务数据（优先akshare，失败时使用tushare）

        Args:
            symbol: 股票代码
            report_type: 报表类型（'income'利润表, 'balance'资产负债表, 'cashflow'现金流量表）

        Returns:
            DataFrame: 财务数据
        """
        # 优先使用akshare
        try:
            import akshare as ak
            print(f"[Akshare] 正在获取 {symbol} 的财务数据...")

            if report_type == 'income':
                df = ak.stock_financial_report_sina(stock=symbol, symbol="利润表")
            elif report_type == 'balance':
                df = ak.stock_financial_report_sina(stock=symbol, symbol="资产负债表")
            elif report_type == 'cashflow':
                df = ak.stock_financial_report_sina(stock=symbol, symbol="现金流量表")
            else:
                df = None

            if df is not None and not df.empty:
                print(f"[Akshare] ✅ 成功获取财务数据")
                return df
        except Exception as e:
            print(f"[Akshare] ❌ 获取失败: {e}")

        # akshare失败，尝试tushare
        if self.tushare_available:
            try:
                print(f"[Tushare] 正在获取 {symbol} 的财务数据（备用数据源）...")

                ts_code = self._convert_to_ts_code(symbol)

                if report_type == 'income':
                    df = self.tushare_api.income(ts_code=ts_code)
                elif report_type == 'balance':
                    df = self.tushare_api.balancesheet(ts_code=ts_code)
                elif report_type == 'cashflow':
                    df = self.tushare_api.cashflow(ts_code=ts_code)
                else:
                    df = None

                if df is not None and not df.empty:
                    print(f"[Tushare] ✅ 成功获取财务数据")
                    return df
            except Exception as e:
                print(f"[Tushare] ❌ 获取失败: {e}")

        return None


# 全局数据源管理器实例
data_source_manager = DataSourceManager()