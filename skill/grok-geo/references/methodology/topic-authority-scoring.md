# 主题权威评分

## 目标

评估品牌官网在特定主题上的**深度、广度和互联性**。AI 引擎更倾向于引用"主题权威"网站，而非孤立页面。

## 评分模型（0-100）

### 1. 实体覆盖密度（/30）

检查品牌官网（通过 `web_search` 的 site: 查询）在目标行业主题上的内容量：

| 检查项 | 分值 | 方法 |
|--------|------|------|
| 目标关键词在 title/H1 中出现的独立页面数 ≥ 5 | +10 | `web_search("site:domain.com 主题关键词")` |
| 存在"支柱页"（≥ 2000 字的综合指南） | +8 | 检查搜索结果中的长摘要 |
| 存在 ≥ 3 篇支持文章（子主题） | +7 | 同域不同 URL |
| 有 FAQ 或 Q&A 结构内容 | +5 | 检查搜索结果 snippet |

### 2. 内部互联性（/25）

| 检查项 | 分值 | 方法 |
|--------|------|------|
| 支柱页链接到 ≥ 3 篇子文章 | +8 | 搜索结果中引用的 URL 互相有链接关系 |
| 子文章链接回支柱页 | +7 | 同上 |
| 面包屑或分类层级清晰 | +5 | URL 结构分析（/category/topic/page） |
| 相关文章推荐区存在 | +5 | 搜索结果 snippet 中出现"相关阅读"/"推荐阅读" |

### 3. 外部引用权威（/25）

| 检查项 | 分值 | 方法 |
|--------|------|------|
| 被 ≥ 3 个独立域名引用（earned media） | +10 | 搜索结果中非品牌域名的引用 |
| 被行业媒体或权威站点引用 | +8 | 域名匹配已知媒体列表 |
| 引用内容包含具体数据或评价 | +7 | snippet 中有数字或评价词 |

### 4. 内容新鲜度（/20）

| 检查项 | 分值 | 方法 |
|--------|------|------|
| 最近一篇文章 ≤ 90 天 | +8 | 搜索结果中的日期 |
| 最近 6 个月有 ≥ 3 篇更新 | +7 | 多个日期 |
| 历史文章有更新标记 | +5 | snippet 中出现"更新于"/"updated" |

## 输出结构

```json
{
  "topic": "项目管理软件",
  "domain": "example.com",
  "total_score": 62,
  "band": "foundation",
  "breakdown": {
    "entity_coverage": { "score": 22, "max": 30, "details": {...} },
    "internal_linking": { "score": 15, "max": 25, "details": {...} },
    "external_authority": { "score": 12, "max": 25, "details": {...} },
    "freshness": { "score": 13, "max": 20, "details": {...} }
  },
  "pillar_pages": [
    {"url": "https://example.com/guide", "title": "...", "word_count_estimate": 3500}
  ],
  "supporting_articles": [
    {"url": "https://example.com/feature-a", "title": "..."}
  ],
  "recommendations": [
    "创建支柱页：'项目管理软件完整选购指南'",
    "为 3 个子主题各写一篇深度文章",
    "在支柱页和子文章之间建立双向链接"
  ]
}
```

## 评分等级

| 等级 | 分数段 | 含义 |
|------|--------|------|
| **Excellent** | 86-100 | 主题权威性极强，AI 高概率引用 |
| **Good** | 68-85 | 有较好的主题覆盖，需加强互联 |
| **Foundation** | 36-67 | 基础内容存在但深度不足 |
| **Critical** | 0-35 | 几乎没有主题相关内容 |

## Agent 使用指南

1. 此检查在 **Phase 7（机会生成）** 前执行，作为机会排序的输入
2. 主题权威分低的领域自动提升 `competitive_gap` 和 `brand_absence` 分数
3. `pillar_pages` 和 `supporting_articles` 直接写入 content_brief 的 `outline` 字段
4. **不做全站爬取**，仅通过 3-5 次 `web_search("site:domain.com ...")` 查询抽样评估