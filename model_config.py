"""
模型配置文件
包含所有可用的AI模型选项

说明：当前 API 端点为阿里云百炼（DEEPSEEK_BASE_URL=dashscope compatible-mode），
百炼平台同时代理了 DeepSeek、智谱GLM、Kimi 等第三方模型。
以下模型均已通过当前 key 在百炼端点实测可用；模型名须使用百炼的命名规范。
"""

model_options = {
    # ===== 通义千问 =====
    "qwen-max": "通义千问 Max（最强）",
    "qwen-plus": "通义千问 Plus（默认推荐）",
    "qwen-plus-latest": "通义千问 Plus Latest",
    "qwen-flash": "通义千问 Flash（快速）",
    "qwen-turbo": "通义千问 Turbo（快速）",
    "qwen-long": "通义千问 Long（长文本）",
    "qwen3-235b-a22b": "通义千问3-235B",
    "qwen3-235b-a22b-thinking-2507": "通义千问3-235B Thinking（推理）",
    "qwen3-235b-a22b-instruct-2507": "通义千问3-235B Instruct",
    # ===== DeepSeek（百炼代理）=====
    "deepseek-v3": "DeepSeek-V3",
    "deepseek-v3.1": "DeepSeek-V3.1",
    "deepseek-v3.2": "DeepSeek-V3.2",
    "deepseek-r1": "DeepSeek-R1（推理增强）",
    "deepseek-r1-0528": "DeepSeek-R1-0528（推理增强）",
    # ===== 智谱 GLM（百炼代理）=====
    "glm-4.6": "智谱 GLM-4.6",
    # ===== Kimi（百炼代理）=====
    "Moonshot-Kimi-K2-Instruct": "Kimi K2",
}
