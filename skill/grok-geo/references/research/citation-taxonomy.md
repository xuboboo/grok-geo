# 引用分类规则

## Source Types

| source_type | 说明 | 示例 |
| --- | --- | --- |
| owned | 品牌自有官网 | brand-website.com/blog |
| competitor_owned | 竞品官网 | competitor.com |
| earned_media | 第三方媒体/评测 | 36kr.com, techcrunch.com |
| social | 社交平台 | twitter.com, weibo.com |
| community | 社区论坛 | reddit.com, v2ex.com |
| commerce | 电商平台/比价 | amazon.com, jd.com |
| institutional | 官方/学术/政府 | gov.cn, edu.cn |
| directory | 目录/导航站 | producthunt.com |
| unknown | 无法分类 | 其他 |

## 分类优先级

1. **品牌域名匹配**：URL 域名与 brand.website 或 brand.competitors 匹配
2. **用户域名映射**：input 中提供的自定义域名分类
3. **机构规则**：.gov/.edu/.org 等已知机构域名
4. **URL/标题规则**：包含 "review"、"comparison"、"reddit" 等关键词
5. **模型判断**：Agent 基于上下文判断
6. **兜底**：unknown

## URL 规范化

分类前必须先规范化：
- 删除跟踪参数：utm_source, utm_medium, utm_campaign, utm_term, utm_content, gclid, fbclid, yclid, mc_cid, mc_eid
- 去除 fragment (#...)
- 小写 host
- 删除默认端口 (:443, :80)
- 去除尾部斜杠

## 引用对象

```json
{
  "question_id": "q-001",
  "original_url": "https://Example.com/path?utm_source=x&id=1#frag",
  "canonical_url": "https://example.com/path?id=1",
  "domain": "example.com",
  "title": "页面标题",
  "source_type": "owned",
  "supports_target_brand": true
}
```