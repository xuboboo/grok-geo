# 内容保鲜指数 & RAG 分块就绪度

---

## 一、内容保鲜指数（Freshness Score）

### 目标

检测品牌内容是否存在**时间性腐烂**（temporal decay）——AI 引擎优先引用最新、最准确的内容。过期内容不仅不会被引用，还可能被标记为不可靠来源。

### 腐烂模式检测

| 模式 | 信号 | 示例 | 风险 |
|------|------|------|------|
| **时间腐烂** (temporal) | 文章日期 > 12 个月 | "发布于 2024-01" | AI 可能跳过过期内容 |
| **统计腐烂** (statistical) | 引用的数字明显过时 | "2023 年市场份额..." | 数据可信度下降 |
| **版本腐烂** (version) | 提及的产品版本已非最新 | "v2.0 新功能"（当前 v4.5） | 信息错位 |
| **事件腐烂** (event) | 引用已结束的事件 | "2024 年大会预告" | 信息无效 |
| **价格腐烂** (price) | 价格与当前不符 | "每月 $9"（当前 $19） | 严重误导 |

### 评分模型（0-100，越高越保鲜）

```text
freshness_score = 100
  - 时间腐烂扣分 (0-30)
  - 统计腐烂扣分 (0-25)
  - 版本腐烂扣分 (0-20)
  - 事件腐烂扣分 (0-15)
  - 价格腐烂扣分 (0-10)
```

### 输出结构

```json
{
  "freshness_score": 72,
  "evergreen_score": 85,
  "decay_signals": [
    {
      "pattern": "temporal",
      "severity": "medium",
      "evidence": "文章日期 2024-03-15，距今 16 个月",
      "deduction": 15
    },
    {
      "pattern": "statistical",
      "severity": "low",
      "evidence": "引用 '2024 年数据'，可能需更新",
      "deduction": 5
    }
  ],
  "recommendations": [
    "更新文章日期和 '最后更新' 标记",
    "将 2024 年统计数据替换为最新版本",
    "添加 '本文持续更新' 信号"
  ]
}
```

### 评分等级

| 等级 | 分数段 | 含义 |
|------|--------|------|
| **Fresh** | 86-100 | 内容高度保鲜，AI 优先引用 |
| **Aging** | 68-85 | 部分信号需关注 |
| **Stale** | 36-67 | 存在明显过期内容 |
| **Rotting** | 0-35 | 严重过期，可能被 AI 视为不可靠 |

---

## 二、RAG 分块就绪度（RAG Chunk Readiness）

### 目标

评估品牌内容是否适合被 RAG（Retrieval-Augmented Generation）系统分块检索和引用。AI 搜索引擎的底层往往使用 RAG 架构，内容的"分块友好度"直接影响被引用概率。

### 检查维度

| 维度 | 权重 | 检查项 |
|------|------|--------|
| **段落结构** | 25% | 每段 ≤ 150 词、单主题、有主题句 |
| **标题层级** | 20% | H1→H2→H3 不跳跃、标题描述性强 |
| **定义开头** | 15% | 关键段落以定义或断言开头（而非铺垫） |
| **自包含性** | 20% | 每个 section 可独立理解，不依赖上下文 |
| **锚点句** | 10% | 包含可独立引用的事实句（带数据或权威来源） |
| **列表/表格** | 10% | 结构化数据便于精确引用 |

### 评分模型（0-100）

```text
rag_readiness = paragraph_score × 0.25
              + heading_score × 0.20
              + definition_score × 0.15
              + self_contained_score × 0.20
              + anchor_sentence_score × 0.10
              + structured_data_score × 0.10
```

### 输出结构

```json
{
  "rag_readiness_score": 68,
  "band": "good",
  "breakdown": {
    "paragraph_structure": { "score": 72, "issues": ["第3段超过200词"] },
    "heading_hierarchy": { "score": 85, "issues": [] },
    "definition_openings": { "score": 55, "issues": ["仅40%的段落以定义开头"] },
    "self_containment": { "score": 65, "issues": ["第2段依赖第1段上下文"] },
    "anchor_sentences": { "score": 60, "issues": ["仅发现2个可独立引用的事实句"] },
    "structured_data": { "score": 80, "issues": ["存在表格但缺少列表"] }
  },
  "chunk_friendly_sections": 8,
  "total_sections": 12,
  "chunk_utilization": 0.67,
  "recommendations": [
    "将第3段拆分为2个独立段落",
    "为第5、7段添加定义性开头句",
    "在关键段落添加带数据的锚点句"
  ]
}
```

### 评分等级

| 等级 | 分数段 | 含义 |
|------|--------|------|
| **RAG-Ready** | 86-100 | 内容高度可分块，AI 可精确引用 |
| **Good** | 68-85 | 大部分内容适合分块 |
| **Needs Work** | 36-67 | 需要结构调整才能有效分块 |
| **Not Ready** | 0-35 | 内容结构不适合 RAG 检索 |

---

## Agent 使用指南

1. **Freshness Score** 在 Phase 2（Brand Research）阶段计算，作为品牌研究的一部分
2. **RAG Readiness** 在 Phase 2 评估品牌官网代表性页面时计算
3. 两个分数都写入 `metrics.json`
4. 分数低的项目自动提升对应机会的 `executability` 和 `evidence_readiness` 权重
5. **不做全量内容分析**，仅通过搜索结果 snippet 和已知 facts 抽样评估