# 语义漂移检测

## 目标

检测 AI 搜索回答中**品牌相关内容的语义变化**——不仅是位置变化，更是含义、情感、推荐力度的深层漂移。

## 漂移类型

### 1. 位置漂移（Position Drift）

品牌在推荐列表中的排名变化。

| 漂移方向 | 含义 | 严重度 |
|----------|------|--------|
| ↑ 提升 2+ 位 | 品牌可见度改善 | positive |
| → 不变 (±1) | 稳定 | neutral |
| ↓ 下降 2+ 位 | 品牌可见度下降 | warning |
| 消失 | 从回答中消失 | critical |

### 2. 引用漂移（Citation Drift）

品牌域名引用状态变化。

| 变化 | 含义 | 严重度 |
|------|------|--------|
| 新增引用 | 品牌内容被引用 | positive |
| 引用不变 | 稳定 | neutral |
| 引用消失 | 品牌内容不再被引用 | warning |
| 竞品新增引用 | 竞品获得引用 | warning |

### 3. 情感漂移（Sentiment Drift）

品牌描述的情感基调变化。

| 变化 | 含义 | 严重度 |
|------|------|--------|
| 情感提升 ≥15 分 | 正面评价增加 | positive |
| 情感变化 <15 分 | 稳定 | neutral |
| 情感下降 ≥15 分 | 负面评价增加 | warning |
| 情感下降 ≥30 分 | 严重负面化 | critical |

### 4. 推荐漂移（Recommendation Drift）

推荐类型变化。

| 变化 | 含义 | 严重度 |
|------|------|--------|
| 升级（mentioned→recommended） | 推荐力度增强 | positive |
| 不变 | 稳定 | neutral |
| 降级（recommended→mentioned） | 推荐力度减弱 | warning |
| 降级到 discouraged | 被明确不推荐 | critical |

### 5. 竞品漂移（Competitor Drift）

竞品在回答中的出现变化。

| 变化 | 含义 | 严重度 |
|------|------|--------|
| 竞品消失 | 竞品可见度下降 | positive |
| 竞品不变 | 稳定 | neutral |
| 新竞品出现 | 新竞争者进入 | warning |
| 竞品排名超过品牌 | 竞品地位提升 | critical |

### 6. 来源漂移（Source Drift）

引用来源的稳定性。

| 变化 | 含义 | 严重度 |
|------|------|--------|
| 品牌新增来源引用 | 品牌内容影响力扩大 | positive |
| 来源稳定 | 无变化 | neutral |
| 品牌来源消失 | 品牌内容影响力下降 | warning |
| 竞品新增来源 | 竞品内容影响力扩大 | warning |

## 漂移评分模型

### 单题漂移分（0-100，越高越稳定）

```text
drift_score = 100
  - 位置漂移扣分: |Δposition| × 8（上限 40）
  - 引用漂移扣分: 失去引用 -15, 竞品新增引用 -10
  - 情感漂移扣分: |Δsentiment| / 2（上限 25）
  - 推荐漂移扣分: 降级 -20, 升级 +0
  - 竞品漂移扣分: 新竞品出现 -10, 竞品超越 -15
```

### 综合漂移分（Run 级别）

```text
overall_drift = Σ(question_drift_score × business_weight) / Σ(business_weight)
```

## 输出结构

```json
{
  "drift_analysis": {
    "overall_drift_score": 72,
    "drift_band": "minor_drift",
    "questions_analyzed": 30,
    "drifts_detected": {
      "position_drifts": 5,
      "citation_drifts": 3,
      "sentiment_drifts": 2,
      "recommendation_drifts": 1,
      "competitor_drifts": 4,
      "source_drifts": 6
    },
    "critical_drifts": [
      {
        "question_id": "q-007",
        "drift_type": "recommendation",
        "severity": "critical",
        "baseline": {"recommendation_type": "recommended", "position": 2},
        "current": {"recommendation_type": "mentioned_only", "position": 5},
        "evidence": "品牌从第2位推荐降为仅提及，第5位"
      }
    ],
    "positive_drifts": [
      {
        "question_id": "q-012",
        "drift_type": "position",
        "severity": "positive",
        "baseline": {"position": 4},
        "current": {"position": 1},
        "evidence": "品牌从第4位提升到第1位"
      }
    ],
    "recommendations": [
      "q-007: 品牌推荐降级需紧急调查，检查是否有负面事件",
      "q-012: 品牌排名提升，确认是否为持续改善"
    ]
  }
}
```

## 漂移等级

| 等级 | 分数段 | 含义 |
|------|--------|------|
| **Stable** | 86-100 | 品牌表现高度稳定 |
| **Minor Drift** | 68-85 | 少量变化，需关注 |
| **Significant Drift** | 36-67 | 明显变化，需行动 |
| **Major Drift** | 0-35 | 严重变化，需紧急响应 |

## Agent 使用指南

1. **仅当存在历史 Run**（用户提供的 run_id）时执行漂移检测
2. 按 `question_id` 匹配基线和当前快照
3. 计算 6 种漂移类型的严重度
4. critical 漂移自动写入机会生成的最高优先级
5. 结果写入 `report.json` → `drift_analysis`