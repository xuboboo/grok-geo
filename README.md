# grok-geo Skill

**AI 搜索 / GEO 品牌诊断 Agent Skill（v5.0.0）**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

---

## About

通用 GEO Agent Skill，支持 17+ AI 引擎的品牌可见度诊断。提供引用准确性验证、竞争对手对比和内容差距分析。

**Keywords**: `open-source` `ai` `seo` `geo` `generative-engine-optimization` `ai-search` `brand-monitoring` `citation-analysis` `agent-skill`

---

### Supported AI Engines

| 类别 | 引擎 |
|------|------|
| **国际** | OpenAI (ChatGPT)、Anthropic (Claude)、Google (Gemini)、Perplexity、Mistral、Cohere、xAI (Grok)、DeepSeek |
| **国内** | 豆包、通义千问、智谱 GLM、Kimi、文心一言、讯飞星火、腾讯混元、火山引擎 |

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
grok-geo/
├── skill/grok-geo/          # Agent Skill 本体
│   ├── SKILL.md             # Agent 工作流定义
│   ├── scripts/             # 计算脚本
│   ├── schemas/             # JSON Schema
│   ├── templates/           # 报告模板
│   ├── examples/            # 示例和演示
│   ├── evals/               # 评估测试
│   └── mcp/                 # MCP Server
├── tests/                   # 测试套件
├── ui/                      # Streamlit Web Dashboard
├── .github/workflows/       # CI/CD
├── Dockerfile               # Docker 部署
└── docker-compose.yml       # 容器编排
```

---

## 使用教程

### 场景一：快速体验（离线演示）

```bash
git clone https://github.com/your-username/grok-geo.git
cd grok-geo

# 使用预置数据运行，无需网络
python skill/grok-geo/examples/run_offline_demo.py --base-dir ./geo-audit-runs --keep

# 查看结果
# 报告位置：geo-audit-runs/geo_offline_demo_00000001/output/
```

**输出文件**：`report.md`（可读报告）、`report.json`（结构化数据）、`questions.csv`、`evidence.csv`、`opportunities.csv`、`manifest.json`

---

### 场景二：Agent 集成模式（推荐）

#### 步骤 1：安装 Skill

```bash
# Cursor 用户
cp -r skill/grok-geo/ ~/.cursor/skills/grok-geo/

# Claude Code 用户
cp -r skill/grok-geo/ ~/.claude/skills/grok-geo/
```

#### 步骤 2：触发 Skill

在 Agent 对话中描述需求：

```
请分析品牌 "小米" 在 AI 搜索中的表现
```

或提供详细配置：

```
我想对品牌 "小米" 进行 GEO 审计：
- 网站：www.mi.com
- 行业：消费电子
- 目标客户：年轻消费者
- 目标地区：中国
- 主要竞争对手：华为、苹果、OPPO
```

#### 步骤 3：查看结果

Agent 会自动执行完整流程并返回报告路径。

---

### 场景三：自定义品牌审计

#### 输入参数

| 参数 | 必填 | 说明 | 示例 |
|------|------|------|------|
| `brand_name` | Yes | 品牌名称 | "小米" |
| `website` | Yes | 官方网站 | "www.mi.com" |
| `industry` | Yes | 行业 | "消费电子" |
| `target_customer` | Yes | 目标客户 | "年轻消费者" |
| `target_region` | No | 目标地区 | "中国" |
| `competitors` | No | 竞争对手 | ["华为", "苹果"] |
| `brand_aliases` | No | 品牌别名 | ["Xiaomi", "Redmi"] |
| `products` | No | 主要产品 | ["手机", "智能家居"] |

#### 运行模式

| 模式 | 问题数 | 适用场景 |
|------|--------|----------|
| `quick` | 10 | 快速概览 |
| `standard` | 30 | 完整诊断 |
| `offline_import` | - | 分析已有数据 |

---

### 场景四：持续监控

```bash
# 添加定期审计任务
python skill/grok-geo/scripts/scheduler.py --add "brand-weekly" \
  --brand-config ./input.json \
  --cron "0 2 * * 1"

# 查看已配置任务
python skill/grok-geo/scripts/scheduler.py --list

# 手动触发
python skill/grok-geo/scripts/scheduler.py --run "brand-weekly"
```

---

### 输出结果解读

#### 品牌可见度评分 (GEO Score)

- **80-100 分**：优秀
- **60-79 分**：良好，有改进空间
- **40-59 分**：一般，需要优化
- **0-39 分**：较差，需要重点关注

#### 优化机会优先级

- **P0（紧急）**：立即处理，影响品牌声誉
- **P1（高）**：优先处理，影响用户获取
- **P2（中）**：计划处理，提升竞争力
- **P3（低）**：可选处理

---

## 测试

```bash
# 运行所有测试
python -m unittest discover -s tests -p "test_*.py" -v

# 或使用 Makefile
make test
```

## 打包发布

```bash
python scripts/package_skill.py
# 或
make package
```

---

## 安全约束

- 确定性计算脚本不发起网络请求，实时搜索由 Agent 的 `web_search` 工具完成
- 禁止伪造引用
- 禁止读取 run 外路径
- API Key 在日志中自动脱敏

## 许可证

本项目采用 **[MIT 许可证](LICENSE)**。

**grok-geo** - 让品牌在 AI 搜索时代脱颖而出