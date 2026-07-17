# Cutting-Edge GEO — 2026 前沿技术

## 能力 1: ChatGPT Shopping 追踪

ChatGPT 已支持购物搜索，用户可直接在 ChatGPT 中发现和比较产品。

### 追踪维度

| 维度 | 说明 |
|------|------|
| 产品出现率 | 品牌产品在购物类 prompt 中被推荐的比例 |
| 产品排名 | 在推荐列表中的位置（第 1/2/3... 位） |
| 竞品对比 | 同类产品中品牌 vs 竞品的出现频率 |
| 价格感知 | AI 如何描述品牌的价格定位 |
| 购买链接 | AI 是否提供直达购买链接 |
| 产品属性覆盖 | AI 强调的产品属性 vs 品牌希望强调的属性 |

### 实现方式

```python
# 购物类 prompt 模板
SHOPPING_TEMPLATES = [
    "best {product_category} for {use_case}",
    "{product_category} comparison {brand_a} vs {brand_b}",
    "top {product_category} under {price_range}",
    "{product_category} recommendations for {persona}",
    "where to buy {product_category}",
]
```

---

## 能力 2: AI Prompt Discovery

从种子关键词自动发现用户在 AI 搜索中实际使用的 prompt。

### Prompt 发现流程

```
种子关键词: "project management tool"
         │
         ▼
┌─────────────────────────────────┐
│  AI Prompt 生成器               │
│  - 基于种子词扩展变体            │
│  - 模拟用户意图分布              │
│  - 按漏斗阶段分类               │
└────────────────┬────────────────┘
                 │
         ┌───────┼───────┐
         ▼       ▼       ▼
    awareness  consider  conversion
    prompts    prompts   prompts
```

### Prompt 质量评分

| 因素 | 权重 | 说明 |
|------|------|------|
| 搜索意图明确度 | 25% | prompt 是否有清晰的购买/比较/了解意图 |
| 品牌触发可能性 | 25% | 该 prompt 是否可能触发品牌提及 |
| 竞争激烈度 | 20% | 多少竞品在争夺该 prompt |
| 转化潜力 | 20% | 该 prompt 的用户是否接近购买 |
| 时效性 | 10% | 该 prompt 是否为趋势性话题 |

---

## 能力 3: AI Share of Voice (SOV)

品牌在 AI 搜索中的声音份额。

### SOV 计算模型

```
AI SOV = Σ(brand_mentions_in_prompt × prompt_weight) / Σ(all_mentions_in_prompt × prompt_weight)

其中 prompt_weight 基于:
- prompt 的商业价值（高意图 > 低意图）
- prompt 的搜索频率
- prompt 的竞争激烈度
```

### SOV 分层分析

| 层级 | 说明 | 示例 |
|------|------|------|
| Overall SOV | 所有 prompt 的综合份额 | 品牌在所有 AI 搜索中被提及的比例 |
| Category SOV | 品类级份额 | 在 "PM tools" 类 prompt 中的份额 |
| Intent SOV | 意图级份额 | 在购买意图 prompt 中的份额 |
| Competitor SOV | 竞品对比份额 | vs 竞品的相对份额变化 |
| Platform SOV | 平台级份额 | 在 ChatGPT vs Perplexity 中的份额差异 |

---

## 能力 4: Agentic Search 优化

搜索将集成 AI Agent 能力。用户可以在搜索中直接触发 Agent 执行任务（预订、购买、比较）。

### Agentic Search 特征

1. **任务型查询**: "帮我比较这三款 PM 工具的价格和功能"
2. **Agent 触发**: 搜索可直接调用 Agent 完成任务
3. **结构化数据依赖**: Agent 严重依赖 schema markup 来理解产品
4. **实时数据**: Agent 需要最新的价格、库存、评价数据

### 优化策略

| 策略 | 说明 |
|------|------|
| 结构化产品数据 | Product schema 必须包含 price, availability, reviews |
| API 可访问性 | 提供机器可读的产品 API（价格/库存/规格） |
| 实时数据更新 | 确保 schema 数据与实际同步 |
| Agent 友好格式 | 使用 JSON-LD 而非 microdata |
| 任务完成路径 | 确保从 AI 回答到购买的路径畅通 |

---

## 能力 5: AI Traffic Analytics

追踪哪些 AI 爬虫访问了你的站点、访问了哪些页面。

### AI 爬虫活跃度指标

| 指标 | 说明 |
|------|------|
| 爬取频率 | 每个 AI 爬虫每天/周的访问次数 |
| 爬取深度 | 平均每 session 访问的页面数 |
| 爬取覆盖率 | AI 爬虫访问的页面占总页面的比例 |
| 爬取优先级 | 哪些页面被最频繁爬取 |
| 爬取遗漏 | 重要页面未被爬取的情况 |

### 新增 AI 爬虫 UA（2026 年新发现）

| UA 字符串 | 来源 | 说明 |
|-----------|------|------|
| `ChatGPT-User` | OpenAI | ChatGPT 实时搜索代理 |
| `GPTBot` | OpenAI | GPT 训练数据爬虫 |
| `ClaudeBot` | Anthropic | Claude 数据爬虫 |
| `Claude-Web` | Anthropic | Claude 实时搜索 |
| `PerplexityBot` | Perplexity | Perplexity 索引爬虫 |
| `Perplexity-User` | Perplexity | Perplexity 实时代理 |
| `Google-Extended` | Google | Gemini/AI Overviews 训练 |
| `GoogleOther` | Google | Google 其他 AI 服务 |
| `anthropic-ai` | Anthropic | Anthropic 内部爬虫 |
| `Bytespider` | ByteDance | 字节跳动 AI 训练 |
| `YouBot` | You.com | You.com 索引爬虫 |
| `Diffbot` | Diffbot | 知识图谱数据 |
| `Omgilibot` | Omgili | AI 训练数据 |
| `Applebot-Extended` | Apple | Apple AI 服务 |

---

## 能力 6: Persona-Based Prompt Tracking

按用户画像追踪 prompt 表现。

### Persona 维度

| Persona | 特征 | Prompt 偏好 |
|---------|------|------------|
| Technical Buyer | 技术评估 | "API integration", "scalability", "security features" |
| Business Buyer | 商业决策 | "ROI", "pricing comparison", "enterprise plan" |
| End User | 最终用户 | "how to use", "tutorial", "best practice" |
| IT Admin | IT 管理 | "deployment", "SSO", "compliance" |
| Developer | 开发者 | "SDK", "API docs", "developer experience" |

---

## 输出格式

```json
{
  "schema_version": "1.0",
  "chatgpt_shopping": {
    "product_appearance_rate": 0.0,
    "avg_product_rank": 0,
    "competitor_comparison": {},
    "price_perception": "string",
    "attribute_coverage": {}
  },
  "prompt_discovery": {
    "discovered_prompts": [],
    "prompt_quality_scores": {},
    "coverage_by_intent": {}
  },
  "ai_sov": {
    "overall_sov": 0.0,
    "by_platform": {},
    "by_intent": {},
    "by_competitor": {},
    "trend": "growing|stable|declining"
  },
  "agentic_readiness": {
    "structured_data_score": 0,
    "api_accessibility": false,
    "real_time_data_freshness": "string",
    "task_completion_path_score": 0
  },
  "ai_traffic_analytics": {
    "total_crawls": 0,
    "crawl_by_bot": {},
    "crawl_coverage": 0.0,
    "uncrawled_important_pages": []
  },
  "persona_tracking": {}
}
```