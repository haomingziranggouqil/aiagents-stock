# 🤖 复合多AI智能体股票分析系统

基于 Python + Streamlit + 多AI大模型的智能股票分析系统，模拟证券分析师团队，提供全方位的投资分析和决策建议。

> 初心：让小散不再迷茫。也许这个软件不能让你发大财，但能给你足够的信心。  
> **股市有风险，入市需谨慎！**

<img width="1910" alt="系统截图" src="https://github.com/user-attachments/assets/fe366e1d-2352-46db-a3cc-6f147ee6d9d9" />

## ✨ 核心功能

| 模块 | 说明 |
|------|------|
| 🎯 **AI团队分析** | 7位AI分析师协作：技术面、基本面、资金面、情绪面、风险评估、综合研判 |
| 📊 **AI盯盘** | 实时监控 + DeepSeek AI自动交易决策，支持T+1规则，K线可视化 |
| 💰 **主力选股** | 跟踪主力资金流向，批量深度分析TOP股票 |
| 🐉 **智瞰龙虎** | 龙虎榜数据分析，游资行为识别，题材追踪 |
| 📈 **持仓管理** | 持仓定时分析，评级变化追踪，自动同步监测 |
| 🔔 **智能通知** | 邮件 / 钉钉 / 飞书实时推送分析报告和告警 |
| 📄 **PDF报告** | 一键生成专业分析报告 |

## 🚀 快速开始

### 环境要求

- Python 3.10+
- 大模型 API Key（支持阿里云DashScope / DeepSeek / 硅基流动等）

### 安装部署

```bash
git clone https://github.com/haomingziranggouqil/aiagents-stock.git
cd aiagents-stock

# Linux 一键部署
bash scripts/setup_linux.sh

# 或手动安装
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 配置

复制 `.env.example` 为 `.env`，填写必要配置：

```env
# 必填 - AI大模型（支持OpenAI兼容接口）
DEEPSEEK_API_KEY=your_api_key
DEEPSEEK_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# 可选 - 通达信本地数据源（更快更稳定）
TDX_ENABLED=false
TDX_BASE_URL=http://192.168.1.222:8181

# 可选 - 通知
EMAIL_ENABLED=false
WEBHOOK_ENABLED=false
```

### 启动

```bash
# 方式一：一键启动（任意目录）
stock

# 方式二：手动启动
source venv/bin/activate
python run.py
```

访问 http://localhost:8503

## 📁 项目结构

```
aiagents-stock/
├── app.py                  # 主入口（Streamlit）
├── run.py                  # 启动脚本
├── config.py               # 全局配置
├── model_config.py         # AI模型列表
├── core/                   # 基础设施（API客户端、数据库、限流、路径）
├── data/                   # 数据采集（行情、资金流、情绪、新闻）
├── agents/                 # AI智能体（分析师团队）
├── modules/                # 功能模块
│   ├── monitor/            # 实时监测
│   ├── smart_monitor/      # AI盯盘
│   ├── longhubang/         # 智瞰龙虎
│   ├── main_force/         # 主力选股
│   ├── sector_strategy/    # 板块策略
│   └── portfolio/          # 持仓管理
├── services/               # 共享服务（PDF生成等）
├── scripts/                # 部署脚本
├── data_db/                # 数据库文件
└── docs/                   # 详细文档
```

## 📊 数据源

系统采用多层 fallback 架构，确保数据可用性：

| 数据类型 | 主数据源 | 备用 | API Key |
|----------|----------|------|---------|
| 股票行情 | AKShare（腾讯） | Tushare → 本地缓存 | 否 |
| 资金流向 | AKShare | 问财(Pywencai) | 否 |
| 财务数据 | 新浪财经 | Tushare | 否 |
| 市场情绪 | AKShare | 问财 | 否 |
| 龙虎榜 | StockAPI | — | 否（1000次/天） |
| 实时行情 | TDX（可选） | AKShare | 否 |

## 🐳 Docker 部署

```bash
docker-compose up -d
```

详见 [Docker部署文档](docs/DOCKER_DEPLOYMENT.md)

## 📚 文档索引

- [快速开始](docs/QUICK_START.md)
- [AI盯盘使用说明](docs/AI盯盘交易时段优化说明.md)
- [TDX数据源配置](docs/TDX数据源快速配置.md)
- [MiniQMT量化交易](docs/MINIQMT_INTEGRATION_GUIDE.md)
- [持仓分析指南](docs/PORTFOLIO_USAGE.md)
- [智瞰龙虎说明](docs/LONGHUBANG_BATCH_ANALYSIS.md)
- [更新日志](docs/UPDATE_LOG.md)

## 📜 免责声明

本系统仅供学习和研究使用，不构成投资建议。投资决策风险由用户自行承担。

## 📄 许可证

MIT License

---

欢迎提交 Issue 和 PR！联系邮箱：ws3101001@126.com

<img width="300" alt="微信群" src="https://www.sd-hn.cn/img/2wm1104.png" />
