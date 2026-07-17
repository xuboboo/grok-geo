# 内容可引用性评分引擎

## 目标

评估品牌官网内容被 AI 引擎引用的**可引用性**（Citability）——不仅仅是"能不能被找到"，而是"AI 愿不愿意引用你"。

## 方法来源

| 论文 | 会议 | 关键发现 |
|------|------|----------|
| [GEO: Generative Engine Optimization](https://arxiv.org/abs/2311.09735) | KDD 2024 | Cite Sources: +115%, Statistics: +40%, Fluency: +29% |
| [AutoGEO](https://arxiv.org/abs/2510.11438) | ICLR 2026 | 自动规则提取，比 Princeton 基线 +50.99% |
| [C-SEO Bench](https://arxiv.org/abs/2506.11097) | 2025 | 基础设施比内容改写更重要 |

## 评分方法（Top 20 核心方法）

按效果提升幅度排序，Agent 在 Phase 2 品牌研究阶段通过搜索结果 snippet 抽样检测：

### 信号类（Signal-based）

| # | 方法 | 效果提升 | 检测方式 | 分值 |
|---|------|----------|----------|------|
| 1 | **Cite Sources** — 引用外部权威来源 | +115% | snippet 中出现外部链接 | /8 |
| 2 | **Statistics** — 包含具体数据 | +40% | snippet 中有数字 | /7 |
| 3 | **Quotation** — 包含直接引语 | +41% | snippet 中有引号 | /6 |
| 4 | **Fluency** — 流畅的散文体 | +29% | 非碎片化文本 | /5 |
| 5 | **Technical Terms** — 使用专业术语 | +25% | 行业关键词密度 | /4 |
| 6 | **Authoritative Tone** — 权威语气 | +20% | 断言式语句而非犹豫式 | /3 |

### 结构类（Structure-based）

| # | 方法 | 检测方式 | 分值 |
|---|------|----------|------|
| 7 | **Structured Data** — JSON-LD / Schema.org | Phase 2 已覆盖（site-readiness-checklist） | /4 |
| 8 | **FAQ Format** — 问答结构 | snippet 中出现 Q/A 模式 | /4 |
| 9 | **Numbered Lists** — 有序列表 | snippet 中有 1. 2. 3. 或 <ol> | /3 |
| 10 | **Tables** — 表格数据 | snippet 中有表格结构 | /3 |
| 11 | **Definition Opening** — 段落以定义开头 | 首句是断言/定义 | /3 |
| 12 | **Heading Hierarchy** — 清晰的标题层级 | snippet 中有 H2/H3 | /2 |

### 实体类（Entity-based）

| # | 方法 | 检测方式 | 分值 |
|---|------|----------|------|
| 13 | **Unique Entities** — 独特实体密度 | 品牌名、产品名、创始人名出现频率 | /3 |
| 14 | **Knowledge Graph Links** — 外部实体链接 | Wikipedia/Wikidata/LinkedIn 引用 | /3 |
| 15 | **Cross-Reference** — 交叉引用 | 页面间相互链接 | /2 |
| 16 | **Consistent Naming** — 一致的命名 | 品牌名拼写一致 | /2 |

### 时效类（Freshness-based）

| # | 方法 | 检测方式 | 分值 |
|---|------|----------|------|
| 17 | **Date Modified** — 最近更新日期 | snippet 中有日期 | /2 |
| 18 | **Current Data** — 当前年份数据 | 引用 2025/2026 数据 | /2 |
| 19 | **Version Markers** — 版本标记 | "v4.0"、"最新版" | /1 |
| 20 | **Update Signals** — 更新信号 | "持续更新"、"定期修订" | /1 |

**总分：/100（20 项方法加权求和）**

## 输出结构

```json
{
  "citability_score": 72,
  "band": "good",
  "top_strengths": [
    {"method": "Cite Sources", "score": 7, "max": 8, "evidence": "snippet 包含 3 个外部链接"},
    {"method": "Statistics", "score": 6, "max": 7, "evidence": "包含具体百分比数据"}
  ],
  "top_weaknesses": [
    {"method": "Quotation", "score": 1, "max": 6, "evidence": "未发现直接引语"},
    {"method": "FAQ Format", "score": 0, "max": 4, "evidence": "无问答结构"}
  ],
  "method_scores": {
    "cite_sources": {"score": 7, "max": 8},
    "statistics": {"score": 6, "max": 7},
    "quotation": {"score": 1, "max": 6},
    "fluency": {"score": 4, "max": 5},
    "technical_terms": {"score": 3, "max": 4},
    "authoritative_tone": {"score": 2, "max": 3},
    "structured_data": {"score": 4, "max": 4},
    "faq_format": {"score": 0, "max": 4},
    "numbered_lists": {"score": 2, "max": 3},
    "tables": {"score": 1, "max": 3},
    "definition_opening": {"score": 2, "max": 3},
    "heading_hierarchy": {"score": 2, "max": 2},
    "unique_entities": {"score": 2, "max": 3},
    "knowledge_graph_links": {"score": 1, "max": 3},
    "cross_reference": {"score": 2, "max": 2},
    "consistent_naming": {"score": 2, "max": 2},
    "date_modified": {"score": 2, "max": 2},
    "current_data": {"score": 2, "max": 2},
    "version_markers": {"score": 1, "max": 1},
    "update_signals": {"score": 0, "max": 1}
  },
  "recommendations": [
    "添加 FAQ 结构（效果提升最大的未覆盖方法）",
    "在关键段落添加直接引语",
    "添加包含年份的数据表格"
  ]
}
```

## 评分等级

| 等级 | 分数段 | 含义 |
|------|--------|------|
| **Highly Citable** | 86-100 | 内容高度可引用，AI 优先选择 |
| **Good** | 68-85 | 多数信号到位，部分可优化 |
| **Foundation** | 36-67 | 基础结构存在，可引用性不足 |
| **Not Citable** | 0-35 | 内容难以被 AI 有效引用 |

## Agent 使用指南

1. 在 Phase 2（Brand Research）阶段，对品牌官网代表性页面执行
2. 通过 3-5 次 `web_search("site:domain.com ...")` 的 snippet 抽样检测
3. 不做全站爬取，仅抽样评估
4. 低分方法自动纳入机会生成的输入
5. 与 `site-readiness-checklist`（技术层）和 `content-freshness`（时效层）互补