"""
新闻数据获取模块
使用东方财富搜索API + 财联社电报获取股票新闻
"""

import re
import json
import time
import sys
import warnings
from datetime import datetime

import requests
import pandas as pd

warnings.filterwarnings('ignore')


class QStockNewsDataFetcher:
    """新闻数据获取类（东方财富搜索API + 财联社电报）"""

    def __init__(self):
        self.max_items = 30  # 最多获取的新闻数量
        self.available = True
        print("✓ 新闻数据获取器初始化成功")
    
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
        """获取新闻数据（直接请求东方财富搜索API + 财联社电报）"""
        try:
            print(f"   正在获取新闻...")
            news_items = []

            # 方法1: 东方财富搜索API（直接HTTP请求，绕过AKShare的pyarrow bug）
            try:
                items = self._fetch_eastmoney_news(symbol)
                if items:
                    print(f"   ✓ 从东方财富获取到 {len(items)} 条新闻")
                    news_items.extend(items)
            except Exception as e:
                print(f"   ⚠ 从东方财富获取失败: {e}")

            # 方法2: 财联社电报（通过AKShare，筛选相关内容）
            if not news_items or len(news_items) < 5:
                try:
                    import akshare as ak
                    df = ak.stock_news_cls()
                    if df is not None and not df.empty:
                        # 获取股票名称用于匹配
                        stock_name = self._get_stock_name(symbol)
                        keywords = [symbol]
                        if stock_name:
                            keywords.append(stock_name)

                        mask = pd.Series([False] * len(df))
                        for kw in keywords:
                            for col in ['内容', '标题']:
                                if col in df.columns:
                                    mask |= df[col].str.contains(kw, na=False)

                        df_filtered = df[mask]
                        if not df_filtered.empty:
                            print(f"   ✓ 从财联社获取到 {len(df_filtered)} 条相关新闻")
                            for _, row in df_filtered.head(self.max_items - len(news_items)).iterrows():
                                item = {'source': '财联社'}
                                for col in df_filtered.columns:
                                    value = row.get(col)
                                    if value is not None and not (isinstance(value, float) and pd.isna(value)):
                                        item[col] = str(value)
                                if len(item) > 1:
                                    news_items.append(item)
                except Exception as e:
                    print(f"   ⚠ 从财联社获取失败: {e}")

            if not news_items:
                print(f"   未找到股票 {symbol} 的新闻")
                return None

            news_items = news_items[:self.max_items]
            return {
                "items": news_items,
                "count": len(news_items),
                "query_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "date_range": "最近新闻"
            }

        except Exception as e:
            print(f"   获取新闻数据异常: {e}")
            return None

    def _fetch_eastmoney_news(self, symbol, page_size=20):
        """直接请求东方财富搜索API获取个股新闻"""
        url = 'https://search-api-web.eastmoney.com/search/jsonp'
        cb = f'jQuery351_{int(time.time() * 1000)}'
        inner_param = {
            'uid': '',
            'keyword': symbol,
            'type': ['cmsArticleWebOld'],
            'client': 'web',
            'clientType': 'web',
            'clientVersion': 'curr',
            'param': {
                'cmsArticleWebOld': {
                    'searchScope': 'default',
                    'sort': 'default',
                    'pageIndex': 1,
                    'pageSize': page_size,
                    'preTag': '<em>',
                    'postTag': '</em>',
                }
            },
        }
        params = {
            'cb': cb,
            'param': json.dumps(inner_param, ensure_ascii=False),
            '_': str(int(time.time() * 1000)),
        }
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': f'https://so.eastmoney.com/news/s?keyword={symbol}',
        }
        r = requests.get(url, params=params, headers=headers, timeout=10)
        r.raise_for_status()

        # 解析JSONP响应
        text = r.text
        json_str = text[text.index('(') + 1: text.rindex(')')]
        data = json.loads(json_str)
        raw_items = data.get('result', {}).get('cmsArticleWebOld', [])

        # 用Python re清理HTML标签（绕过pyarrow正则bug）
        results = []
        for item in raw_items:
            title = re.sub(r'</?em>', '', item.get('title', ''))
            content = re.sub(r'</?em>', '', item.get('content', ''))
            content = content.replace('　', '').replace('\r\n', ' ')
            results.append({
                'source': '东方财富',
                '新闻标题': title,
                '新闻内容': content[:500] if len(content) > 500 else content,
                '发布时间': item.get('date', ''),
                '文章来源': item.get('mediaName', ''),
                '新闻链接': f"http://finance.eastmoney.com/a/{item.get('code', '')}.html",
            })
        return results

    def _get_stock_name(self, symbol):
        """通过AKShare获取股票名称"""
        try:
            import akshare as ak
            df = ak.stock_zh_a_spot_em()
            if df is not None and not df.empty:
                match = df[df['代码'] == symbol]
                if not match.empty:
                    return match.iloc[0]['名称']
        except Exception:
            pass
        return None
    
    def format_news_for_ai(self, data):
        """将新闻数据格式化为适合AI阅读的文本"""
        if not data or not data.get("data_success"):
            return "未能获取新闻数据"

        text_parts = []

        if data.get("news_data"):
            news_data = data["news_data"]
            text_parts.append(f"""
【最新新闻】
查询时间：{news_data.get('query_time', 'N/A')}
新闻数量：{news_data.get('count', 0)}条

""")

            for idx, item in enumerate(news_data.get('items', []), 1):
                text_parts.append(f"新闻 {idx}:")

                # 优先字段
                priority_fields = ['新闻标题', '发布时间', '文章来源', '新闻内容', '新闻链接']
                for field in priority_fields:
                    if field in item:
                        value = item[field]
                        if field == '新闻内容' and len(str(value)) > 500:
                            value = str(value)[:500] + "..."
                        text_parts.append(f"  {field}: {value}")

                # 其他字段
                for key, value in item.items():
                    if key not in priority_fields and key != 'source':
                        if len(str(value)) > 300:
                            value = str(value)[:300] + "..."
                        text_parts.append(f"  {key}: {value}")

                text_parts.append("")

        return "\n".join(text_parts)


# 测试
if __name__ == "__main__":
    print("测试新闻数据获取...")
    print("=" * 60)

    fetcher = QStockNewsDataFetcher()

    for symbol in ["600519", "000001"]:
        print(f"\n{'=' * 60}")
        print(f"测试股票: {symbol}")
        print(f"{'=' * 60}\n")

        data = fetcher.get_stock_news(symbol)

        if data.get("data_success"):
            formatted = fetcher.format_news_for_ai(data)
            print(formatted[:1000])
        else:
            print(f"获取失败: {data.get('error', '未知错误')}")

