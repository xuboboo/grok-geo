# grok-geo Skill

**AI 搜索 / GEO 品牌诊断 Agent Skill（v5.0.0）**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Open Source](https://img.shields.io/badge/Open%20Source-❤️-red.svg)](https://opensource.org/)

---

## About

> Universal GEO skill for AI agents. 17 AI engine adapters + 60+ deterministic metrics + 92 compliance rules covering brand visibility, AI citations, competitor benchmarking, sentiment analysis, entity KG scoring, content freshness, trust stack, and predictive GEO. Supports offline mode, scheduled audits, real-time monitoring with Email/Slack/WeChat/DingTalk alerts, PDF export, and Docker deployment.

**Keywords**: `open-source` `ai` `seo` `geo` `generative-engine-optimization` `ai-search` `brand-monitoring` `citation-analysis` `agent-skill`

---

### Features

| Category | Capabilities |
|----------|-------------|
| **AI Engines (国际)** | OpenAI (ChatGPT)、Anthropic (Claude)、Google (Gemini)、Perplexity、Mistral、Cohere、xAI (Grok)、DeepSeek |
| **AI Engines (国内)** | 豆包 (Doubao)、通义千问 (Qwen)、智谱 GLM (Zhipu)、Kimi (Moonshot)、文心一言 (Wenxin)、讯飞星火 (Spark)、腾讯混元 (Hunyuan)、火山引擎 (Volcengine) |
| **Metrics** | 60+ metrics: GEO Score, Sentiment, Citability, Trust Stack, Entity KG, i18n, Predictive |
| **Compliance** | GEO Lint (92 rules), Schema Validation, Entity Resolution |
| **Monitoring** | Real-time alerts (Email/Slack/WeChat/DingTalk), 30-day trend history |
| **Export** | JSON, PDF, CSV reports |
| **Deployment** | CLI, Streamlit Web UI, Docker |
| **Testing** | 212 unit/integration/boundary tests |

### Quick Start

```bash
# Install
pip install -r requirements.txt

# Run offline demo
python skill/geo-brand-audit/examples/run_offline_demo.py --base-dir ./geo-audit-runs --keep

# Launch Web UI
streamlit run ui/app.py

# Docker deployment
docker-compose up -d
```

### Project Structure

```
skill/
├── skill/geo-brand-audit/       # Core skill (SKILL.md + scripts + schemas)
├── tests/                       # 212 tests (unit/boundary/performance)
├── ui/                          # Streamlit Web Dashboard
├── .github/workflows/           # CI/CD (GitHub Actions)
├── Dockerfile                   # Docker deployment
└── docker-compose.yml           # Container orchestration
```

### Documentation

- [SKILL.md](skill/geo-brand-audit/SKILL.md) - Agent workflow (11 phases)
- [METRICS.md](skill/geo-brand-audit/METRICS.md) - 60+ metric definitions
- [CHANGELOG.md](skill/geo-brand-audit/CHANGELOG.md) - Version history
- [references/](skill/geo-brand-audit/references/) - 25 methodology docs

---

> 🌟 **这是一个完全开源的项目**，采用 MIT 许可证，欢迎任何人使用、修改和分发。
> 支持 17+ 主流 AI 引擎的品牌可见度诊断，覆盖 ChatGPT、豆包、DeepSeek、通义千问、智谱 GLM、Kimi、文心一言、Claude、Gemini、Perplexity 等，提供引用准确性验证、竞争对手表现分析和内容差距诊断的完整解决方案。

## 核心功能

- **品牌可见度分析**：评估品牌在 AI 搜索结果中的出现频率和位置
- **引用准确性验证**：检查 AI 搜索结果中品牌信息的准确性
- **竞争对手对比**：分析品牌与竞争对手在 AI 搜索中的表现差异
- **内容差距识别**：发现品牌在 AI 搜索优化中的内容缺失
- **可操作建议**：提供基于证据的优化建议和内容策略

## 项目结构

```
grok-geo/
├── skill/grok-geo/          # Agent Skill 本体（发布 ZIP 内容）
│   ├── SKILL.md             # Agent 工作流定义（11 阶段）
│   ├── scripts/             # 确定性计算脚本（50+ Python 脚本）
│   ├── schemas/             # JSON Schema 数据契约
│   ├── templates/           # 报告模板
│   ├── examples/            # 输入示例和演示脚本
│   ├── evals/               # 评估测试用例
│   ├── mcp/                 # MCP Server（JSON-RPC stdio）
│   └── references/          # 参考文档和方法论
├── tests/                   # 测试套件
│   ├── unit/                # 单元测试
│   ├── integration/         # 集成测试
│   ├── boundary/            # 边界测试
│   └── performance/         # 性能测试
├── devtools/                # 开发辅助工具（不包含在发布 ZIP 中）
├── scripts/                 # 项目级脚本
├── dist/                    # 构建产物
└── geo-audit-runs/          # 运行时输出目录
```

## 📖 使用教程

### 场景一：快速体验（离线演示）

**适合**：想快速了解项目功能，无需配置 Agent 环境

```bash
# 1. 克隆项目
git clone https://github.com/your-username/grok-geo.git
cd grok-geo

# 2. 运行离线演示（使用预置数据，无需网络）
python skill/grok-geo/examples/run_offline_demo.py --base-dir ./geo-audit-runs --keep

# 3. 查看结果
# 报告位置：geo-audit-runs/geo_offline_demo_00000001/output/
```

**输出文件说明**：
- `report.md` - 可读的 Markdown 报告，包含品牌诊断结果
- `report.json` - 结构化 JSON 数据，便于程序处理
- `questions.csv` - 生成的诊断问题列表
- `evidence.csv` - 收集的证据和引用
- `opportunities.csv` - 优化机会和建议
- `manifest.json` - 运行元数据和配置信息

---

### 场景二：Agent 集成模式（推荐）

**适合**：在 Cursor、Claude Code 等 AI Agent 环境中使用

#### 步骤 1：安装 Skill

将 `skill/grok-geo/` 目录复制到你的 Agent Skills 目录：

```bash
# Cursor 用户
cp -r skill/grok-geo/ ~/.cursor/skills/grok-geo/

# Claude Code 用户
cp -r skill/grok-geo/ ~/.claude/skills/grok-geo/
```

#### 步骤 2：触发 Skill

在 Agent 对话中，直接描述你的需求：

```
请分析品牌 "小米" 在 AI 搜索中的表现
```

或者提供更详细的信息：

```
我想对品牌 "小米" 进行 GEO 审计：
- 网站：www.mi.com
- 行业：消费电子
- 目标客户：年轻消费者
- 目标地区：中国
- 主要竞争对手：华为、苹果、OPPO
```

#### 步骤 3：Agent 交互流程

Agent 会自动执行以下流程：

1. **收集信息**：确认品牌名称、网站、行业等基本信息
2. **品牌调研**：通过 web_search 收集品牌信息
3. **生成问题**：创建 10-30 个诊断问题
4. **执行搜索**：批量搜索并收集证据
5. **分析数据**：计算 60+ 指标
6. **生成报告**：输出完整的诊断报告

#### 步骤 4：查看结果

Agent 会返回报告路径，你可以直接查看或下载：

```
报告已生成：
- 完整报告：geo-audit-runs/run_20260718_001/output/report.md
- 数据文件：geo-audit-runs/run_20260718_001/output/report.json
- 优化建议：geo-audit-runs/run_20260718_001/output/opportunities.csv
```

---

### 场景三：自定义品牌审计

**适合**：需要审计特定品牌，提供详细配置

#### 输入参数说明

| 参数 | 必填 | 说明 | 示例 |
|------|------|------|------|
| `brand_name` | ✅ | 品牌或公司名称 | "小米" |
| `website` | ✅ | 官方网站 URL | "www.mi.com" |
| `industry` | ✅ | 行业或产品类别 | "消费电子" |
| `target_customer` | ✅ | 目标客户群体 | "年轻消费者" |
| `target_region` | ❌ | 目标地区 | "中国"、"全球" |
| `competitors` | ❌ | 竞争对手列表 | ["华为", "苹果"] |
| `brand_aliases` | ❌ | 品牌别名 | ["Xiaomi", "Redmi"] |
| `products` | ❌ | 主要产品 | ["手机", "智能家居"] |
| `known_facts` | ❌ | 已知事实 | {"founded": "2010"} |
| `forbidden_claims` | ❌ | 禁止的声明 | ["市场第一"] |

#### 运行模式

| 模式 | 问题数 | 搜索深度 | 适用场景 |
|------|--------|----------|----------|
| `quick` | 10 | 1 次/问题 | 快速概览，60 秒完成 |
| `standard` | 30 | 2 次/问题 | 完整诊断，5-10 分钟 |
| `offline_import` | - | 使用已有数据 | 分析已有的搜索结果 |

#### 示例：创建自定义审计

```python
# 创建输入配置文件
import json

brand_config = {
    "brand_name": "小米",
    "website": "www.mi.com",
    "industry": "消费电子",
    "target_customer": "年轻消费者",
    "target_region": "中国",
    "competitors": ["华为", "苹果", "OPPO", "vivo"],
    "brand_aliases": ["Xiaomi", "Redmi", "POCO"],
    "products": ["手机", "笔记本电脑", "智能家居", "电视"],
    "mode": "standard"
}

# 保存配置
with open("input.json", "w", encoding="utf-8") as f:
    json.dump(brand_config, f, ensure_ascii=False, indent=2)

# 运行审计（在 Agent 环境中）
# Agent 会自动读取 input.json 并执行完整流程
```

---

### 场景四：持续监控

**适合**：需要定期监控品牌在 AI 搜索中的表现

#### 设置定期审计

```bash
# 添加每周一凌晨 2 点的审计任务
python skill/grok-geo/scripts/scheduler.py --add "brand-weekly" \
  --brand-config ./input.json \
  --cron "0 2 * * 1"

# 查看已配置的任务
python skill/grok-geo/scripts/scheduler.py --list

# 手动触发一次审计
python skill/grok-geo/scripts/scheduler.py --run "brand-weekly"
```

#### 漂移检测

```bash
# 比较当前运行与基线
python skill/grok-geo/scripts/detect_drift.py \
  --baseline ./geo-audit-runs/run_baseline \
  --current ./geo-audit-runs/run_current

# 检查可见度告警
python skill/grok-geo/scripts/detect_visibility_alerts.py \
  --baseline ./geo-audit-runs/run_baseline \
  --current ./geo-audit-runs/run_current
```

#### 告警规则

| 指标 | 阈值 | 级别 |
|------|------|------|
| `geo_score` | < 40 | 🔴 严重 |
| `geo_score` | < 60 | 🟡 警告 |
| `mention_rate` | < 30% | 🔴 严重 |
| `recommendation_rate` | < 20% | 🟡 警告 |
| `sentiment_index` | < 20 | 🔴 严重 |

---

### 场景五：批量审计

**适合**：需要审计多个品牌或产品线

```bash
# 创建批量审计脚本
cat > batch_audit.sh << 'EOF'
#!/bin/bash

brands=("小米" "华为" "苹果" "OPPO")

for brand in "${brands[@]}"; do
  echo "审计品牌: $brand"
  # 在 Agent 环境中执行
  # Agent 会为每个品牌创建独立的审计运行
done
EOF

chmod +x batch_audit.sh
./batch_audit.sh
```

---

### 输出结果解读

#### 1. 品牌可见度评分 (GEO Score)

- **80-100 分**：优秀 - 品牌在 AI 搜索中表现突出
- **60-79 分**：良好 - 有改进空间
- **40-59 分**：一般 - 需要优化
- **0-39 分**：较差 - 需要重点关注

#### 2. 关键指标说明

| 指标 | 含义 | 优化方向 |
|------|------|----------|
| `mention_rate` | 品牌被提及的频率 | 增加品牌曝光 |
| `recommendation_rate` | 被推荐的频率 | 提升产品质量和服务 |
| `sentiment_index` | 情感倾向评分 | 改善用户体验 |
| `citation_accuracy` | 引用准确性 | 确保信息一致性 |
| `competitor_gap` | 与竞争对手的差距 | 差异化竞争策略 |

#### 3. 优化机会优先级

- **P0（紧急）**：立即处理，影响品牌声誉
- **P1（高）**：优先处理，影响用户获取
- **P2（中）**：计划处理，提升竞争力
- **P3（低）**：可选处理，锦上添花

---

### 常见问题

**Q: 离线演示和 Agent 模式有什么区别？**
A: 离线演示使用预置数据，无需网络，适合快速体验。Agent 模式会实时搜索，获取最新数据，适合实际使用。

**Q: 如何查看历史审计结果？**
A: 所有审计结果都保存在 `geo-audit-runs/` 目录下，按运行时间戳命名。

**Q: 可以自定义报告模板吗？**
A: 可以，修改 `skill/grok-geo/templates/` 目录下的模板文件。

**Q: 如何处理搜索失败的问题？**
A: 系统会自动重试失败的搜索，如果成功率低于 80%，会标记为部分完成。

**Q: 数据安全如何保障？**
A: 所有数据本地存储，脚本不发起网络请求，搜索由 Agent 的 web_search 工具完成。

## 开发指南

### 测试

```bash
# 运行所有测试
python -m unittest discover -s tests -p "test_*.py" -v

# 或使用 Makefile
make test

# 使用 pytest（如果已安装）
pytest tests/
```

### 评估

```bash
# 运行评估测试
python skill/grok-geo/evals/run_evals.py

# 或使用 Makefile
make eval
```

### 打包发布

```bash
# 打包为 ZIP 文件
python scripts/package_skill.py

# 或使用 Makefile
make package
```

产物位置：
- `dist/grok-geo-v1.0.0.zip`
- `dist/grok-geo-v1.0.0.zip.sha256`

### 完整发布流程

```bash
# 运行测试、评估并打包
make release
```

## 配置说明

### 运行目录

- **Hosted 环境**：`/mnt/data/geo-audit-runs`（默认）
- **本地环境**：通过环境变量 `GEO_AUDIT_RUNS_DIR` 配置，默认 `./geo-audit-runs`

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `GEO_AUDIT_RUNS_DIR` | 运行输出目录 | `./geo-audit-runs` |
| `PYTHON` | Python 解释器路径 | `python` |

## 架构设计

### 核心原则

1. **确定性计算**：所有指标计算均由 Python 脚本完成，禁止手动计算
2. **证据驱动**：所有结论必须有可追溯的证据支持
3. **渐进式披露**：SKILL.md 保持简洁，详细信息按需加载
4. **安全第一**：脚本不发起网络请求，禁止伪造引用

### 指标分级

- **T1 Core**：纯算法指标，无外部依赖
- **T2 Extended**：需要丰富数据源的指标
- **T3 Experimental**：启发式指标，需要警告标识

### MCP Server

项目提供 MCP（Model Context Protocol）Server，支持 7 个工具：

- `run_audit`：执行完整审计
- `get_status`：获取运行状态
- `get_report`：获取报告
- `get_metrics`：获取指标数据
- `schedule_audit`：调度审计任务
- `list_runs`：列出历史运行
- `delete_run`：删除运行记录

## 安全约束

- **确定性计算脚本**（`scripts/` 下除 `multi_engine_query.py`、`api_adapters.py`、`alert_channels.py` 外）**不发起任何网络请求**，实时搜索由 Agent 的 `web_search` 工具完成
- **AI 引擎查询**（`multi_engine_query.py`、`api_adapters.py`）通过 `urllib.request` / `httpx` 调用官方 API，所有 API Key 从环境变量读取，禁止硬编码
- **告警通知**（`alert_channels.py`）通过 webhook 发送告警，URL 从环境变量读取
- **禁止伪造引用**：所有数据必须来自真实搜索结果
- **禁止执行用户 shell**：脚本仅执行预定义操作（`subprocess.run` 不使用 `shell=True`）
- **禁止读取 run 外路径**：`path_utils.resolve_under()` 严格限制文件访问范围，防止路径遍历
- **API Key 保护**：配置文件中的密钥在日志和序列化输出中自动脱敏（`config.to_dict()`）

## 🤝 贡献指南

**欢迎贡献！** 这是一个开源项目，我们欢迎任何形式的贡献：

- 🐛 **报告问题**：发现 bug 或有改进建议？[创建 Issue](https://github.com/your-username/grok-geo/issues)
- 💡 **功能建议**：有新想法？[开始讨论](https://github.com/your-username/grok-geo/discussions)
- 🔧 **代码贡献**：修复 bug 或添加新功能
- 📚 **文档改进**：完善文档、添加示例
- 🧪 **测试用例**：添加测试覆盖或边界情况

### 快速贡献流程

```bash
# 1. Fork 项目到你的 GitHub
# 2. 克隆你的 Fork
git clone https://github.com/your-username/grok-geo.git
cd grok-geo

# 3. 创建特性分支
git checkout -b feature/amazing-feature

# 4. 进行修改并添加测试
# 5. 提交更改
git commit -m 'feat: add amazing feature'

# 6. 推送到你的 Fork
git push origin feature/amazing-feature

# 7. 创建 Pull Request
```

### 开发规范

- 遵循 PEP 8 代码风格
- 为新功能添加测试
- 更新相关文档
- 确保所有测试通过
- 编写清晰的提交信息（使用 [Conventional Commits](https://www.conventionalcommits.org/)）

### 社区准则

本项目遵循 [Contributor Covenant 行为准则](CODE_OF_CONDUCT.md)。我们致力于为每个人提供友好、安全和包容的环境。

## 📄 许可证

本项目采用 **[MIT 许可证](LICENSE)** - 这是最宽松的开源许可证之一。

**这意味着你可以：**
- ✅ 商业使用
- ✅ 修改代码
- ✅ 分发代码
- ✅ 私人使用
- ✅ 子许可证

**唯一要求：** 在副本中包含原始许可证和版权声明。

**完全免费** - 无需支付任何费用，无需联系作者获取许可。

## 版本历史

- **v5.0.0**：架构重构 + 指标分级 + MCP Server
- **v4.0.0**：Agentic 品牌库
- **v3.0.0**：前沿技术集成
- **v2.0.0**：多搜索引擎支持
- **v1.0.0**：核心功能发布

## 相关资源

- [设计文档](skill/grok-geo/references/methodology/)：评分模型和框架
- [API 规范](skill/grok-geo/schemas/)：JSON Schema 定义
- [评估报告](dist/eval-report-v1.0.0.json)：性能基准测试

## 🌍 社区与支持

**加入开源社区！** 我们欢迎每个人参与：

- **💬 GitHub Discussions**：[加入讨论](https://github.com/your-username/grok-geo/discussions) - 提问、分享想法、展示用例
- **🐛 问题报告**：[GitHub Issues](https://github.com/your-username/grok-geo/issues) - 报告 bug 或请求功能
- **📧 安全漏洞**：请通过 [SECURITY.md](SECURITY.md) 私密报告
- **⭐ Star 项目**：如果这个项目对你有帮助，请给我们一个 Star！

### 参与方式

- **使用者**：使用项目并提供反馈
- **贡献者**：提交代码、文档或测试
- **推广者**：分享项目、撰写教程
- **维护者**：帮助审查 PR 和解决问题

**所有贡献者都会被列入[贡献者列表](https://github.com/your-username/grok-geo/graphs/contributors)！**

---

**grok-geo** - 让品牌在 AI 搜索时代脱颖而出

**🌟 开源、免费、社区驱动 - 欢迎加入我们！**
