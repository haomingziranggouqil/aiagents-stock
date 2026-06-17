"""
数据聚合层
统一封装个股分析所需的补充数据获取（财务/季报/资金流/情绪/新闻/风险），
带 Streamlit 缓存，供单股分析、批量分析等多处复用，消除重复代码。
"""

import streamlit as st

from data.stock_data import StockDataFetcher

# 缓存时长（秒）。补充数据变化不频繁，5分钟内复用避免重复请求。
_CACHE_TTL = 300


def _is_chinese_stock(symbol):
    return symbol.isdigit() and len(symbol) == 6


# ---------------------------------------------------------------------------
# 各数据源的带缓存获取函数
# 同一 symbol 在 TTL 内只请求一次，Streamlit rerun 不会重复打接口。
# show_spinner=False：进度提示由上层 status 回调统一控制。
# ---------------------------------------------------------------------------

@st.cache_data(ttl=_CACHE_TTL, show_spinner=False)
def fetch_financial(symbol):
    """基础财务数据（始终获取）"""
    return StockDataFetcher().get_financial_data(symbol)


@st.cache_data(ttl=_CACHE_TTL, show_spinner=False)
def fetch_quarterly(symbol):
    """季报数据（利润表/资产负债表/现金流）"""
    from data.quarterly_report_data import QuarterlyReportDataFetcher
    return QuarterlyReportDataFetcher().get_quarterly_reports(symbol)


@st.cache_data(ttl=_CACHE_TTL, show_spinner=False)
def fetch_fund_flow(symbol):
    """资金流向数据"""
    from data.fund_flow_akshare import FundFlowAkshareDataFetcher
    return FundFlowAkshareDataFetcher().get_fund_flow_data(symbol)


@st.cache_data(ttl=_CACHE_TTL, show_spinner=False)
def fetch_sentiment(symbol, stock_data):
    """市场情绪数据（ARBR/换手率/涨跌停等）"""
    from data.market_sentiment_data import MarketSentimentDataFetcher
    return MarketSentimentDataFetcher().get_market_sentiment_data(symbol, stock_data)


@st.cache_data(ttl=_CACHE_TTL, show_spinner=False)
def fetch_news(symbol):
    """个股新闻数据"""
    from data.qstock_news_data import QStockNewsDataFetcher
    return QStockNewsDataFetcher().get_stock_news(symbol)


@st.cache_data(ttl=_CACHE_TTL, show_spinner=False)
def fetch_risk(symbol):
    """风险数据（限售解禁/大股东减持/重要事件）"""
    return StockDataFetcher().get_risk_data(symbol)


# ---------------------------------------------------------------------------
# 统一编排
# ---------------------------------------------------------------------------

# 默认分析师开关（无配置时使用）
DEFAULT_ANALYSTS = {
    'technical': True,
    'fundamental': True,
    'fund_flow': True,
    'risk': True,
    'sentiment': False,
    'news': False,
}


def collect_supplementary_data(symbol, stock_data, analysts=None, status=None):
    """根据分析师开关获取全部补充数据。

    Args:
        symbol: 股票代码
        stock_data: 已获取的历史行情（情绪指标计算需要）
        analysts: 分析师开关字典，None 时用 DEFAULT_ANALYSTS
        status: 可选回调 status(stage_text, info_text)，用于上层显示进度/提示。
                stage_text 为正在进行的阶段；info_text 为结果摘要（成功/警告），可为 None。

    Returns:
        dict: {financial, quarterly, fund_flow, sentiment, news, risk}
              对应数据；未启用或非A股或失败的项为 None。
    """
    if analysts is None:
        analysts = DEFAULT_ANALYSTS

    def notify(stage, info=None):
        if status:
            status(stage, info)

    is_cn = _is_chinese_stock(symbol)
    result = {
        'financial': None, 'quarterly': None, 'fund_flow': None,
        'sentiment': None, 'news': None, 'risk': None,
    }

    # 1. 基础财务数据（始终获取）
    notify("📊 正在获取财务数据...")
    try:
        result['financial'] = fetch_financial(symbol)
    except Exception as e:
        notify(None, ("warning", f"获取财务数据时出错: {e}"))

    # 2. 季报数据（基本面分析师 + A股）
    if analysts.get('fundamental', True):
        if is_cn:
            notify("📊 正在获取季报数据...")
            try:
                result['quarterly'] = fetch_quarterly(symbol)
            except Exception as e:
                notify(None, ("warning", f"获取季报数据时出错: {e}"))
        else:
            notify(None, ("info", "美股暂不支持季报数据"))

    # 3. 资金流向（资金面分析师 + A股）
    if analysts.get('fund_flow', True):
        if is_cn:
            notify("💰 正在获取资金流向数据...")
            try:
                result['fund_flow'] = fetch_fund_flow(symbol)
            except Exception as e:
                notify(None, ("warning", f"获取资金流向数据时出错: {e}"))
        else:
            notify(None, ("info", "美股暂不支持资金流向数据"))

    # 4. 市场情绪（情绪分析师 + A股）
    if analysts.get('sentiment', False):
        if is_cn:
            notify("📊 正在获取市场情绪数据...")
            try:
                result['sentiment'] = fetch_sentiment(symbol, stock_data)
            except Exception as e:
                notify(None, ("warning", f"获取市场情绪数据时出错: {e}"))
        else:
            notify(None, ("info", "美股暂不支持市场情绪数据"))

    # 5. 新闻（新闻分析师 + A股）
    if analysts.get('news', False):
        if is_cn:
            notify("📰 正在获取新闻数据...")
            try:
                result['news'] = fetch_news(symbol)
            except Exception as e:
                notify(None, ("warning", f"获取新闻数据时出错: {e}"))
        else:
            notify(None, ("info", "美股暂不支持新闻数据"))

    # 6. 风险数据（风险管理师 + A股）
    if analysts.get('risk', True):
        if is_cn:
            notify("⚠️ 正在获取风险数据...")
            try:
                result['risk'] = fetch_risk(symbol)
            except Exception as e:
                notify(None, ("warning", f"获取风险数据时出错: {e}"))
        else:
            notify(None, ("info", "美股暂不支持风险数据"))

    return result
