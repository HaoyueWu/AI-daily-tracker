# 🤖 AI Daily Tracker

极简、高信噪比的每日 AI 核心资讯聚合看板。

自动化抓取全球四大前沿信息源，由大语言模型深度分析、评分与摘要提炼，最终呈现为一页式现代数据面板。

---

## 🌟 核心特性

| 特性 | 说明 |
|:---|:---|
| 🌍 全球极客视野 | 聚合 Hacker News 热榜，捕捉硬核开发者社区的技术讨论与最新发现 |
| 🐙 热门开源动向 | 追踪 GitHub 当日 Star 增速最快的 AI 相关仓库 |
| 🤗 模型趋势先锋 | 实时抓取 Hugging Face Trending 榜单，掌握大模型流行风向 |
| 💡 国内商业落地 | 解析 36氪 RSS 订阅流，过滤国内 AI 产业化与创投前沿动态 |
| 🧠 LLM 智能漏斗 | 通义千问自动评分 (1~10)、生成标签与一句话中文摘要 |
| ⏳ 动态热度排序 | 综合内容价值与时间新鲜度，智能平衡重大突破与最新资讯的排列权重 |
| 👑 全网 Top 5 | 跨源汇总最具影响力的 5 条资讯，置顶高亮展示 |
| 📂 查看更多 | 折叠区域收纳主页未展示的剩余资讯，按模块分组，附带精简摘要 |

## 🛠️ 技术栈

| 层级 | 技术 |
|:---|:---|
| 前端 | [Streamlit](https://streamlit.io/)（双栏瀑布流 + 自适应深浅主题） |
| 数据 | Pandas DataFrame |
| 网络 | Requests + Python 内置 XML 解析 |
| AI | OpenAI 兼容 SDK → Qwen (可替换为任意 LLM) |

## 📁 项目结构

```
├── app.py              # Streamlit 前端主入口
├── data_fetcher.py     # 四大数据源抓取器
├── llm_pipeline.py     # LLM 评分 + 时间衰减算法
├── test_run.py         # 全链路自动化测试脚本
└── requirements.txt    # 依赖清单
```

## 🚀 快速开始

### 1. 环境搭建

```bash
# 创建并激活虚拟环境
python3 -m venv venv
source venv/bin/activate    # macOS / Linux

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置 API 密钥

| 文件 | 配置项 | 说明 |
|:---|:---|:---|
| `data_fetcher.py` | `Authorization: Bearer <Token>` | 替换为您的 GitHub Personal Access Token |
| `llm_pipeline.py` | `api_key` / `base_url` | 替换为您使用的 LLM 服务商密钥（默认为阿里通义千问） |

### 3. 启动

```bash
streamlit run app.py
```

浏览器访问 `http://localhost:8501`，点击侧边栏「🚀 一键获取今日 AI 资讯」即可。

## 🔌 更换 LLM

项目使用标准 `openai` SDK 发送请求，天然兼容所有 OpenAI 格式的 API 端点。只需修改 `llm_pipeline.py` 中的 `base_url` 和 `api_key`，即可无缝切换至 OpenAI / DeepSeek / Kimi / 本地 Ollama 等任意大模型服务。

## ⚠️ 常见问题

**Q: 抓取超时 / Connection Timeout？**
> 境外源（Hacker News、Hugging Face）默认 25 秒超时。如果网络波动较大，请确保代理工具正常运行。若使用全局 TUN 模式，国内源（36氪）可能被误拦截，建议切换为规则模式或直连。

**Q: 36氪数据为空？**
> 36氪 RSS 通过关键词过滤 AI 相关内容，若当日该站未发布相关文章则结果为空，属正常现象。
