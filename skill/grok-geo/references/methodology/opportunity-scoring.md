# 机会评分规则

## 评分公式

```
total = business_value × 0.30
      + competitive_gap × 0.25
      + brand_absence × 0.20
      + executability × 0.15
      + evidence_readiness × 0.10
      - risk_penalty
```

## 各维度说明

| 维度 | 权重 | 含义 | 范围 |
| --- | --- | --- | --- |
| business_value | 0.30 | 目标问题的业务价值 | 0-100 |
| competitive_gap | 0.25 | 竞品占优但目标品牌缺席的差距 | 0-100 |
| brand_absence | 0.20 | 目标品牌在高价值问题中缺席的程度 | 0-100 |
| executability | 0.15 | 建议的可执行性（越容易执行分越高） | 0-100 |
| evidence_readiness | 0.10 | 现有证据/内容资产的就绪程度 | 0-100 |
| risk_penalty | 减分 | 高风险声明或实施风险 | 0-50 |

## 机会类型

| type | 说明 |
| --- | --- |
| content_gap | 品牌缺席高价值问题，需创建内容 |
| recommendation_gap | 竞品被推荐但品牌未被提及 |
| citation_gap | AI 引用竞品/第三方但未引用品牌官网 |
| fact_correction | 品牌信息错误或过时，需纠正 |
| competitor_advantage | 竞品在某方面有明显优势信号 |

## 输出约束

- 最多 10 条机会（rank_opportunities.py 截断）
- 同 intent + 同推荐资产的机会自动合并
- 按 total_score 降序排列

## 机会对象

```json
{
  "id": "OPP-001",
  "title": "补充项目管理工具对比内容",
  "opportunity_type": "content_gap",
  "observed_gap": "品牌未出现在项目管理工具推荐问题中",
  "competitor_evidence": "竞品A和B被推荐为Top3",
  "recommended_asset": "发布项目管理工具对比评测文章",
  "target_question_ids": ["q-003", "q-007"],
  "scores": {
    "business_value": 85,
    "competitive_gap": 70,
    "brand_absence": 90,
    "executability": 80,
    "evidence_readiness": 30,
    "risk_penalty": 0,
    "total": 72.5
  }
}
```