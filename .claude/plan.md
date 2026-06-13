# 项目目录整理 + 清理垃圾方案

## 目标
将 70+ 个扁平文件按功能分组到子目录，清理测试产物和冗余文件，保持项目可正常运行。

---

## 一、清理垃圾文件（直接删除）

| 文件 | 原因 |
|------|------|
| `test_browser_report.pdf` | 测试产物 |
| `test_stock_report.pdf` | 测试产物 |
| `risk_data_debug_output.txt` | 调试输出 |
| `stm.py` | 部署脚本草稿，内容是 shell 命令不是 Python |
| `env_example.txt` | 与 `.env.example` 重复 |
| `test_browser_pdf.py` | 测试脚本 |
| `test_llm_prompt.py` | 测试脚本 |
| `update_env_example.py` | 一次性工具脚本 |
| `.trae/` 目录 | Trae IDE 的内部文档，非项目代码 |
| `Dockerfile国际源版` | 与标准 Dockerfile 重复，可合并说明到 docs |

---

## 二、目录结构重组

```
aiagents-stock/
├── app.py                        # 主入口（保留根目录）
├── run.py                        # 启动脚本（保留根目录）
├── config.py                     # 配置常量（保留根目录）
├── model_config.py               # 模型配置（保留根目录）
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .dockerignore
├── .gitignore
├── README.md
├── CLAUDE.md
├── BUILD_CN.md
├── TECHNICAL_DOCUMENTATION.md
├── .streamlit/
│
├── core/                         # 核心基础设施
│   ├── __init__.py
│   ├── deepseek_client.py        # LLM API 客户端
│   ├── config_manager.py         # Web配置管理
│   ├── data_source_manager.py    # 多数据源管理
│   ├── notification_service.py   # 通知服务(邮件/Webhook)
│   └── database.py               # 主分析记录数据库
│
├── data/                         # 数据采集层
│   ├── __init__.py
│   ├── stock_data.py             # 股票行情+技术指标
│   ├── fund_flow_akshare.py      # 资金流向(AKShare)
│   ├── quarterly_report_data.py  # 季报数据(pywencai)
│   ├── risk_data_fetcher.py      # 风险数据(pywencai)
│   ├── market_sentiment_data.py  # 市场情绪数据
│   ├── news_announcement_data.py # 新闻公告数据
│   └── qstock_news_data.py       # qstock新闻数据
│
├── agents/                       # AI智能体层
│   ├── __init__.py
│   ├── ai_agents.py              # 核心6人分析师团队
│   ├── longhubang_agents.py      # 龙虎榜5人分析师
│   ├── sector_strategy_agents.py # 板块策略4人团队
│   └── main_force_analysis.py    # 主力选股AI分析
│
├── modules/                      # 功能模块
│   ├── __init__.py
│   ├── longhubang/               # 智瞰龙虎
│   │   ├── __init__.py
│   │   ├── engine.py             # longhubang_engine.py
│   │   ├── data.py               # longhubang_data.py
│   │   ├── db.py                 # longhubang_db.py
│   │   ├── scoring.py            # longhubang_scoring.py
│   │   ├── pdf.py                # longhubang_pdf.py
│   │   └── ui.py                 # longhubang_ui.py
│   │
│   ├── sector_strategy/          # 智策板块
│   │   ├── __init__.py
│   │   ├── engine.py
│   │   ├── data.py
│   │   ├── db.py
│   │   ├── scheduler.py
│   │   ├── pdf.py
│   │   └── ui.py
│   │
│   ├── main_force/               # 主力选股
│   │   ├── __init__.py
│   │   ├── selector.py           # main_force_selector.py
│   │   ├── batch_db.py
│   │   ├── pdf_generator.py
│   │   ├── history_ui.py
│   │   └── ui.py
│   │
│   ├── smart_monitor/            # AI盯盘
│   │   ├── __init__.py
│   │   ├── engine.py
│   │   ├── data.py
│   │   ├── tdx_data.py
│   │   ├── deepseek.py
│   │   ├── qmt.py
│   │   ├── kline.py
│   │   ├── db.py
│   │   └── ui.py
│   │
│   ├── monitor/                  # 实时监测
│   │   ├── __init__.py
│   │   ├── db.py                 # monitor_db.py
│   │   ├── service.py            # monitor_service.py
│   │   ├── manager.py            # monitor_manager.py
│   │   ├── scheduler.py          # monitor_scheduler.py
│   │   └── ui.py                 # monitor_ui.py
│   │
│   └── portfolio/                # 持仓分析
│       ├── __init__.py
│       ├── db.py                 # portfolio_db.py
│       ├── manager.py            # portfolio_manager.py
│       ├── scheduler.py          # portfolio_scheduler.py
│       └── ui.py                 # portfolio_ui.py
│
├── services/                     # 共享服务/工具
│   ├── __init__.py
│   ├── pdf_generator.py          # 通用PDF生成
│   ├── pdf_browser_launcher.py   # 浏览器PDF工具
│   └── miniqmt_interface.py      # MiniQMT量化交易
│
├── scripts/                      # 部署/安装脚本
│   ├── setup_linux.sh
│   └── setup_windows.bat
│
├── docs/                         # 文档（已有，保持不变）
│
└── data_db/                      # 数据库文件集中存放
    ├── .gitkeep
    └── (运行时生成的 *.db 文件)
```

---

## 三、Import 路径更新策略

由于文件移动后所有 `from xxx import yyy` 都需要更新，采用以下方案：

**方案：根目录兼容层（推荐）**
- 在每个被移走的原始位置放一个单行兼容文件做 re-export
- 例如根目录保留 `deepseek_client.py`，内容为：
  ```python
  from core.deepseek_client import *  # noqa: F401,F403
  ```
- 这样所有现有 import 不会断，后续可逐步迁移调用方

这是最安全的做法——零运行风险，逐步过渡。

---

## 四、数据库文件处理

将 `*.db` 文件移动到 `data_db/` 目录，并更新各 `*_db.py` 中的数据库路径常量。`.gitignore` 中添加 `data_db/*.db`。

---

## 五、执行顺序

1. 删除垃圾文件
2. 创建目录结构
3. 移动文件到对应目录
4. 在根目录创建兼容 re-export 文件
5. 移动 .db 文件到 data_db/，更新路径
6. 更新 .gitignore
7. 验证项目能正常 import（python -c 测试）

---

## 六、不动的文件

- `app.py` — Streamlit 入口必须在根目录
- `run.py` — 启动脚本
- `config.py` — 全局配置，被大量引用
- `model_config.py` — 模型列表
- `monitor_schedule_config.json` — 运行时配置
- 所有 docs/ 内容不变
- `.streamlit/` 不变
