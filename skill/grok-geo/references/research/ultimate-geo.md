# Ultimate GEO — 终极能力补全

## 终极能力清单

### 能力 1: Agentic Brand Vault — 品牌叙事一致性引擎

**核心功能：**
- 品牌叙事声明 → 自动检查跨 AI 引擎的一致性
- 词关联图谱：AI 模型中品牌与哪些词关联
- 叙事偏差检测：AI 回答是否偏离品牌定位
- 跨引擎品牌一致性评分 (CECS)

**词关联图谱 (Word Association Graph)：**

```
品牌 "Notion" →
  正向关联: [productivity, collaborative, workspace, flexible, templates]
  中性关联: [documentation, notes, wiki, database]
  负向关联: [pricey, limited offline, mobile]
  目标关联: [knowledge management, company wiki, second brain]
  缺失关联: [AI writing, calendar, email]  ← 缺口
```

### 能力 2: Narrative & Tone Analysis — 叙事语调分析

**分析维度：**

| 维度 | 说明 |
|------|------|
| 叙述框架 | AI 是否将品牌描述为 leader / challenger / innovator / specialist |
| 语调倾向 | positive / neutral / negative / mixed |
| 语言模式 | AI 使用的关键词和短语模式 |
| 品牌定位一致性 | AI 描述 vs 品牌自我定位的偏差 |
| 情感叙事 | 品牌故事的情感基调 |
| 竞品叙事对比 | 竞品被描述的叙事框架差异 |

**叙事偏差评分 (Narrative Deviation Score)：**

```
NDS = 1 - (cosine_similarity(AI_narrative, brand_narrative))

0.0 = 完全一致
0.5 = 部分偏差
1.0 = 完全偏离
```

### 能力 3: Multi-Model Coverage Heatmap — 多模型覆盖热力图

**热力图矩阵：**

```
                      ChatGPT  Perplexity  Claude  Gemini  Grok
Brand A (us)           85%       72%        68%     90%     45%
Competitor X           92%       88%        75%     70%     60%
Competitor Y           55%       45%        80%     65%     35%

Coverage Gap:          -7%       -16%       -7%     +20%   -15%
Platform Favorability: Gemini > ChatGPT > Perplexity > Claude > Grok
```

**平台偏好分析：**
- ChatGPT: 偏好权威来源和故事性内容
- Perplexity: 偏好引用密集、学术背书的内容  
- Claude: 偏好结构化、分析性内容
- Gemini: 偏好 Google 生态内容（Maps, Reviews, YouTube）
- Grok: 偏好实时、社交验证内容

**建议：** 根据平台的差异化内容策略优化

### 能力 4: Agentic GEO Engine — 自主优化代理

**自主优化循环：**

```
┌─────────────────────────────────────────────────────┐
│  Agentic GEO Engine                                  │
│                                                       │
│  while True:                                          │
│    # 感知                                               │
│    metrics = run_complete_audit(brand)                 │
│                                                       │
│    # 诊断                                               │
│    gaps = detect_gaps(metrics, baselines)              │
│                                                       │
│    # 决策                                               │
│    actions = prioritize_actions(gaps, resources)       │
│                                                       │
│    # 执行                                               │
│    for action in actions:                              │
│        execute(action)                                 │
│                                                       │
│    # 验证                                               │
│    next_checkin = schedule_next_run(action)            │
│                                                       │
│    # 等待下一个检查点                                     │
│    sleep_until(next_checkin)                           │
└─────────────────────────────────────────────────────┘
```

**自主代理能力：**

| 代理 | 职责 | 触发条件 |
|------|------|----------|
| 监控代理 | 持续监测 AI 可见度变化 | 每日自动 |
| 诊断代理 | 检测差距和异常 | 监控触发 |
| 优化代理 | 生成和执行优化动作 | 诊断完成 |
| 验证代理 | 验证优化效果 | 动作完成 |
| 报告代理 | 生成优化报告 | 每周/月 |

### 能力 5: Hybrid GEO+SEO Metric — 统一 SEO/GEO 指标

**统一指标模型：**

```
Unified Brand Score (UBS) = 0.4 × GEO_Score + 0.3 × SEO_Score + 0.3 × Brand_Score

GEO_Score = AI 可见度指标 (0-100)
SEO_Score = 传统搜索指标 (0-100)  
Brand_Score = 品牌健康度指标 (0-100)
```

**统一看板字段：**

| 指标 | GEO | SEO | 来源 |
|------|-----|-----|------|
| 可见度 | AI mention rate | Organic visibility | 搜索+AI |
| 流量 | AI referrer sessions | Organic traffic | GSC+GA4 |
| 转化 | AI conversion rate | Organic conversion | GA4 |
| 排名 | AI recommendation position | SERP position | 多引擎 |
| 内容 | AI citation coverage | Keyword coverage | 内容分析 |

### 输出格式

```json
{
  "schema_version": "2.0",
  "version": "4.0.0",
  "brand_vault": {
    "narrative_statements": [],
    "word_association_graph": {},
    "cross_engine_consistency_score": 0.0,
    "deviations": []
  },
  "narrative_analysis": {
    "framing": "string",
    "tone": "string",
    "language_patterns": [],
    "positioning_deviation": 0.0,
    "competitor_narratives": {}
  },
  "coverage_heatmap": {
    "by_platform": {},
    "favorability_ranking": [],
    "recommended_strategies": []
  },
  "agentic_engine": {
    "status": "running|idle|error",
    "last_optimization": "ISO-8601",
    "optimization_cycle_count": 0,
    "total_actions_executed": 0,
    "active_agents": [],
    "next_scheduled_run": "ISO-8601"
  },
  "hybrid_metrics": {
    "ubs": 0.0,
    "geo_score": 0.0,
    "seo_score": 0.0,
    "brand_score": 0.0,
    "breakdown": {}
  }
}
```