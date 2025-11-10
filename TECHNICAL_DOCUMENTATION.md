# 天心多AI智能体股票分析系统技术文档

## 1. 项目概述

天心多AI智能体股票分析系统是一个基于复合AI智能体的股票分析和交易辅助系统。该系统模拟证券公司分析师团队，通过多个专业领域的AI智能体协作，为用户提供全方位的股票投资分析和决策建议。

该项目主要面向中国A股市场，包含多个功能模块：
- 基础股票分析（技术面、基本面、资金面、风险管理）
- 龙虎榜分析（游资行为分析、个股潜力挖掘）
- 板块策略分析（宏观策略、行业趋势、资金流向、市场情绪）
- 主力选股分析
- 持仓管理与定时分析
- 智能盯盘与自动交易

## 2. 技术架构

### 2.1 核心架构

系统采用模块化设计，主要由以下组件构成：

1. **AI智能体集群**：多个专业领域的AI分析智能体
2. **数据获取层**：从多个数据源获取股票相关信息
3. **决策引擎**：基于AI分析结果生成投资决策
4. **交易执行层**：支持模拟交易和实盘交易
5. **用户界面**：基于Streamlit的Web界面
6. **数据存储层**：SQLite数据库存储历史数据和分析结果
7. **通知系统**：邮件和Webhook通知机制

### 2.2 AI智能体集群

系统包含多个专业AI智能体，每个智能体专注于特定领域的分析：

#### 2.2.1 基础分析智能体（ai_agents.py）

1. **技术分析师**：负责技术指标分析、图表形态识别、趋势判断
2. **基本面分析师**：负责公司财务分析、行业研究、估值分析
3. **资金面分析师**：负责资金流向分析、主力行为研究、市场情绪判断
4. **风险管理师**：负责风险评估和控制建议
5. **市场情绪分析师**：分析市场情绪和投资者心理
6. **新闻分析师**：分析新闻事件和舆情影响

#### 2.2.2 龙虎榜分析智能体（longhubang_agents.py）

1. **游资行为分析师**：分析游资操作特征和意图
2. **个股潜力分析师**：从龙虎榜数据挖掘潜力股
3. **资金趋势分析师**：分析资金流向趋势和热点板块
4. **市场情绪分析师**：分析市场情绪和投资者心理

#### 2.2.3 板块策略智能体（sector_strategy_agents.py）

1. **宏观策略师**：分析宏观经济和新闻对板块的影响
2. **行业趋势分析师**：分析行业发展趋势和投资机会
3. **资金流向分析师**：分析资金在不同板块间的流动
4. **市场情绪分析师**：分析市场情绪和投资者心理

## 3. 多智能体交互机制

### 3.1 协作模式

系统采用并行分析模式，多个专业智能体同时对同一目标进行分析，然后将分析结果汇总形成综合报告。每个智能体都有明确的职责和专业领域，确保分析的专业性和全面性。

### 3.2 数据分发机制

1. **数据获取**：系统从多个数据源获取股票相关信息
2. **数据分发**：将获取的数据按照智能体需求进行分发
3. **并行分析**：各智能体并行处理分配的数据
4. **结果整合**：将各智能体分析结果进行整合

### 3.3 交互流程

```python
# 多智能体协调示例
def analyze_stock_comprehensive(self, stock_info, stock_data, indicators, financial_data, fund_flow_data, risk_data, quarterly_data):
    """综合分析 - 协调多个AI智能体进行并行分析"""
    # 创建分析任务
    analysis_tasks = []
    
    # 技术面分析
    technical_task = self.technical_analyst_agent(stock_info, stock_data, indicators)
    analysis_tasks.append(technical_task)
    
    # 基本面分析
    fundamental_task = self.fundamental_analyst_agent(stock_info, financial_data, quarterly_data)
    analysis_tasks.append(fundamental_task)
    
    # 资金面分析
    fund_flow_task = self.fund_flow_analyst_agent(stock_info, indicators, fund_flow_data)
    analysis_tasks.append(fund_flow_task)
    
    # 风险管理分析
    risk_task = self.risk_management_agent(stock_info, indicators, risk_data)
    analysis_tasks.append(risk_task)
    
    # 等待所有分析完成并整合结果
    comprehensive_analysis = self._integrate_analyses(analysis_tasks)
    
    return comprehensive_analysis
```

