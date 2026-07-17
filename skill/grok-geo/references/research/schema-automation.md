# Schema Automation — AI 可读文件自动生成

## 设计目标

从品牌输入配置自动生成 5 种 AI 可读文件，使 AI 引擎能高效发现、理解和引用品牌信息。

## 生成文件清单

### 1. llms.txt

AI 时代的 `robots.txt`。告诉 AI 爬虫「这个站点是什么、有哪些关键页面」。

```
# Brand Name
> Brief description of what the brand does (≤160 chars)

## Products
- [Product A](https://example.com/product-a): One-line description
- [Product B](https://example.com/product-b): One-line description

## Key Pages
- [About](https://example.com/about)
- [Pricing](https://example.com/pricing)
- [Documentation](https://example.com/docs)
- [Blog](https://example.com/blog)

## Contact
- Email: contact@example.com
- Twitter: @brand

## Last Updated
2026-07-17
```

### 2. llms-full.txt

完整版本，包含站点地图和详细产品信息。

### 3. entity.json

机器可读的品牌实体文件（源自 schema.org/Organization）。

```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "Brand Name",
  "url": "https://example.com",
  "logo": "https://example.com/logo.png",
  "description": "Brief description",
  "foundingDate": "2020-01-01",
  "founders": [
    { "@type": "Person", "name": "Founder Name" }
  ],
  "sameAs": [
    "https://twitter.com/brand",
    "https://linkedin.com/company/brand",
    "https://en.wikipedia.org/wiki/Brand"
  ],
  "contactPoint": {
    "@type": "ContactPoint",
    "email": "contact@example.com",
    "contactType": "customer service"
  },
  "address": {
    "@type": "PostalAddress",
    "addressCountry": "US"
  }
}
```

### 4. brand.json

品牌级 AI 上下文文件，比 entity.json 更侧重于 AI 理解。

```json
{
  "name": "Brand Name",
  "tagline": "One-line value proposition",
  "industry": "SaaS",
  "founded": "2020",
  "hq": "San Francisco, CA",
  "employees": "50-200",
  "target_customer": "SMB teams",
  "core_value_props": [
    "Value prop 1",
    "Value prop 2"
  ],
  "competitors": [
    "Competitor A",
    "Competitor B"
  ],
  "pricing_model": "freemium",
  "key_differentiators": [
    "Differentiator 1",
    "Differentiator 2"
  ],
  "social_proof": {
    "customers": ["Customer A", "Customer B"],
    "awards": ["Award 1"],
    "metrics": { "users": "10000+", "uptime": "99.9%" }
  }
}
```

### 5. aeo.json

AI Engine Optimization 专用配置文件。

```json
{
  "schema_version": "1.0",
  "brand": "Brand Name",
  "preferred_citation_name": "Brand Name",
  "preferred_citation_source": "https://example.com/about",
  "faq_entries": [
    { "q": "What is Brand?", "a": "Brand is..." },
    { "q": "How much does Brand cost?", "a": "Brand starts at..." }
  ],
  "key_facts": [
    "Founded in 2020",
    "Serves 10,000+ customers",
    "SOC 2 Type II certified"
  ],
  "content_priorities": [
    { "topic": "Core Feature 1", "url": "https://example.com/feature-1" },
    { "topic": "Pricing", "url": "https://example.com/pricing" }
  ],
  "supported_languages": ["en", "zh", "ja"],
  "last_updated": "2026-07-17"
}
```

## 生成规则

### 数据源优先级

1. 用户提供的 `known_facts`（最高优先级）
2. 从品牌网站 `web_search` 提取的事实
3. 从 schema.org 结构化数据提取
4. 合理推断（标记为 `inferred: true`）

### 质量约束

- 所有事实必须可追溯到搜索结果或用户输入
- 不得编造客户名称、收入数据或认证信息
- 日期格式统一为 ISO-8601
- URL 必须为有效 HTTP(S) 链接
- 描述文本不超过 160 字符（AI 摘要截断阈值）

### 输出位置

```
<RUN>/output/
  llms.txt
  llms-full.txt
  entity.json
  brand.json
  aeo.json
```

## 验证规则

生成后自动验证：

1. **llms.txt**: 至少包含品牌名、描述、3 个关键 URL
2. **entity.json**: 必须通过 JSON-LD 验证，包含 name, url, @type
3. **brand.json**: 必须包含 name, industry, target_customer
4. **aeo.json**: 必须包含 preferred_citation_name 和至少 2 个 key_facts
5. **交叉一致性**: 所有文件中的品牌名必须一致