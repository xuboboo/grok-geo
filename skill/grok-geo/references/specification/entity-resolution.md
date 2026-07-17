# 实体解析规则

## 标准化流程

1. Unicode NFKC 规范化
2. 去除商标符号（TM、R、C）
3. 全角转半角
4. 标点转空格
5. 统一小写
6. 合并连续空格
7. 可选去除公司后缀（有限公司、Inc.、Ltd. 等）

## 匹配优先级

1. 官方全名（brand_name）
2. 品牌别名（brand_aliases）
3. 产品名（products[].name / aliases）
4. 英文名
5. 模糊匹配（编辑距离）
6. 模型语义消歧（兜底）

## Mention 类型

| mention_type | 说明 | 位置分 |
| --- | --- | --- |
| strongly_recommended | 强烈推荐 | rank=1:1.0, rank=2:0.75, rank=3:0.55, else:0.30 |
| recommended | 推荐 | rank=1:1.0, rank=2:0.75, rank=3:0.55, else:0.30 |
| weakly_recommended | 弱推荐 | 0.20 |
| positive_mention | 正面提及 | 0.10 |
| neutral_mention | 中性提及 | 0.05 |
| comparison_only | 仅对比出现 | 0.05 |
| citation_only | 仅引用出现 | 0.05 |
| negative_mention | 负面提及 | 0.00 |
| not_recommended | 明确不推荐 | -0.30 |

## 竞品实体

- entity_type = "competitor"
- 来自 input.competitors 列表
- 与目标品牌相同的标准化规则
- 竞品与目标品牌名称冲突时拒绝输入

## 关键约束

- 不得仅凭文本位置推断推荐排名
- 推荐判定必须有明确的语义信号
- 无法确定时标记为 neutral_mention