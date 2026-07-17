# Analytics Integration — GSC + GA4 AI Referrer 分析

## 设计目标

通过 Google Search Console 和 Google Analytics 4 数据，量化 AI 搜索对品牌网站流量的实际影响。
追踪 AI referrer、AI 来源的用户行为、AI 搜索带来的转化。

## 数据源

### 1. Google Search Console (GSC)

**API**: Google Search Console API v1

**关键指标**:
- `impressions`: 搜索展示次数
- `clicks`: 点击次数
- `ctr`: 点击率
- `position`: 平均排名

**AI 相关分析**:
- AI Overviews 触发的查询（通过 position 变化检测）
- AI 引用后的流量变化
- 被 AI 引用的页面排名变化

### 2. Google Analytics 4 (GA4)

**API**: Google Analytics Data API v1beta

**关键指标**:
- `sessions`: 会话数
- `users`: 用户数
- `engagementRate`: 互动率
- `conversions`: 转化数

**AI Referrer 追踪**:
- `chatgpt.com` — ChatGPT 搜索来源
- `perplexity.ai` — Perplexity 来源
- `claude.ai` — Claude 来源
- `gemini.google.com` — Gemini 来源
- `copilot.microsoft.com` — Copilot 来源
- `you.com` — You.com 来源

## AI Referrer 分析维度

### 1. 流量概览 (Traffic Overview)

| 指标 | 说明 |
|------|------|
| AI 总流量 | 所有 AI referrer 的会话总数 |
| AI 流量占比 | AI 流量 / 总流量 |
| AI 流量趋势 | 按周/月的 AI 流量变化 |
| AI 来源分布 | 各 AI 平台的流量占比 |

### 2. 用户行为 (User Behavior)

| 指标 | 说明 |
|------|------|
| AI 用户互动率 | AI 来源用户的 engagement rate |
| AI 用户停留时间 | 平均会话时长 |
| AI 用户跳出率 | 只浏览 1 页就离开的比例 |
| AI 用户页面深度 | 平均浏览页数 |

### 3. 转化分析 (Conversion Analysis)

| 指标 | 说明 |
|------|------|
| AI 转化率 | AI 来源的转化率 |
| AI 转化价值 | AI 来源带来的转化价值 |
| AI 转化路径 | AI 用户的典型转化路径 |
| AI vs 其他来源 | AI 流量与其他来源的转化对比 |

### 4. 内容洞察 (Content Insights)

| 指标 | 说明 |
|------|------|
| AI 着陆页 Top 10 | AI 流量最常到达的页面 |
| AI 高互动内容 | AI 用户互动率最高的内容 |
| AI 高转化内容 | AI 用户转化率最高的内容 |
| AI 内容缺口 | 有 AI 流量但无转化的页面 |

## GSC API 查询示例

```json
{
  "startDate": "2026-06-01",
  "endDate": "2026-07-17",
  "dimensions": ["query", "page", "date"],
  "dimensionFilterGroups": [{
    "filters": [{
      "dimension": "page",
      "operator": "contains",
      "expression": "/product/"
    }]
  }],
  "rowLimit": 1000
}
```

## GA4 API 查询示例

```json
{
  "dateRanges": [{ "startDate": "2026-06-01", "endDate": "2026-07-17" }],
  "dimensions": [
    { "name": "sessionSource" },
    { "name": "sessionMedium" },
    { "name": "landingPage" }
  ],
  "metrics": [
    { "name": "sessions" },
    { "name": "engagementRate" },
    { "name": "conversions" }
  ],
  "dimensionFilter": {
    "filter": {
      "fieldName": "sessionSource",
      "inListFilter": {
        "values": ["chatgpt.com", "perplexity.ai", "claude.ai", "gemini.google.com"]
      }
    }
  }
}
```

## 输出格式

```json
{
  "schema_version": "1.0",
  "period": { "start": "2026-06-01", "end": "2026-07-17" },
  "ai_traffic_overview": {
    "total_sessions": 0,
    "ai_sessions": 0,
    "ai_share": 0.0,
    "trend": "growing|stable|declining"
  },
  "ai_sources": {
    "chatgpt.com": { "sessions": 0, "share": 0.0, "engagement_rate": 0.0 },
    "perplexity.ai": { "sessions": 0, "share": 0.0, "engagement_rate": 0.0 }
  },
  "ai_user_behavior": {
    "avg_engagement_rate": 0.0,
    "avg_session_duration_sec": 0,
    "bounce_rate": 0.0,
    "pages_per_session": 0.0
  },
  "ai_conversions": {
    "total_conversions": 0,
    "conversion_rate": 0.0,
    "top_converting_pages": []
  },
  "top_landing_pages": [],
  "gsc_insights": {
    "ai_triggered_queries": [],
    "position_changes": []
  }
}
```

## 安全约束

- API credentials 通过环境变量传递
- 不存储用户的 PII 数据
- 数据仅用于分析，不用于广告定向
- 遵守 Google API 服务条款