### 3.4 分析结果整合

系统通过以下方式整合多个智能体的分析结果：

1. **结构化存储**：每个智能体的分析结果以结构化格式存储
2. **权重分配**：根据不同分析类型的重要性分配权重
3. **综合评估**：基于所有分析结果生成综合评估报告
4. **决策建议**：根据综合评估生成具体的投资建议

### 3.5 实时通信机制

为了实现分析过程的透明化和实时可视化，系统采用了以下通信机制：

1. **WebSocket通信**：后端通过WebSocket将关键分析节点的输出实时推送到前端
2. **消息类型定义**：定义专门的分析类型及其子类型（如debate_turn、risk_assessment），以结构化方式传递不同阶段的分析结果
3. **分段发送机制**：后端在执行过程中主动分段发送中间结果，避免仅返回最终结论，确保用户能够追溯完整的决策链条
4. **前端解析渲染**：前端支持对各类分析消息的解析、分类展示、样式区分和逐条渲染，提供动态更新的分析过程视图

## 4. 分析团队辩论流程

### 4.1 团队构成

系统模拟一个专业的投资分析团队，包括以下角色：

1. **技术分析师**：专注于技术指标、图表形态和趋势分析
2. **基本面分析师**：负责公司财务状况、行业地位和估值水平分析
3. **资金面分析师**：分析资金流向、主力行为和市场情绪
4. **风险管理师**：识别和评估各类投资风险
5. **市场情绪分析师**：分析整体市场情绪和投资者心理
6. **新闻分析师**：分析新闻事件和舆情影响

### 4.2 辩论流程

#### 4.2.1 并行分析阶段

1. **任务分配**：系统根据分析目标为每个智能体分配相应的分析任务
2. **数据准备**：为每个智能体准备所需的数据
3. **独立分析**：各智能体并行进行独立分析，生成各自的分析报告

#### 4.2.2 团队讨论阶段

在所有智能体完成独立分析后，系统启动团队讨论流程：

```python
def conduct_team_discussion(self, agents_results: Dict[str, Any], stock_info: Dict) -> str:
    """进行团队讨论"""
    print("🤝 分析团队正在进行综合讨论...")
    time.sleep(2)
    
    # 收集参与分析的分析师名单和报告
    participants = []
    reports = []
    
    if "technical" in agents_results:
        participants.append("技术分析师")
        reports.append(f"【技术分析师报告】\n{agents_results['technical'].get('analysis', '')}")
    
    if "fundamental" in agents_results:
        participants.append("基本面分析师")
        reports.append(f"【基本面分析师报告】\n{agents_results['fundamental'].get('analysis', '')}")
    
    if "fund_flow" in agents_results:
        participants.append("资金面分析师")
        reports.append(f"【资金面分析师报告】\n{agents_results['fund_flow'].get('analysis', '')}")
    
    if "risk_management" in agents_results:
        participants.append("风险管理师")
        reports.append(f"【风险管理师报告】\n{agents_results['risk_management'].get('analysis', '')}")
    
    if "market_sentiment" in agents_results:
        participants.append("市场情绪分析师")
        reports.append(f"【市场情绪分析师报告】\n{agents_results['market_sentiment'].get('analysis', '')}")
    
    if "news" in agents_results:
        participants.append("新闻分析师")
        reports.append(f"【新闻分析师报告】\n{agents_results['news'].get('analysis', '')}")
    
    # 组合所有报告
    all_reports = "\n\n".join(reports)
    
    discussion_prompt = f"""
现在进行投资决策团队会议，参会人员包括：{', '.join(participants)}。

股票：{stock_info.get('name', 'N/A')} ({stock_info.get('symbol', 'N/A')})

各分析师报告：

{all_reports}

请模拟一场真实的投资决策会议讨论：
1. 各分析师观点的一致性和分歧
2. 不同维度分析的权重考量
3. 风险收益评估
4. 投资时机判断
5. 策略制定思路
6. 达成初步共识

请以对话形式展现讨论过程，体现专业团队的思辨过程。
注意：只讨论参与分析的分析师的观点。
"""
    
    messages = [
        {"role": "system", "content": "你需要模拟一场专业的投资团队讨论会议，体现不同角色的观点碰撞和最终共识形成。"},
        {"role": "user", "content": discussion_prompt}
    ]
    
    discussion_result = self.deepseek_client.call_api(messages, max_tokens=6000)
    
    print("✅ 团队讨论完成")
    return discussion_result
```

