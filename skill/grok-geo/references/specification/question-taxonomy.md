# 问题分类与生成规则

## Intent 类型

| intent | 说明 | 典型示例 |
| --- | --- | --- |
| category_awareness | 品类认知 | "项目管理软件有哪些选择？" |
| use_case | 使用场景 | "20人研发团队怎么做需求管理？" |
| recommendation | 推荐选择 | "哪个协作工具适合远程团队？" |
| comparison | 品牌对比 | "Jira 和 Linear 哪个更好？" |
| purchase | 价格采购 | "企业版项目管理工具多少钱？" |
| trust_risk | 信任风险 | "XX 软件数据安全吗？" |
| brand_fact | 品牌事实 | "示例科技什么时候成立的？" |
| support | 使用与售后 | "XX 客户支持响应怎么样？" |

## 生成约束

1. **不含品牌词**的问题至少占 70%（validate_questions.py 校验）
2. **推荐/对比/采购**类问题至少占 30%
3. **brand_fact** 类不超过 20%
4. quick 模式 10 题，standard 模式 30 题
5. 每题可有最多 query_variants 个变体查询

## 问题对象 Schema

```json
{
  "id": "q-001",
  "text": "20人研发团队适合什么项目管理工具？",
  "intent": "recommendation",
  "business_value": 80,
  "target_region": "中国大陆",
  "language": "zh-CN",
  "query_variants": ["小团队项目管理软件推荐"]
}
```

## 去重规则

### 规则去重
- Unicode NFKC 规范化后完全一致 → 保留先生成的

### 语义去重
- 去除标点、停用词后核心实体集合重叠 >80% → 保留 business_value 更高的