# 搜索结果信号即时提取

## 目标

在每次搜索完成后**立即**从响应中提取结构化信号，而不等到 Phase 5 集中分析。这使得搜索过程本身成为一个**数据采集 + 即时分析**的双重管道。

## 信号分类

### A 类：品牌可见度信号（即时提取，确定性）

| 信号 | 类型 | 提取方式 |
|------|------|----------|
| `brand_mentioned` | bool | 文本匹配（品牌名/别名/产品名） |
| `brand_cited` | bool | 引用 URL 匹配品牌域名 |
| `brand_domain_cited` | bool | 域名匹配（canonical_url 的 domain） |
| `brand_position_in_answer` | int \| null | 品牌首次出现的位置（按段落/列表项计） |
| `brand_in_heading` | bool | 品牌名是否出现在标题/列表项标题中 |

### B 类：推荐信号（Agent 提取，语义判断）

| 信号 | 类型 | 提取方式 |
|------|------|----------|
| `recommendation_detected` | bool | 上下文语义判断 |
| `recommendation_strength` | string | strongly_recommended / recommended / weakly_recommended / not_recommended |
| `recommendation_type` | string | top_pick / strong_alternative / conditional / mentioned_only / discouraged |
| `recommendation_rank` | int \| null | 有序列表中的排名 |

### C 类：竞品信号（即时提取 + 语义）

| 信号 | 类型 | 提取方式 |
|------|------|----------|
| `competitor_mentioned` | list[str] | 竞品名文本匹配 |
| `competitor_cited` | list[str] | 竞品域名引用匹配 |
| `competitor_recommendation` | list[dict] | 竞品的推荐状态 |

### D 类：引用来源信号（即时提取）

| 信号 | 类型 | 提取方式 |
|------|------|----------|
| `citation_domains` | list[str] | 从 citations[] 提取所有域名 |
| `citation_count` | int | 引用总数 |
| `citation_types` | dict | 按来源类型分类计数 |
| `brand_domain_in_citations` | bool | 品牌域名是否在引用中 |

### E 类：平台特征信号（Agent 推断）

| 信号 | 类型 | 提取方式 |
|------|------|----------|
| `detected_engine` | string | 从响应特征推断（chatgpt/perplexity/claude/gemini/unknown） |
| `has_inline_citations` | bool | 回答中是否有内联引用标注 |
| `has_source_cards` | bool | 是否有来源卡片 |
| `response_length` | int | 回答字数 |
| `has_list_structure` | bool | 是否包含列表 |
| `has_table_structure` | bool | 是否包含表格 |

### F 类：响应质量信号（Agent 评估）

| 信号 | 类型 | 提取方式 |
|------|------|----------|
| `answer_completeness` | float | 0-1，回答完整度 |
| `citation_density` | float | 引用密度（引用数/回答字数） |
| `factual_specificity` | string | high / medium / low |
| `is_refusal` | bool | 是否拒答 |
| `is_hallucinated` | bool | 是否明显编造（无引用支撑的具体声明） |

## 即时提取流程

```
web_search 返回结果
    │
    ├─ 1. 保存原始响应（raw/search_results.jsonl）
    │
    ├─ 2. A 类信号提取（确定性，脚本）
    │     ├─ brand_mentioned: contains_brand_token(answer_text, brand_name, aliases)
    │     ├─ brand_cited: any(cit.url 匹配 brand_domain for cit in citations)
    │     ├─ brand_position: answer_text 中首次出现 brand 的段落索引
    │     └─ competitor_mentioned: [name for name in competitors if name in answer_text]
    │
    ├─ 3. D 类信号提取（确定性，脚本）
    │     ├─ citation_domains: set(cit.domain for cit in citations)
    │     ├─ citation_count: len(citations)
    │     └─ brand_domain_in_citations: brand_domain in citation_domains
    │
    ├─ 4. E 类信号提取（规则推断，脚本）
    │     ├─ response_length: len(answer_text)
    │     ├─ has_list_structure: 检测 "1." "2." 或 "\n-" 模式
    │     └─ has_table_structure: 检测 "|" 分隔符模式
    │
    └─ 5. B/F 类信号提取（Agent 语义判断）
          ├─ recommendation_detected: Agent 从上下文判断
          ├─ recommendation_strength: Agent 分级
          ├─ answer_completeness: Agent 评估
          └─ is_refusal: Agent 判断
```

## 提取优先级

1. **A 类 + D 类**：每次搜索后必须立即提取（脚本自动完成）
2. **E 类**：每次搜索后立即提取（规则推断）
3. **B 类 + F 类**：在 Phase 5 实体分析时由 Agent 提取
4. **C 类**：A 类完成后立即关联

## 信号聚合

搜索批次完成后，聚合以下统计：

```json
{
  "batch_id": 3,
  "questions_in_batch": 5,
  "signals_summary": {
    "brand_mentioned_count": 3,
    "brand_cited_count": 1,
    "recommendation_count": 2,
    "competitor_mentioned_unique": ["竞品A", "竞品B"],
    "avg_citation_count": 4.2,
    "platform_signals": {
      "has_inline_citations": 4,
      "has_source_cards": 3,
      "avg_response_length": 856
    }
  }
}
```

## 脚本接口

### extract_search_signals.py

```bash
python scripts/extract_search_signals.py \
  --search-result /tmp/search_result_q001.json \
  --brand-name "示例科技" \
  --brand-domain "example.com" \
  --competitors '["竞品A","竞品B"]' \
  --aliases '["示例项目"]' \
  --output /tmp/signals_q001.json
```

**输出**：包含所有 A/D/E 类信号的 JSON 文件。

## Agent 使用指南

1. 每次 `web_search` 调用后，立即调用 `extract_search_signals.py`
2. 将提取的信号合并到搜索结果对象的 `extracted_signals` 字段
3. 追加到 `raw/search_results.jsonl`
4. 批次完成后更新 manifest 中的信号统计
5. Phase 5 时 Agent 只需补充 B/F 类信号，无需重复 A/D/E 类