#### 4.2.3 讨论内容

在团队讨论阶段，AI会模拟以下讨论内容：

1. **观点一致性分析**：分析各分析师观点的一致性和分歧点
2. **权重考量**：根据不同分析维度的重要性分配权重
3. **风险收益评估**：综合评估投资的风险收益比
4. **投资时机判断**：判断当前是否为合适的投资时机
5. **策略制定思路**：制定具体的投资策略
6. **达成初步共识**：形成初步的投资共识

#### 4.2.4 最终决策阶段

在团队讨论完成后，系统进入最终决策阶段：

```python
def final_decision(self, discussion_result: str, stock_info: Dict, indicators: Dict) -> Dict[str, Any]:
    """制定最终投资决策"""
    print("📋 正在制定最终投资决策...")
    time.sleep(1)
    
    decision = self.deepseek_client.final_decision(discussion_result, stock_info, indicators)
    
    print("✅ 最终投资决策完成")
    return decision
```

最终决策包含以下要素：
1. **投资评级**：买入/持有/卖出
2. **目标价位**：具体的目标价格
3. **操作建议**：具体的买入/卖出策略
4. **进场位置**：具体的进场价位区间
5. **止盈位置**：止盈价位
6. **止损位置**：止损价位
7. **持有周期建议**：建议的持有时间
8. **风险提示**：潜在风险提示
9. **仓位建议**：建议的仓位大小

### 4.3 辩论特点

1. **专业性**：每个智能体都具备专业领域的深度知识
2. **多维度**：从技术、基本面、资金面、风险等多个维度进行分析
3. **交互性**：通过团队讨论实现观点的交互和融合
4. **透明性**：整个辩论过程对用户可见，提高决策的可信度
5. **可追溯性**：保留完整的分析和讨论过程，便于回溯和验证

## 5. 股票分析模块详解

### 5.1 技术分析模块

技术分析模块主要负责对股票的技术指标进行分析，包括：

- **趋势分析**：均线系统、价格走势分析
- **超买超卖分析**：RSI、KDJ等指标分析
- **动量分析**：MACD等动量指标分析
- **支撑阻力分析**：布林带等支撑阻力位分析
- **成交量分析**：成交量和换手率分析

技术分析模块通过调用AI模型，基于股票的技术指标数据生成专业的技术分析报告。

### 5.2 基本面分析模块

基本面分析模块负责对公司财务状况、行业地位、估值水平等进行分析：

- **财务指标分析**：盈利能力、偿债能力、运营能力等
- **行业分析**：行业地位、竞争优势分析
- **估值分析**：PE、PB等估值指标分析
- **成长性分析**：营收增长、利润增长等分析
- **季报趋势分析**：基于季报数据的趋势分析

### 5.3 资金面分析模块

资金面分析模块专注于资金流向和市场情绪分析：

- **资金流向分析**：主力资金流入流出分析
- **主力行为研究**：主力资金操作行为分析
- **市场情绪判断**：基于市场数据的情绪分析
- **流动性分析**：股票流动性状况分析

### 5.4 风险管理模块

风险管理模块负责识别和评估投资风险：

- **系统性风险评估**：宏观经济风险、市场风险等
- **非系统性风险评估**：公司特定风险、行业风险等
- **流动性风险评估**：交易流动性风险分析
- **波动性风险评估**：价格波动风险分析
- **估值风险评估**：估值过高风险分析

## 6. 信息源获取机制

### 6.1 数据源类型

系统从多个数据源获取股票相关信息：

1. **股票基础数据**：股票代码、名称、当前价格等基本信息
2. **技术指标数据**：均线、RSI、MACD等技术指标
3. **财务数据**：公司财务报表、财务指标等
4. **资金流向数据**：主力资金流入流出数据
5. **风险数据**：限售解禁、大股东减持等风险信息
6. **季报数据**：季度财务报表数据
7. **新闻资讯数据**：财经新闻、公告等信息
8. **龙虎榜数据**：游资交易数据
9. **板块数据**：行业板块相关信息

### 6.2 数据获取流程

