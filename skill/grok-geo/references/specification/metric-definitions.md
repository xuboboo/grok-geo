# 指标定义

全部由 `calculate_metrics.py` 确定性计算。Agent 不得手动计算或修改数值。

## 核心指标

### mention_rate（提及率）
- 公式：品牌被提及的有效回答数 / 有效回答总数
- 含义：品牌在 AI 搜索中被提到的概率

### recommendation_rate（推荐率）
- 公式：明确推荐的回答数 / 推荐型有效回答数
- 推荐型回答：intent ∈ {recommendation, comparison, purchase}
- 含义：品牌被正面推荐的概率

### visibility_score（可见度分）
- 公式：Σ(position_score × business_value) / Σ(business_value) × 100
- 裁剪到 [0, 100]
- position_score 由 mention_type 和 recommendation_rank 决定

### recommendation_sov（推荐份额）
- 公式：品牌正向推荐分 / (品牌正向推荐分 + 竞品正向推荐分)
- 含义：品牌在推荐场景中的相对份额

### owned_citation_rate（自有引用率）
- 公式：引用品牌官网的有效回答数 / 有效回答总数
- 含义：AI 搜索引用品牌自有内容的概率

### earned_support_rate（第三方支持率）
- 公式：第三方正面引用回答数 / 有引用的有效回答数
- 含义：第三方内容支持品牌的程度

### accuracy_score（信息准确率）
- 公式：(correct + 0.5 × partially_correct) / 可验证声明数
- 含义：AI 搜索中品牌信息的准确性

### question_coverage（问题覆盖率）
- 公式：品牌被提及的问题数 / 有效问题总数
- 含义：品牌在多少比例的问题中被提到

## 统计工具

- 所有比例类指标输出：分子、分母、样本量、Wilson 95% CI
- Wilson CI 使用 z=1.96（95% 置信度）
- 除零场景返回 null 而非报错