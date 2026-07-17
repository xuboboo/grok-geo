# 搜索快照归档与时间对比

## 目标

将每次搜索结果**归档为可对比的快照**，支持跨时间、跨版本、跨平台的品牌可见度变化追踪。

## 快照对象

每次 `web_search` 调用的结果归档为一个快照：

```json
{
  "snapshot_id": "snap_20260717T084212Z_q001_v1",
  "run_id": "geo_20260717T083012Z_a1b2c3d4",
  "question_id": "q-001",
  "query_text": "适合五十人研发团队的项目管理软件有哪些？",
  "query_variant": "original",
  "captured_at": "2026-07-17T08:42:12Z",
  "search_environment": "openai_web_search",
  "answer_text": "...",
  "answer_hash": "sha256:...",
  "citations": [...],
  "extracted_signals": {...},
  "brand_snapshot": {
    "mentioned": true,
    "cited": true,
    "position": 2,
    "recommendation_type": "recommended",
    "sentiment_score": 75
  },
  "competitor_snapshots": {
    "竞品A": {"mentioned": true, "position": 1, "cited": true},
    "竞品B": {"mentioned": false}
  }
}
```

## 快照存储结构

```text
<RUN>/
  snapshots/
    <question_id>/
      snap_<timestamp>_<variant>.json    # 单次快照
    <question_id>/
      snap_<timestamp>_<variant>.json
  snapshots_index.json                   # 快照索引（按时间排序）
```

## 快照索引

```json
{
  "snapshots": [
    {
      "snapshot_id": "snap_20260717T084212Z_q001_v1",
      "question_id": "q-001",
      "captured_at": "2026-07-17T08:42:12Z",
      "brand_mentioned": true,
      "brand_cited": true,
      "brand_position": 2,
      "answer_hash": "sha256:abc123..."
    }
  ],
  "total_snapshots": 60,
  "unique_questions": 30,
  "date_range": {
    "first": "2026-07-17T08:30:00Z",
    "last": "2026-07-17T09:15:00Z"
  }
}
```

## 时间对比维度

### 同一 Run 内对比

- 原始查询 vs 变体查询的品牌可见度差异
- 不同问题间的品牌表现差异
- 批次间的品牌提及率变化趋势

### 跨 Run 对比（历史审计）

- 同一问题在不同时间的品牌位置变化
- 引用来源的稳定性（哪些来源持续出现/消失）
- 竞品排名的变化
- 新出现的引用来源

## 对比输出

```json
{
  "comparison_type": "cross_run",
  "question_id": "q-001",
  "baseline": {
    "run_id": "geo_20260710_...",
    "captured_at": "2026-07-10T10:00:00Z",
    "brand_position": 3,
    "brand_cited": false,
    "answer_hash": "sha256:def456..."
  },
  "current": {
    "run_id": "geo_20260717_...",
    "captured_at": "2026-07-17T08:42:00Z",
    "brand_position": 1,
    "brand_cited": true,
    "answer_hash": "sha256:abc123..."
  },
  "delta": {
    "position_change": -2,
    "citation_gained": true,
    "answer_changed": true,
    "new_citation_domains": ["blog.example.com"],
    "lost_citation_domains": ["old-review.com"],
    "severity": "improved"
  }
}
```

## 快照质量指标

| 指标 | 公式 | 含义 |
|------|------|------|
| `snapshot_count` | 总快照数 | 搜索覆盖量 |
| `unique_answer_rate` | 唯一 answer_hash 数 / 总快照数 | 回答多样性 |
| `brand_mention_rate` | brand_mentioned=true / 总快照 | 品牌曝光率 |
| `brand_citation_rate` | brand_cited=true / 总快照 | 品牌引用率 |
| `avg_brand_position` | Σ(brand_position) / 提及快照数 | 平均排名 |
| `position_volatility` | stddev(brand_position) | 排名稳定性 |

## Agent 使用指南

1. **每次搜索后**立即创建快照，保存到 `snapshots/<question_id>/`
2. **每次搜索后**更新 `snapshots_index.json`
3. **Run 结束时**计算快照质量指标，写入 `metrics.json` → `snapshot_quality`
4. **如有历史 Run**（用户提供 run_id），执行跨 Run 对比
5. 对比结果写入 `report.json` → `temporal_analysis`