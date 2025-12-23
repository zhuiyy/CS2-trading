# CS2 Sticker Trading Agent (Budapest Major Simulation)

本项目旨在利用大语言模型（LLM）——特别是 **Gemini 3 Flash Preview/Gemini 3 Pro Preview** —— 来分析 CS2（反恐精英2）饰品市场的相关新闻，并基于情感分析进行自动化交易决策。

项目模拟了 2025 年布达佩斯 Major 期间的市场波动，测试 AI 是否能通过解读新闻（如战队表现、选手言论、市场情绪）来预测贴纸价格走势并实现盈利。

## 🛠 技术栈 (Tech Stack)

*   **核心语言**: Python 3.10+
*   **大语言模型 (LLM)**: 
    *   **Model**: Google Gemini 3 Flash Preview/Gemini 3 Pro Preview
    *   **SDK**: `google-genai` (New SDK supporting v1beta/v2)
    *   **Features**: 启用了 `thinking_config` (Thinking Level: Medium) 以增强模型的推理和逻辑分析能力。
*   **数据分析与可视化**: 
    *   Pandas (数据处理)
    *   Matplotlib & Seaborn (盈亏曲线、归因分析图表)
*   **开发环境**: VS Code, Jupyter Notebook

## 📂 项目结构 (Project Structure)

```text
cs2_trading/
├── agents/                 # 智能体模块
│   ├── ArtificialNewsAgent.py  # 新闻代理：负责读取/生成模拟的赛事新闻
│   ├── FinancialAgent.py       # 金融代理：负责宏观市场情绪分析
│   ├── market.py               # 交易代理：负责具体的买卖决策 (Trader) 和评分 (Scorer)
├── llm/
│   └── wrapper.py          # LLM 包装器：封装 google-genai SDK，处理重试逻辑 (429 Backoff) 和 Thinking Config
├── data/
│   ├── api.py              # 模拟交易所 API：提供历史价格数据
│   └── inventory.py        # 库存管理系统：追踪持仓、成本和市值
├── strategy.py             # 策略核心：定义 DailyStrategy，串联新闻、分析与交易执行
├── res/                    # 资源文件（新闻语料、初始库存等）
backtest_budapest_major.ipynb   # [主程序] 回测运行脚本
analysis_backtest.ipynb         # [分析工具] 结果可视化与复盘分析
backtest.log                    # 详细的交易日志
```

## 🧠 方法论 (Methodology)

本策略采用 **"News-Driven Sentiment Trading" (新闻驱动的情绪交易)** 方法：

1.  **每日循环 (Daily Cycle)**: 模拟器按天推进，每天早上读取当天的赛事新闻。
2.  **情绪分析 (Sentiment Analysis)**: 
    *   LLM 阅读新闻，分析其对特定战队（如 FaZe, NAVI）或选手（如 ZywOo, NiKo）贴纸价格的潜在影响。
    *   输出 0-10 的评分（Scoring）。
3.  **决策制定 (Decision Making)**:
    *   结合当前评分、持仓成本和市场热度，LLM 生成具体的交易指令（Buy/Sell/Hold）。
    *   引入了 `FinancialAgent` 进行宏观风险提示（如“市场过热，建议减仓”）。
4.  **执行与记录 (Execution)**: 更新虚拟账户的资金和库存，并记录详细日志。

## 📊 实验结果与分析 (Results)

我们在 **2025年布达佩斯 Major (模拟)** 期间进行了回测。

*   **总体表现**: 策略在模拟期间面临挑战，主要受制于高价资产（如 NiKo 贴纸）的剧烈波动。
*   **关键发现 (Key Insights)**:
    *   **选品 vs. 仓位 (Selection vs. Sizing)**: 通过 `analysis_backtest.ipynb` 中的 **等权重反事实分析 (Counterfactual Analysis)** 发现，AI 的选品眼光（即挑选潜力资产的能力）实际上优于其最终的账户表现。
    *   **归因分析**: 亏损的主要原因在于**仓位管理不当**——即在单价高且表现不佳的资产上投入了过多资金，掩盖了其他低价潜力资产（如杂牌战队贴纸）的涨幅。
    *   **模型能力**: Gemini 3 Flash Preview 在开启 `thinking_level="medium"` 后，能够给出非常详尽且符合逻辑的市场分析，但在具体的“止损”操作上仍显犹豫。

## 🚀 如何运行 (How to Run)

1.  **安装依赖**:
    ```bash
    pip install -r requirements.txt
    ```
2.  **配置环境**:
    在 `.env` 文件中设置 `GEMINI_API_KEY`。
3.  **运行回测**:
    打开并运行 `backtest_budapest_major.ipynb`。支持断点续传（Checkpoint）。
4.  **查看分析**:
    运行 `analysis_backtest.ipynb`，生成盈亏曲线、Drawdown 图表及等权重对比分析图。

