# Closed-Loop Optimization — 闭环优化执行

## 设计目标

从「发现问题」到「执行修复」到「验证效果」的完整闭环。
不只是诊断，而是生成可执行的优化动作并追踪影响。

## 闭环流程

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  1. GAP         │     │  2. ACTION      │     │  3. EXECUTE     │
│  DETECTION      │────▶│  GENERATION     │────▶│  & TRACK        │
│                 │     │                 │     │                 │
│  - 引用缺口     │     │  - 内容创建     │     │  - 外联执行     │
│  - 竞品优势     │     │  - 技术修复     │     │  - 进度追踪     │
│  - 实体缺失     │     │  - 外联计划     │     │  - 影响度量     │
│  - 漏斗断点     │     │  - Schema 补充  │     │  - A/B 验证     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                                              │
         │              ┌─────────────────┐             │
         └──────────────│  4. VERIFY      │◀────────────┘
                        │  & ITERATE      │
                        │                 │
                        │  - 重跑审计     │
                        │  - 对比 delta   │
                        │  - 迭代优化     │
                        └─────────────────┘
```

## 动作类型

### 1. 内容创建 (Content Creation)
- **触发**: 品牌在某类问题中完全未被提及
- **动作**: 创建针对性内容页面
- **验证**: 14 天后重查同类问题

### 2. 内容更新 (Content Update)
- **触发**: 品牌被提及但信息过时或不准确
- **动作**: 更新现有内容中的过时信息
- **验证**: 7 天后重查

### 3. 技术修复 (Technical Fix)
- **触发**: GEO Lint 发现 ERROR 级问题
- **动作**: 修复 robots.txt / llms.txt / schema 等
- **验证**: 3 天后重检

### 4. 外联建设 (Outreach Building)
- **触发**: 引用来源集中在少数域名
- **动作**: 联系高影响力发布者/媒体
- **目标**: 获得新的第三方引用
- **验证**: 30 天后检查引用来源多样性

### 5. 误解纠正 (Misperception Correction)
- **触发**: AI 引擎传播关于品牌的错误信息
- **动作**: 更新官网声明 + 联系平台纠正
- **验证**: 7 天后重查

### 6. Schema 优化 (Schema Optimization)
- **触发**: GEO Lint Schema 维度得分低
- **动作**: 补充/修正结构化数据
- **验证**: 3 天后重检

### 7. FAQ 创建 (FAQ Creation)
- **触发**: 品牌在常见问题中未被推荐
- **动作**: 创建 FAQ 内容 + FAQPage schema
- **验证**: 14 天后重查

## 外联执行模板

### 发布者外联（基于 Publisher Influence Mapping）

```
Subject: Collaboration Opportunity — [Your Brand] × [Publisher]

Hi [Name],

I noticed your recent article "[Article Title]" covers [topic] extensively.
We've built [Brand] specifically to address [pain point mentioned in article].

Would you be open to:
1. A brief demo of [Brand] for a potential mention in future coverage
2. Contributing a guest piece on [relevant topic]
3. Providing exclusive data/study for your readers

[Brand] currently serves [X] customers including [notable client].
Happy to share more details at your convenience.

Best,
[Name]
```

### 作者外联（基于 AthenaHQ 模式）

```
Subject: Quick question about your [Platform] recommendation

Hi [Author Name],

I saw your [answer/article] about [topic] where you mentioned [competitor].
I'm curious — have you had a chance to look at [Brand]?

We recently [milestone/achievement] and I think your audience would find
[value proposition] relevant to their needs.

Would love to get your honest feedback — even if it's just a quick reply.

Thanks,
[Name]
```

## 影响追踪指标

| 指标 | 计算方式 | 目标 |
|------|----------|------|
| 引用增长率 | (新引用数 - 基线引用数) / 基线 | > 20% |
| 提及率变化 | 新提及率 - 基线提及率 | > 10pp |
| 推荐率变化 | 新推荐率 - 基线推荐率 | > 5pp |
| 引用来源多样性 | 新增独立引用域名数 | > 5 |
| 外联回复率 | 回复数 / 发送数 | > 15% |
| 内容发布数 | 已发布的新内容页数 | 按计划 |

## 输出格式

```json
{
  "schema_version": "1.0",
  "generated_at": "ISO-8601",
  "gap_analysis": {
    "citation_gaps": [...],
    "competitor_advantages": [...],
    "entity_missing": [...],
    "funnel_breakpoints": [...]
  },
  "action_plan": [
    {
      "id": "act_001",
      "type": "content_creation|content_update|technical_fix|outreach|misperception|schema|faq",
      "priority": "P0|P1|P2",
      "title": "string",
      "description": "string",
      "target_url": "string",
      "effort_hours": 0,
      "deadline_days": 0,
      "validation_method": "string",
      "status": "pending|in_progress|completed|verified"
    }
  ],
  "outreach_templates": [...],
  "tracking_metrics": { ... }
}
```