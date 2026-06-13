"""
资金流向数据获取模块
优先使用akshare，东方财富被封时自动回退到问财(pywencai)
"""

import pandas as pd
import warnings
from datetime import datetime, timedelta
import akshare as ak
from core.data_source_manager import data_source_manager

warnings.filterwarnings('ignore')


class FundFlowAkshareDataFetcher:
    """资金流向数据获取类（使用akshare数据源）"""
    
    def __init__(self):
        self.days = 30  # 获取最近30个交易日
        self.available = True
        print("[OK] 资金流向数据获取器初始化成功（akshare数据源）")
    
    def get_fund_flow_data(self, symbol):
        """
        获取个股资金流向数据
        
        Args:
            symbol: 股票代码（6位数字）
            
        Returns:
            dict: 包含资金流向数据的字典
        """
        data = {
            "symbol": symbol,
            "fund_flow_data": None,
            "data_success": False,
            "source": "akshare"
        }
        
        # 只支持中国股票
        if not self._is_chinese_stock(symbol):
            data["error"] = "资金流向数据仅支持中国A股股票"
            return data
        
        try:
            print(f"[资金流向] 正在获取 {symbol} 的资金流向数据...")
            
            # 确定市场
            market = self._get_market(symbol)
            
            # 获取资金流向数据
            fund_flow_data = self._get_individual_fund_flow(symbol, market)
            
            if fund_flow_data:
                data["fund_flow_data"] = fund_flow_data
                print(f"   [OK] 成功获取 {len(fund_flow_data.get('data', []))} 个交易日的资金流向数据")
                data["data_success"] = True
                print("[完成] 资金流向数据获取完成")
            else:
                print("[警告] 未能获取到资金流向数据")
                
        except Exception as e:
            print(f"[ERROR] 获取资金流向数据失败: {e}")
            data["error"] = str(e)
        
        return data
    
    def _is_chinese_stock(self, symbol):
        """判断是否为中国股票"""
        return symbol.isdigit() and len(symbol) == 6
    
    def _get_market(self, symbol):
        """
        根据股票代码判断市场
        上海证券交易所: sh (60开头, 688开头)
        深圳证券交易所: sz (00开头, 30开头)
        北京证券交易所: bj (8开头, 4开头)
        """
        if symbol.startswith('60') or symbol.startswith('688'):
            return 'sh'
        elif symbol.startswith('00') or symbol.startswith('30'):
            return 'sz'
        elif symbol.startswith('8') or symbol.startswith('4'):
            return 'bj'
        else:
            # 默认深圳
            return 'sz'
    
    def _get_individual_fund_flow(self, symbol, market):
        """获取个股资金流向数据（akshare → tushare → 问财 三级fallback）"""
        # 方法1: akshare
        result = self._try_akshare_fund_flow(symbol, market)
        if result:
            return result

        # 方法2: tushare
        result = self._try_tushare_fund_flow(symbol)
        if result:
            return result

        # 方法3: 问财 fallback
        result = self._try_pywencai_fund_flow(symbol)
        if result:
            return result

        return None

    def _try_akshare_fund_flow(self, symbol, market):
        """通过akshare获取资金流向"""
        try:
            print(f"   [Akshare] 正在获取资金流向 (市场: {market})...")
            df = ak.stock_individual_fund_flow(stock=symbol, market=market)
            if df is not None and not df.empty:
                return self._format_fund_flow_df(df, market)
            print(f"   [Akshare] 未找到资金流向数据")
        except Exception as e:
            print(f"   [Akshare] ❌ 获取失败: {e}")
        return None

    def _try_tushare_fund_flow(self, symbol):
        """通过tushare获取资金流向"""
        if not data_source_manager.tushare_available:
            return None
        try:
            print(f"   [Tushare] 正在获取资金流向数据...")
            ts_code = data_source_manager._convert_to_ts_code(symbol)
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=self.days * 2)).strftime('%Y%m%d')

            df = data_source_manager.tushare_api.moneyflow(
                ts_code=ts_code, start_date=start_date, end_date=end_date
            )
            if df is not None and not df.empty:
                df = df.rename(columns={
                    'trade_date': '日期',
                    'buy_sm_amount': '小单买入', 'sell_sm_amount': '小单卖出',
                    'buy_md_amount': '中单买入', 'sell_md_amount': '中单卖出',
                    'buy_lg_amount': '大单买入', 'sell_lg_amount': '大单卖出',
                    'buy_elg_amount': '超大单买入', 'sell_elg_amount': '超大单卖出',
                    'net_mf_amount': '净额'
                })
                df = df.head(self.days)
                print(f"   [Tushare] ✅ 成功获取 {len(df)} 条资金流向数据")
                market = self._get_market(symbol)
                return self._format_fund_flow_df(df, market)
        except Exception as e:
            print(f"   [Tushare] ❌ 获取失败: {e}")
        return None

    def _try_pywencai_fund_flow(self, symbol):
        """通过问财获取资金流向（fallback）"""
        try:
            import pywencai
            print(f"   [问财] 正在获取资金流向数据...")
            result = pywencai.get(question=f'{symbol}近30日资金流向', loop=True)

            if result is None:
                print(f"   [问财] ❌ 返回空数据")
                return None

            data_list = []

            if isinstance(result, dict):
                # 解析问财返回的字典结构
                # 优先取"资金流入数据一览"
                flow_data = result.get('资金流入数据一览', [])
                if flow_data and isinstance(flow_data, list):
                    for item in flow_data[:self.days]:
                        day_data = {
                            '日期': item.get('交易日期', ''),
                        }
                        # 计算主力净流入 = (主动买入大单+被动买入大单+主动买入特大单+被动买入特大单) 相关
                        # 问财返回的是买入金额，需要构造可用的摘要
                        big_buy = (item.get('主动买入大单金额', 0) or 0) + (item.get('被动买入大单金额', 0) or 0)
                        big_sell = item.get('主动卖出大单金额', 0) or 0  # 如果有
                        super_buy = (item.get('主动买入特大单金额', 0) or 0) + (item.get('被动买入特大单金额', 0) or 0)

                        day_data['大单买入'] = big_buy
                        day_data['超大单买入'] = super_buy
                        day_data['中单买入'] = (item.get('主动买入中单金额', 0) or 0) + (item.get('被动买入中单金额', 0) or 0)
                        day_data['小单买入'] = item.get('小单买入金额', 0) or 0
                        data_list.append(day_data)

                # 如果没有详细数据，取基本概况
                if not data_list:
                    overview = result.get('基本概况', [])
                    if overview and isinstance(overview, list):
                        item = overview[0]
                        net_flow = item.get(next((k for k in item if '资金流向' in k), ''), 0)
                        inflow = item.get(next((k for k in item if '资金流入' in k), ''), 0)
                        outflow = item.get(next((k for k in item if '资金流出' in k), ''), 0)
                        data_list.append({
                            '日期': datetime.now().strftime('%Y%m%d'),
                            '主力净流入-净额': net_flow,
                            '区间流入': inflow,
                            '区间流出': outflow,
                        })

            if not data_list:
                print(f"   [问财] ❌ 无法解析资金流向数据")
                return None

            print(f"   [问财] ✅ 成功获取 {len(data_list)} 条资金流向数据")
            market = self._get_market(symbol)
            return {
                "data": data_list,
                "days": len(data_list),
                "columns": list(data_list[0].keys()) if data_list else [],
                "market": market,
                "source": "问财",
                "query_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        except Exception as e:
            print(f"   [问财] ❌ 获取失败: {e}")
        return None

    def _format_fund_flow_df(self, df, market):
        """将DataFrame格式化为标准返回结构"""
        # 取最近N天并倒序
        df = df.tail(self.days)
        df = df.iloc[::-1].reset_index(drop=True)

        data_list = []
        for _, row in df.iterrows():
            item = {}
            for col in df.columns:
                value = row.get(col)
                if value is None or (isinstance(value, float) and pd.isna(value)):
                    continue
                if isinstance(value, (int, float)):
                    item[col] = value
                else:
                    item[col] = str(value)
            if item:
                data_list.append(item)

        return {
            "data": data_list,
            "days": len(data_list),
            "columns": df.columns.tolist(),
            "market": market,
            "query_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def format_fund_flow_for_ai(self, data):
        """
        将资金流向数据格式化为适合AI阅读的文本
        """
        if not data or not data.get("data_success"):
            return "未能获取资金流向数据"
        
        text_parts = []
        
        fund_flow_data = data.get("fund_flow_data")
        if fund_flow_data:
            text_parts.append(f"""
【个股资金流向数据 - akshare数据源】
股票代码：{data.get('symbol', 'N/A')}
市场：{fund_flow_data.get('market', 'N/A').upper()}
交易日数：最近{fund_flow_data.get('days', 0)}个交易日
查询时间：{fund_flow_data.get('query_time', 'N/A')}

═══════════════════════════════════════
[资金流向详细数据]
═══════════════════════════════════════
""")
            
            # 显示每个交易日的数据
            for idx, item in enumerate(fund_flow_data.get('data', []), 1):
                date = item.get('日期', 'N/A')
                close_price = item.get('收盘价', 'N/A')
                change_pct = item.get('涨跌幅', 'N/A')
                
                text_parts.append(f"""
第 {idx} 个交易日 ({date}):
  基本信息:
    - 收盘价: {close_price}
    - 涨跌幅: {change_pct}%
  
  主力资金:
    - 主力净流入-净额: {item.get('主力净流入-净额', 'N/A')}
    - 主力净流入-净占比: {item.get('主力净流入-净占比', 'N/A')}%
  
  超大单:
    - 超大单净流入-净额: {item.get('超大单净流入-净额', 'N/A')}
    - 超大单净流入-净占比: {item.get('超大单净流入-净占比', 'N/A')}%
  
  大单:
    - 大单净流入-净额: {item.get('大单净流入-净额', 'N/A')}
    - 大单净流入-净占比: {item.get('大单净流入-净占比', 'N/A')}%
  
  中单:
    - 中单净流入-净额: {item.get('中单净流入-净额', 'N/A')}
    - 中单净流入-净占比: {item.get('中单净流入-净占比', 'N/A')}%
  
  小单:
    - 小单净流入-净额: {item.get('小单净流入-净额', 'N/A')}
    - 小单净流入-净占比: {item.get('小单净流入-净占比', 'N/A')}%
""")
            
            # 添加统计汇总
            text_parts.append("""
═══════════════════════════════════════
[统计汇总 - 最近30个交易日]
═══════════════════════════════════════
""")
            
            # 计算统计数据
            data_list = fund_flow_data.get('data', [])
            if data_list:
                # 主力净流入统计
                main_inflow_list = [item.get('主力净流入-净额', 0) for item in data_list if isinstance(item.get('主力净流入-净额'), (int, float))]
                if main_inflow_list:
                    total_main_inflow = sum(main_inflow_list)
                    avg_main_inflow = total_main_inflow / len(main_inflow_list)
                    positive_days = len([x for x in main_inflow_list if x > 0])
                    negative_days = len([x for x in main_inflow_list if x < 0])
                    
                    text_parts.append(f"""
主力资金统计:
  - 累计净流入: {total_main_inflow:.2f}
  - 平均每日净流入: {avg_main_inflow:.2f}
  - 净流入天数: {positive_days}天
  - 净流出天数: {negative_days}天
  - 净流入占比: {positive_days/len(main_inflow_list)*100:.1f}%
""")
                
                # 涨跌幅统计
                change_pct_list = [item.get('涨跌幅', 0) for item in data_list if isinstance(item.get('涨跌幅'), (int, float))]
                if change_pct_list:
                    avg_change = sum(change_pct_list) / len(change_pct_list)
                    up_days = len([x for x in change_pct_list if x > 0])
                    down_days = len([x for x in change_pct_list if x < 0])
                    
                    text_parts.append(f"""
股价统计:
  - 平均涨跌幅: {avg_change:.2f}%
  - 上涨天数: {up_days}天
  - 下跌天数: {down_days}天
  - 上涨占比: {up_days/len(change_pct_list)*100:.1f}%
""")
        
        return "\n".join(text_parts)


# 测试函数
if __name__ == "__main__":
    print("测试资金流向数据获取（akshare数据源）...")
    print("="*60)
    
    fetcher = FundFlowAkshareDataFetcher()
    
    if not fetcher.available:
        print("[ERROR] 资金流向数据获取器不可用")
        sys.exit(1)
    
    # 测试股票
    test_symbols = [
        ("000001", "平安银行"),
        ("600519", "贵州茅台"),
        ("000858", "五粮液")
    ]
    
    for symbol, name in test_symbols:
        print(f"\n{'='*60}")
        print(f"正在测试股票: {name} ({symbol})")
        print(f"{'='*60}\n")
        
        data = fetcher.get_fund_flow_data(symbol)
        
        if data.get("data_success"):
            print("\n" + "="*60)
            print("资金流向数据获取成功！")
            print("="*60)
            
            formatted_text = fetcher.format_fund_flow_for_ai(data)
            # 只显示前2000个字符
            preview = formatted_text[:2000] if len(formatted_text) > 2000 else formatted_text
            print(preview)
            if len(formatted_text) > 2000:
                print(f"... (共 {len(formatted_text)} 字符)")
        else:
            print(f"\n获取失败: {data.get('error', '未知错误')}")
        
        print("\n")

