# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.
## 项目开发规范与文档标准
在本次会话及所有代码生成任务中，必须严格遵守以下开发规范。

1. 文档注释规范
1.1 文件头注释标准
所有代码文件（如 .py, .js, .ts 等）必须在文件开头包含清晰的注释块。注释块需包含以下关键信息：

Contains (包含内容): 列出文件中定义的主要函数、类或组件名称。
Responsibilities (负责功能): 明确该文件的核心职责和功能点。
Non-Responsibilities (不负责功能): 明确界定该文件不处理的内容，防止职责扩散。
Input (输入): 描述该文件接收的输入数据来源、格式或类型。
Output (输出): 描述该文件产出的结果、副作用或返回值。
示例模板：

"""@File: example_module.py@Contains: [function_a, ClassB]@Responsibilities:    - 负责处理用户数据的清洗与格式化    - 负责生成数据报表@Non-Responsibilities:    - 不负责数据库连接管理    - 不负责用户权限验证@Input: 原始用户数据 JSON 对象@Output: 格式化后的数据字典或报表文件路径"""
1.2 文件夹索引文档 (folder.md)
每个功能文件夹内必须包含一个 folder.md 文件，用于描述该目录的整体架构。

功能范围: 该文件夹内代码文件共同实现的功能。
边界定义: 该文件夹模块不涉及的职责。
接口定义: 该模块对外的输入与输出接口。
文件清单: 简要说明文件夹内各代码文件的作用。
2. 文档维护机制
实时同步原则：

每次修改代码逻辑、新增函数或删除文件时，必须立即更新对应的文件头注释。
每次在文件夹内新增、删除文件或改变模块职责时，必须立即更新 folder.md。
文档更新是代码提交的一部分，不可遗漏。
3. 代码实现与重构策略
3.1 优先重用原则
在开发新功能或修复 Bug 时，必须遵循以下优先级：

