# CS2 Trading Agents — Project Scaffold

这是基于 NLUDL 期中提案的一个项目脚手架，目标是为《CS2 Trading Agents》实现一个模块化、可扩展的代码框架。

目录结构（摘要）:

- `cs2_trading/` — 主要包
  - `data/` — 价格 API 客户端与新闻爬虫
  - `agents/` — 各类 agent（LLM agent、ensemble 等）
  - `llm/` — LLM 接口抽象
  - `backtest/` — 回测引擎与指标计算
  - `portfolio/` — 投资组合与仓位管理
  - `config/` — 配置与常量
  - `utils/` — 日志等工具
- `main.py` — 简单 CLI 入口（演示）
- `requirements.txt` — 最小依赖
- `tests/` — 基本单元测试

目的：提供一个模块化起点，便于后续实现：价格抓取、新闻爬取、LLM 评分/对话、回测与多模型协同。

如何开始（示例）

1. 创建虚拟环境并安装依赖：

   ```powershell
   python -m venv .venv ; .\.venv\Scripts\Activate.ps1 ; python -m pip install -r requirements.txt
   ```

2. 运行示例回测（目前为骨架）：

   ```powershell
   python main.py --demo
   ```

3. 运行测试：

   ```powershell
   pytest -q
   ```

接下来的建议工作：实现真实的价格 API client、news 爬虫、将 LLM 接口绑定到选定的模型（如 OpenAI）、并实现交易策略和回测比较。

作者: 姚一凡 (2400010836)
