# AI 感知快照

## 目标

回答一个关键问题：**AI 引擎"认为"你的品牌是什么？** —— 捕捉 AI 搜索回答中对品牌的定位、价格感知、核心主张和情感倾向。

## 分析维度

### 1. 品牌定位（Brand Positioning）

AI 回答中对品牌的定位描述：

| 定位类型 | 示例 |
|----------|------|
| 市场领导者 | "行业领先的..."、"最受欢迎的..." |
| 挑战者 | "新兴的..."、"快速增长的..." |
| 细分专家 | "专为 XX 设计的..."、"适合 XX 场景..." |
| 性价比选择 | "预算友好的..."、"最具性价比的..." |
| 高端选择 | "企业级..."、"高端定制..." |
| 创新者 | "前沿技术..."、"AI 驱动的..." |

### 2. 价格感知（Price Perception）

AI 回答中对品牌价格的描述：

| 感知类型 | 信号词 |
|----------|--------|
| 免费/开源 | "免费"、"开源"、"free" |
| 低价 | "便宜"、"affordable"、"budget" |
| 中等 | "合理定价"、"competitive pricing" |
| 高价 | "昂贵"、"premium"、"enterprise pricing" |
| 不透明 | "需联系销售"、"custom pricing" |
| 未提及 | 无价格相关信息 |

### 3. 核心主张（Key Claims）

AI 回答中反复出现的品牌特征描述（去重后取 Top 5）：

```json
{
  "claim": "支持私有化部署",
  "frequency": 4,
  "platforms": ["chatgpt", "perplexity"],
  "sentiment": "positive",
  "verifiable": true
}
```

### 4. 情感基调（Sentiment Profile）

跨所有回答的品牌情感分布：

```json
{
  "positive_mentions": 12,
  "neutral_mentions": 5,
  "negative_mentions": 1,
  "overall_sentiment": 0.82,
  "sentiment_band": "favorable"
}
```

### 5. 竞品关联模式（Competitor Association）

品牌最常与哪些竞品一起出现，以及出现的上下文：

```json
{
  "top_co_mentions": [
    {
      "competitor": "竞争品牌A",
      "co_mention_count": 8,
      "context": "comparison",
      "brand_framing": "alternative_to"
    },
    {
      "competitor": "竞争品牌B",
      "co_mention_count": 5,
      "context": "recommendation",
      "brand_framing": "recommended_over"
    }
  ]
}
```

## 综合感知评分（0-100）

```text
perception_score = positioning_clarity × 0.25
                 + price_transparency × 0.15
                 + claim_consistency × 0.20
                 + sentiment_strength × 0.25
                 + competitor_framing × 0.15
```

| 维度 | 0 分 | 100 分 |
|------|------|--------|
| positioning_clarity | 无定位或定位混乱 | 清晰一致的市场定位 |
| price_transparency | 无价格信息 | 定价清晰透明 |
| claim_consistency | 主张矛盾或不一致 | 核心主张高度一致 |
| sentiment_strength | 强烈负面 | 强烈正面 |
| competitor_framing | 被竞品压制 | 被推荐优于竞品 |

## 输出结构

```json
{
  "perception_score": 71,
  "band": "favorable",
  "positioning": {
    "type": "specialist",
    "description": "AI 定位为'专为中小团队设计的项目管理工具'",
    "confidence": 0.85
  },
  "price_perception": {
    "type": "moderate",
    "evidence": "多次提到'合理定价'和'有免费版'",
    "consistency": 0.90
  },
  "key_claims": [
    {"claim": "支持私有化部署", "frequency": 4, "sentiment": "positive"},
    {"claim": "适合 50 人以下团队", "frequency": 3, "sentiment": "neutral"},
    {"claim": "API 文档完善", "frequency": 2, "sentiment": "positive"}
  ],
  "sentiment_profile": {
    "positive": 12,
    "neutral": 5,
    "negative": 1,
    "overall": 0.82,
    "band": "favorable"
  },
  "competitor_associations": [
    {"competitor": "竞品A", "count": 8, "context": "comparison", "framing": "alternative_to"},
    {"competitor": "竞品B", "count": 5, "context": "recommendation", "framing": "recommended_over"}
  ],
  "misperceptions": [
    {"claim": "不支持移动端", "verdict": "incorrect", "evidence": "官网明确支持 iOS/Android"},
    {"claim": "仅限中国大陆", "verdict": "partially_correct", "evidence": "已支持东南亚市场"}
  ],
  "recommendations": [
    "强化'私有化部署'主张的内容覆盖",
    "在定价页面增加透明的价格对比表",
    "针对'不支持移动端'的错误认知创建澄清内容"
  ]
}
```

## 评分等级

| 等级 | 分数段 | 含义 |
|------|--------|------|
| **Excellent** | 86-100 | AI 对品牌认知清晰、积极、准确 |
| **Favorable** | 68-85 | 整体正面，部分可优化 |
| **Mixed** | 36-67 | 认知模糊或存在矛盾 |
| **Negative** | 0-35 | AI 对品牌认知负面或严重错误 |

## Agent 使用指南

1. 在 Phase 5（Entity & Citation Analysis）阶段执行
2. 从搜索结果的回答文本中提取品牌定位、价格感知、核心主张
3. 与 `known_facts` 对比检测 misperceptions
4. 结果写入 `report.json` → `ai_perception`
5. misperceptions 自动纳入机会生成的高优先级输入