检查现有实现: 在编写新代码前，必须全面搜索项目代码库，确认是否已存在相同或相似的实现。
优先改动: 如果存在相似实现，优先考虑扩展现有函数、抽象公共方法或重构现有代码，而不是创建新文件或复制代码。
避免冗余: 坚决避免重复造轮子，确保代码的 DRY (Don't Repeat Yourself) 特性。
3.2 决策确认机制
在以下场景中，必须暂停编码，提出方案并向用户确认：

发现已有多处相似实现，不确定应复用哪一个。
存在多种技术方案可实现需求，且各有利弊。
预计的重构改动范围较大，可能影响其他模块。
3.3 计划先行流程
执行任何代码修改前，必须遵循“计划-确认-执行”流程：

停止编码: 不要直接开始修改文件。
列出计划: 清晰列出即将执行的修改步骤、涉及的文件及原因。
等待确认: 向用户展示计划，等待用户回复“确认”或“同意”。
执行修改: 获得许可后，方可开始代码编写与文档更新。
## Project Overview

天心多AI智能体股票分析系统 (Tianxin Multi-AI Agent Stock Analysis System) - A multi-AI agent stock analysis system for Chinese A-shares, Hong Kong stocks, and US stocks. The system simulates a securities analyst team with specialized AI agents working collaboratively.

## Common Commands

### Running the Application
```bash
# Using run.py (checks dependencies and config)
python run.py

# Direct Streamlit command
streamlit run app.py --server.port 8503 --server.address 0.0.0.0

# With virtual environment
source venv/bin/activate  # Linux/macOS
.\venv\Scripts\Activate.ps1  # Windows PowerShell
streamlit run app.py
```

### Installing Dependencies
```bash
pip install -r requirements.txt
```

### Docker Deployment
```bash
# Using docker-compose
docker-compose up -d

# Manual build and run
docker build -t agentsstock1 .
docker run -d -p 8503:8501 -v $(pwd)/.env:/app/.env --name agentsstock1 agentsstock1
```

## Architecture

### Core Data Flow
```
User Input → StockDataFetcher → Data Processing → Multi-Agent Analysis → Team Discussion → Final Decision → PDF Report
```

### Key Modules

**Data Layer:**
- `stock_data.py` - Stock data fetching (yfinance, AKShare), technical indicator calculation
- `data_source_manager.py` - Multi-source data management with fallback (TDX → Tushare → AKShare)
- `fund_flow_akshare.py` - Fund flow data from AKShare
- `quarterly_report_data.py` - Quarterly financial reports via pywencai
- `risk_data_fetcher.py` - Risk data (share unlocks, insider selling) via pywencai

**AI Agent Layer:**
- `deepseek_client.py` - OpenAI-compatible API client for DeepSeek/other LLMs
- `ai_agents.py` - Core multi-agent system (Technical, Fundamental, Fund Flow, Risk, Market Sentiment, News analysts)
- `longhubang_agents.py` - Longhubang (龙虎榜) specialized agents
- `sector_strategy_agents.py` - Sector strategy agents (Macro, Sector Diagnosis, Fund Flow, Market Sentiment)
- `main_force_analysis.py` - Main force capital flow analysis

**Engine Layer:**
- `longhubang_engine.py` - Longhubang analysis orchestration
- `sector_strategy_engine.py` - Sector strategy analysis orchestration
- `smart_monitor_engine.py` - Smart monitoring engine for automated trading decisions

**UI Layer (Streamlit):**
- `app.py` - Main application entry point with sidebar navigation
- `longhubang_ui.py`, `sector_strategy_ui.py`, `main_force_ui.py`, `monitor_ui.py`, `smart_monitor_ui.py`, `portfolio_ui.py` - Feature-specific UI modules

**Services:**
- `monitor_service.py` - Background monitoring service
- `notification_service.py` - Email and Webhook (DingTalk/Feishu) notifications
- `portfolio_scheduler.py`, `sector_strategy_scheduler.py`, `monitor_scheduler.py` - Scheduled task management
- `miniqmt_interface.py` - MiniQMT trading interface for automated execution

**Database (SQLite + Peewee ORM):**
- `database.py`, `monitor_db.py`, `longhubang_db.py`, `portfolio_db.py`, `smart_monitor_db.py`, `sector_strategy_db.py`, `main_force_batch_db.py`

### Multi-Agent Analysis Pattern

The system uses parallel analysis with specialized agents:

```python
# From ai_agents.py - agents run in parallel, then results are synthesized
agents_results = {
    "technical": self.technical_analyst_agent(...),
    "fundamental": self.fundamental_analyst_agent(...),
    "fund_flow": self.fund_flow_analyst_agent(...),
    "risk_management": self.risk_management_agent(...),
    # ... more agents
}
# Team discussion synthesizes all agent outputs
discussion = self.conduct_team_discussion(agents_results, stock_info)
# Final decision generated
decision = self.final_decision(discussion, stock_info, indicators)
```

## Configuration

### Environment Variables (.env)
Required:
- `DEEPSEEK_API_KEY` - DeepSeek API key for LLM calls
- `DEEPSEEK_BASE_URL` - API endpoint (default: https://api.deepseek.com/v1)

Optional:
- `TUSHARE_TOKEN` - Tushare data source token
- `TDX_ENABLED`, `TDX_BASE_URL` - Local TDX data source
- `MINIQMT_*` - MiniQMT trading interface config
- `EMAIL_*` - Email notification settings
- `WEBHOOK_*` - DingTalk/Feishu webhook settings
- `TIMEZONE` - Default: Asia/Shanghai

### Model Selection
Models are defined in `model_config.py`. Supports DeepSeek, Qwen (阿里百炼), and SiliconFlow models. The system uses OpenAI-compatible API interface.

## Key Patterns

### Adding a New Analysis Feature
1. Create data fetcher module if needed (follow pattern in `stock_data.py`)
2. Create agent functions in dedicated `*_agents.py` file
3. Create engine module for orchestration (`*_engine.py`)
4. Create UI module (`*_ui.py`) with `display_*` function
5. Import and call UI function in `app.py` sidebar navigation
6. Create database module (`*_db.py`) if persistence needed
7. Create PDF generator (`*_pdf.py`) if report export needed

### Database Pattern
All database modules use Peewee ORM with SQLite. Tables are defined as Peewee Model classes. Use `database.py` as reference.

### UI Pattern
UI modules use Streamlit components. Main `app.py` handles navigation via sidebar radio buttons. Each feature module has a `display_*` function called from main app.

### API Client Pattern
`DeepSeekClient` wraps OpenAI SDK. All LLM calls go through `call_api()` method. For reasoner models, automatically extracts `reasoning_content` if present.

## Stock Code Formats
- A股: 6-digit code (000001, 600036)
- 港股: 1-5 digit code (700, 9988) or with HK prefix
- 美股: Letter code (AAPL, TSLA)

## Important Files
- `run.py` - Entry point with dependency checking
- `config.py` - Environment variable loading and configuration constants
- `config_manager.py` - Web UI for configuration management
- `model_config.py` - Available LLM model options

## Notes
- Default server port: 8503 (changed from 8501 to avoid conflicts)
- System designed for Chinese A-share T+1 trading rules
- PDF generation uses pyppeteer (Chrome headless) for Markdown-to-PDF conversion