```python
# 数据获取示例
def fetch_stock_data(self, stock_code):
    """获取股票相关数据"""
    # 获取股票基础信息
    stock_info = self.fetch_basic_info(stock_code)
    
    # 获取技术指标数据
    stock_data, indicators = self.fetch_technical_data(stock_code)
    
    # 获取财务数据
    financial_data = self.fetch_financial_data(stock_code)
    
    # 获取资金流向数据
    fund_flow_data = self.fetch_fund_flow_data(stock_code)
    
    # 获取风险数据
    risk_data = self.fetch_risk_data(stock_code)
    
    # 获取季报数据
    quarterly_data = self.fetch_quarterly_data(stock_code)
    
    return {
        'stock_info': stock_info,
        'stock_data': stock_data,
        'indicators': indicators,
        'financial_data': financial_data,
        'fund_flow_data': fund_flow_data,
        'risk_data': risk_data,
        'quarterly_data': quarterly_data
    }
```

### 6.3 数据处理与分发

获取的数据经过处理后分发给对应的AI智能体：

1. **数据清洗**：对原始数据进行清洗和格式化
2. **数据验证**：验证数据的完整性和准确性
3. **数据分发**：将处理后的数据分发给相应的AI智能体
4. **数据缓存**：对常用数据进行缓存以提高性能

### 6.4 数据源管理机制

系统采用多数据源管理机制，确保数据获取的稳定性和可靠性：

#### 6.4.1 主备数据源切换

系统实现了akshare和tushare数据源的自动切换机制：

- **主数据源**：akshare，优先使用
- **备用数据源**：tushare，当akshare不可用时自动切换
- **自动检测**：系统会自动检测数据源可用性并进行切换

#### 6.4.2 数据标准化

不同数据源返回的数据格式可能不同，系统会对数据进行标准化处理：

- **列名统一**：将不同数据源的列名统一为标准格式
- **数据类型统一**：确保数据类型一致
- **日期格式统一**：将日期格式统一为标准格式

#### 6.4.3 风险数据获取

系统通过pywencai获取风险相关数据：

- **限售解禁数据**：获取股票的限售解禁信息
- **大股东减持数据**：获取大股东减持公告信息
- **重要事件数据**：获取股票的重要事件信息

#### 6.4.4 资金流向数据获取

系统通过akshare获取资金流向数据：

- **个股资金流向**：获取个股的资金流入流出情况
- **行业资金流向**：获取行业的资金流向情况
- **概念资金流向**：获取概念板块的资金流向情况

## 7. AI决策系统

### 7.1 AI模型集成

系统使用DeepSeek API作为AI推理引擎，支持多种模型，包括：

1. **qwen3-max**：通用分析模型
2. **deepseek-reasoner**：强化推理模型，适用于复杂分析任务

### 7.2 提示词工程

系统为每个AI智能体设计了专业的提示词（Prompt Engineering），确保AI能够准确理解分析任务并生成高质量的分析结果。

### 7.3 决策生成流程

1. 构建专业提示词（Prompt Engineering）
2. 调用AI模型进行分析
3. 处理和格式化AI响应
4. 整合多个智能体的分析结果

## 8. 智能盯盘与自动交易系统

### 8.1 实时监控

系统包含一个智能盯盘引擎，支持：

1. **实时数据获取**：从多个数据源获取实时股票数据
2. **AI决策**：基于实时数据进行分析和决策
3. **交易执行**：支持模拟交易和实盘交易（通过miniQMT接口）
4. **通知系统**：交易信号和决策通知

### 8.2 自动交易

自动交易模块支持：

1. **T+1规则适配**：完全遵循A股T+1交易规则
2. **持仓管理**：记录持仓成本，实时显示盈亏
3. **风险控制**：基于AI分析的风险控制机制

## 9. 技术特点

### 9.1 多智能体协作

系统采用多智能体协作模式，每个智能体专注于特定领域，确保分析的专业性和全面性。

### 9.2 AI强化推理

使用支持推理过程输出的AI模型，能够展示AI的思考过程，提高决策的透明度和可信度。

### 9.3 实时监控与自动交易

支持实时股票监控和基于AI决策的自动交易，完全符合A股T+1交易规则。

### 9.4 灵活的模型配置

支持多种AI模型配置，用户可以根据需要选择不同的模型进行分析。

### 9.5 完整的数据管理

使用SQLite数据库存储历史数据和分析结果，支持数据查询和回测分析。