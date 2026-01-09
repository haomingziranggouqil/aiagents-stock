"""
新闻数据获取模块
使用akshare获取股票的最新新闻信息（替代qstock）
"""

import pandas as pd
import sys
import io
import warnings
from datetime import datetime, timedelta
import akshare as ak

warnings.filterwarnings('ignore')

# 设置标准输出编码为UTF-8（仅在命令行环境，避免streamlit冲突）
def _setup_stdout_encoding():
    """仅在命令行环境设置标准输出编码"""
    if sys.platform == 'win32' and not hasattr(sys.stdout, '_original_stream'):
        try:
            # 检测是否在streamlit环境中
            import streamlit
            # 在streamlit中不修改stdout
            return
        except ImportError:
            # 不在streamlit环境，可以安全修改
            try:
                sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='ignore')
            except:
                pass

_setup_stdout_encoding()


class QStockNewsDataFetcher:
    """新闻数据获取类（使用akshare作为数据源）"""
    
    def __init__(self):
        self.max_items = 30  # 最多获取的新闻数量
        self.available = True
        print("✓ 新闻数据获取器初始化成功（akshare数据源）")
    
    def get_stock_news(self, symbol):
        """
        获取股票的新闻数据
        
        Args:
            symbol: 股票代码（6位数字）
            
        Returns:
            dict: 包含新闻数据的字典
        """
        data = {
            "symbol": symbol,
            "news_data": None,
            "data_success": False,
            "source": "qstock"
        }
        
        if not self.available:
            data["error"] = "qstock库未安装或不可用"
            return data
        
        # 只支持中国股票
        if not self._is_chinese_stock(symbol):
            data["error"] = "新闻数据仅支持中国A股股票"
            return data
        
        try:
            # 获取新闻数据
            print(f"📰 正在使用qstock获取 {symbol} 的最新新闻...")
            news_data = self._get_news_data(symbol)
            
            if news_data:
                data["news_data"] = news_data
                print(f"   ✓ 成功获取 {len(news_data.get('items', []))} 条新闻")
                data["data_success"] = True
                print("✅ 新闻数据获取完成")
            else:
                print("⚠️ 未能获取到新闻数据")
                
        except Exception as e:
            print(f"❌ 获取新闻数据失败: {e}")
            data["error"] = str(e)
        
        return data
    
    def _is_chinese_stock(self, symbol):
        """判断是否为中国股票"""
        return symbol.isdigit() and len(symbol) == 6
    
    def _get_news_data(self, symbol):
        """获取新闻数据（使用akshare）"""
        try:
            print(f"   使用 akshare 获取新闻...")
            
            news_items = []
            
            # 方法1: 尝试获取个股新闻（东方财富）
            try:
                # stock_news_em(symbol="600519") - 东方财富个股新闻
                df = ak.stock_news_em(symbol=symbol)
                
                if df is not None and not df.empty:
                    print(f"   ✓ 从东方财富获取到 {len(df)} 条新闻")
                    
                    # 处理DataFrame，提取新闻
                    for idx, row in df.head(self.max_items).iterrows():
                        item = {'source': '东方财富'}
                        
                        # 提取所有列
                        for col in df.columns:
                            value = row.get(col)
                            
                            # 跳过空值
                            if value is None or (isinstance(value, float) and pd.isna(value)):
                                continue
                            
                            # 保存字段
                            try:
                                item[col] = str(value)
                            except:
                                item[col] = "无法解析"
                        
                        if len(item) > 1:  # 如果有数据才添加
                            news_items.append(item)
            
            except Exception as e:
                print(f"   ⚠ 从东方财富获取失败: {e}")
            
            # 方法2: 如果没有获取到，尝试获取新浪财经新闻
            if not news_items:
                try:
                    stock_name = None

                    # 优先使用个股信息接口获取名称 (比拉取全量列表更稳定快)
                    try:
                        if hasattr(ak, 'stock_individual_info_em'):
                            df_info = ak.stock_individual_info_em(symbol=symbol)
                            if df_info is not None and not df_info.empty:
                                # 查找"股票简称"行
                                name_row = df_info[df_info['item'] == '股票简称']
                                if not name_row.empty:
                                    stock_name = name_row.iloc[0]['value']
                                    print(f"   找到股票名称: {stock_name}")
                    except Exception as e:
                        print(f"   个股信息查询失败，尝试全量列表: {e}")

                    # 如果上面的方法失败，尝试旧方法
                    if not stock_name:
                        # stock_zh_a_spot_em() - 获取股票信息，包含代码和名称
                        df_info = ak.stock_zh_a_spot_em()

                        # 查找股票名称
                        if df_info is not None and not df_info.empty:
                            match = df_info[df_info['代码'] == symbol]
                            if not match.empty:
                                stock_name = match.iloc[0]['名称']
                                print(f"   找到股票名称(全量表): {stock_name}")

                    # 使用股票名称搜索新闻
                    if stock_name:
                        # stock_news_sina - 新浪财经新闻
                        try:
                            if hasattr(ak, 'stock_news_sina'):
                                df = ak.stock_news_sina(symbol=stock_name)
                                if df is not None and not df.empty:
                                    print(f"   ✓ 从新浪财经获取到 {len(df)} 条新闻")

                                    for idx, row in df.head(self.max_items).iterrows():
                                        item = {'source': '新浪财经'}

                                        for col in df.columns:
                                            value = row.get(col)
                                            if value is None or (isinstance(value, float) and pd.isna(value)):
                                                continue
                                            try:
                                                item[col] = str(value)
                                            except:
                                                item[col] = "无法解析"

                                        if len(item) > 1:
                                            news_items.append(item)
                            else:
                                print(f"   ⚠️ akshare 缺少 stock_news_sina 方法")
                        except:
                            pass
                
                except Exception as e:
                    print(f"   ⚠ 从新浪财经获取失败: {e}")
            
            # 方法3: 尝试获取财联社电报
            if not news_items or len(news_items) < 5:
                try:
                    # stock_news_cls() - 财联社电报
                    if hasattr(ak, 'stock_news_cls'):
                        df = ak.stock_news_cls()

                        if df is not None and not df.empty:
                            # 筛选包含股票代码或名称的新闻
                            df_filtered = df[
                                df['内容'].str.contains(symbol, na=False) |
                                df['标题'].str.contains(symbol, na=False)
                            ]

                            if not df_filtered.empty:
                                print(f"   ✓ 从财联社获取到 {len(df_filtered)} 条相关新闻")

                                for idx, row in df_filtered.head(self.max_items - len(news_items)).iterrows():
                                    item = {'source': '财联社'}

                                    for col in df_filtered.columns:
                                        value = row.get(col)
                                        if value is None or (isinstance(value, float) and pd.isna(value)):
                                            continue
                                        try:
                                            item[col] = str(value)
                                        except:
                                            item[col] = "无法解析"

                                    if len(item) > 1:
                                        news_items.append(item)
                    else:
                        print(f"   ⚠️ akshare 缺少 stock_news_cls 方法")

                except Exception as e:
                    print(f"   ⚠ 从财联社获取失败: {e}")

            # 方法4: 兜底方案 - 使用 pywencai (问财)
            if not news_items:
                try:
                    print("   ⚠️ akshare 获取新闻失败，尝试切换到问财数据源...")
                    # 延迟导入以避免循环依赖
                    from news_announcement_data import NewsAnnouncementDataFetcher
                    wencai_fetcher = NewsAnnouncementDataFetcher()
                    # 临时修改max_items以匹配
                    original_max = wencai_fetcher.max_items
                    wencai_fetcher.max_items = self.max_items

                    # 获取数据
                    wencai_result = wencai_fetcher.get_news_and_announcements(symbol)

                    if wencai_result and wencai_result.get('news_data'):
                        news_data = wencai_result['news_data']
                        items = news_data.get('items', [])

                        if items:
                            print(f"   ✓ 从问财获取到 {len(items)} 条新闻")
                            for item in items:
                                if 'source' not in item:
                                    item['source'] = '问财'
                                news_items.append(item)
                except ImportError:
                    print("   ⚠️ 未找到 news_announcement_data 模块，无法使用问财兜底")
                except Exception as e:
                    print(f"   ⚠️ 问财数据源获取失败: {e}")

            if not news_items:
                print(f"   未找到股票 {symbol} 的新闻")
                return None
            
            # 限制数量
            news_items = news_items[:self.max_items]
            
            return {
                "items": news_items,
                "count": len(news_items),
                "query_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "date_range": "最近新闻"
            }
            
        except Exception as e:
            print(f"   获取新闻数据异常: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def format_news_for_ai(self, data):
        """
        将新闻数据格式化为适合AI阅读的文本
        """
        if not data or not data.get("data_success"):
            return "未能获取新闻数据"
        
        text_parts = []
        
        # 新闻数据
        if data.get("news_data"):
            news_data = data["news_data"]
            text_parts.append(f"""
【最新新闻 - akshare数据源】
查询时间：{news_data.get('query_time', 'N/A')}
时间范围：{news_data.get('date_range', 'N/A')}
新闻数量：{news_data.get('count', 0)}条

""")
            
            for idx, item in enumerate(news_data.get('items', []), 1):
                text_parts.append(f"新闻 {idx}:")
                
                # 优先显示的字段
                priority_fields = ['title', 'date', 'time', 'source', 'content', 'url']
                
                # 先显示优先字段
                for field in priority_fields:
                    if field in item:
                        value = item[field]
                        # 限制content长度
                        if field == 'content' and len(str(value)) > 500:
                            value = str(value)[:500] + "..."
                        text_parts.append(f"  {field}: {value}")
                
                # 再显示其他字段
                for key, value in item.items():
                    if key not in priority_fields and key != 'source':
                        # 跳过过长的字段
                        if len(str(value)) > 300:
                            value = str(value)[:300] + "..."
                        text_parts.append(f"  {key}: {value}")
                
                text_parts.append("")  # 空行分隔
        
        return "\n".join(text_parts)


# 测试函数
if __name__ == "__main__":
    print("测试新闻数据获取（akshare数据源）...")
    print("="*60)
    
    fetcher = QStockNewsDataFetcher()
    
    if not fetcher.available:
        print("❌ 新闻数据获取器不可用")
        sys.exit(1)
    
    # 测试股票
    test_symbols = ["000001", "600519"]  # 平安银行、贵州茅台
    
    for symbol in test_symbols:
        print(f"\n{'='*60}")
        print(f"正在测试股票: {symbol}")
        print(f"{'='*60}\n")
        
        data = fetcher.get_stock_news(symbol)
        
        if data.get("data_success"):
            print("\n" + "="*60)
            print("新闻数据获取成功！")
            print("="*60)
            
            formatted_text = fetcher.format_news_for_ai(data)
            print(formatted_text)
        else:
            print(f"\n获取失败: {data.get('error', '未知错误')}")
        
        print("\n")

