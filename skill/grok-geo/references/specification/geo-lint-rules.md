# GEO Lint Rules — 发布前合规检查

## 设计目标

在内容发布前自动检测 GEO 合规问题，覆盖 6 大维度、92 条规则。
输出结构化的 lint 报告，区分 ERROR / WARNING / INFO 三级严重度。

## 规则分类

### 1. 结构化数据规则 (Schema Rules) — 22 条

| 规则 ID | 严重度 | 检查项 |
|---------|--------|--------|
| SCHEMA-001 | ERROR | 页面必须包含至少一种 JSON-LD 结构化数据 |
| SCHEMA-002 | ERROR | Organization schema 必须包含 name, url, logo |
| SCHEMA-003 | ERROR | Product schema 必须包含 name, description, brand |
| SCHEMA-004 | WARNING | FAQPage schema 建议包含至少 3 个 Q&A 对 |
| SCHEMA-005 | WARNING | Article schema 必须包含 author, datePublished |
| SCHEMA-006 | ERROR | 所有 schema 的 @context 必须为 https://schema.org |
| SCHEMA-007 | WARNING | 建议包含 BreadcrumbList schema |
| SCHEMA-008 | WARNING | LocalBusiness schema 必须包含 address, telephone |
| SCHEMA-009 | INFO | SoftwareApplication schema 建议包含 applicationCategory |
| SCHEMA-010 | ERROR | schema 不能包含空值字段 |
| SCHEMA-011 | WARNING | 建议使用 aggregateRating 而非单一 review |
| SCHEMA-012 | INFO | 建议为视频内容添加 VideoObject schema |
| SCHEMA-013 | WARNING | HowTo schema 步骤必须包含 text 字段 |
| SCHEMA-014 | INFO | 建议使用 sameAs 链接到社交账号 |
| SCHEMA-015 | ERROR | 价格字段必须包含有效数字 |
| SCHEMA-016 | WARNING | 建议包含 offers → availability 字段 |
| SCHEMA-017 | INFO | 建议使用 isBasedOn 标注引用来源 |
| SCHEMA-018 | WARNING | Review schema 必须包含 author 和 reviewRating |
| SCHEMA-019 | ERROR | Event schema 必须包含 name, startDate, location |
| SCHEMA-020 | WARNING | 建议使用 speakable 标注适合语音搜索的段落 |
| SCHEMA-021 | INFO | 建议使用 hasPart 标注文章的关键段落 |
| SCHEMA-022 | WARNING | 多语言页面必须使用 inLanguage 字段 |

### 2. AI 爬虫可达性规则 (Crawler Rules) — 18 条

| 规则 ID | 严重度 | 检查项 |
|---------|--------|--------|
| CRAWL-001 | ERROR | robots.txt 不能阻断 GPTBot |
| CRAWL-002 | ERROR | robots.txt 不能阻断 ClaudeBot |
| CRAWL-003 | ERROR | robots.txt 不能阻断 Google-Extended |
| CRAWL-004 | ERROR | robots.txt 不能阻断 PerplexityBot |
| CRAWL-005 | WARNING | robots.txt 不能阻断 Bingbot（Copilot 数据源） |
| CRAWL-006 | WARNING | 建议允许 CCBot（Common Crawl，训练数据源） |
| CRAWL-007 | ERROR | 必须存在 llms.txt 或 llms-full.txt |
| CRAWL-008 | WARNING | llms.txt 应包含品牌名称和核心描述 |
| CRAWL-009 | WARNING | llms.txt 应列出主要产品/服务 URL |
| CRAWL-010 | INFO | 建议提供 llms-full.txt 包含完整站点地图 |
| CRAWL-011 | ERROR | meta robots 不能包含 noindex（关键页面） |
| CRAWL-012 | WARNING | X-Robots-Tag 不能阻断 AI 爬虫 |
| CRAWL-013 | INFO | 建议使用 IndexNow 提交新内容 |
| CRAWL-014 | WARNING | 页面加载时间不应超过 3 秒（影响爬取深度） |
| CRAWL-015 | INFO | 建议在 sitemap.xml 中标注 lastmod |
| CRAWL-016 | WARNING | 关键页面不应依赖 JavaScript 渲染核心内容 |
| CRAWL-017 | ERROR | 页面必须可无 cookie 访问 |
| CRAWL-018 | INFO | 建议设置合理的 crawl-delay |

### 3. 内容可引用性规则 (Citability Rules) — 20 条

| 规则 ID | 严重度 | 检查项 |
|---------|--------|--------|
| CITE-001 | ERROR | 页面必须包含明确的事实性声明（非纯营销话术） |
| CITE-002 | WARNING | 建议包含统计数据或量化指标 |
| CITE-003 | WARNING | 建议包含可引用的专家引语 |
| CITE-004 | ERROR | 声明必须有来源归属（数据源、研究、标准） |
| CITE-005 | WARNING | 建议使用列表/表格结构化信息 |
| CITE-006 | WARNING | 段落长度建议 40-150 词（RAG 友好） |
| CITE-007 | INFO | 建议每 300 词包含一个锚点句（主题句） |
| CITE-008 | WARNING | 不能有超过 50% 的内容为 CTA（行动号召） |
| CITE-009 | ERROR | 不能包含关键词堆砌（密度 > 3%） |
| CITE-010 | WARNING | 建议包含作者信息和发布日期 |
| CITE-011 | WARNING | 不能为纯模板化内容（缺乏差异化） |
| CITE-012 | INFO | 建议包含「定义」类型的开头段落 |
| CITE-013 | WARNING | 标题层级必须连续（h1→h2→h3，不能跳级） |
| CITE-014 | ERROR | 每个页面必须有且仅有一个 h1 |
| CITE-015 | WARNING | 建议在标题中包含实体名称 |
| CITE-016 | INFO | 建议使用 dl/dd 标签定义术语 |
| CITE-017 | WARNING | 图片必须包含描述性 alt 文本 |
| CITE-018 | INFO | 建议使用 time 标签标注日期 |
| CITE-019 | WARNING | 外部链接应指向权威来源（.edu, .gov, 行业媒体） |
| CITE-020 | INFO | 建议在内容中使用 blockquote 标注引语 |

### 4. 实体一致性规则 (Entity Rules) — 14 条

| 规则 ID | 严重度 | 检查项 |
|---------|--------|--------|
| ENTITY-001 | ERROR | 品牌名称在页面中拼写必须一致 |
| ENTITY-002 | WARNING | 建议在首段明确声明品牌身份 |
| ENTITY-003 | ERROR | schema 中的 brand name 必须与页面显示一致 |
| ENTITY-004 | WARNING | 建议使用 sameAs 链接到 Wikidata/Wikipedia |
| ENTITY-005 | INFO | 建议创建 entity.json 机器可读文件 |
| ENTITY-006 | WARNING | 品牌描述不应超过 160 字符（AI 摘要友好） |
| ENTITY-007 | INFO | 建议使用 about 和 mentions 标注实体关系 |
| ENTITY-008 | WARNING | 产品名称不应与竞品高度相似 |
| ENTITY-009 | INFO | 建议在 knowledge panel 中声明创始人/CEO |
| ENTITY-010 | ERROR | 联系信息（邮箱/电话）必须可验证 |
| ENTITY-011 | WARNING | 建议声明成立年份和总部位置 |
| ENTITY-012 | INFO | 建议列出关键客户/合作伙伴作为社会证明 |
| ENTITY-013 | WARNING | 社交媒体链接必须可访问 |
| ENTITY-014 | INFO | 建议使用 hasCredential 标注认证/合规信息 |

### 5. 多模态优化规则 (Multimodal Rules) — 10 条

| 规则 ID | 严重度 | 检查项 |
|---------|--------|--------|
| MULTI-001 | WARNING | 图片必须包含 alt 文本（AI 图像搜索） |
| MULTI-002 | WARNING | 视频必须包含字幕/转录文本 |
| MULTI-003 | INFO | 建议为产品图添加 ImageObject schema |
| MULTI-004 | INFO | 建议使用 picture 元素提供多种分辨率 |
| MULTI-005 | WARNING | 长内容建议包含目录（Table of Contents） |
| MULTI-006 | INFO | 建议使用 section 标签分隔内容块 |
| MULTI-007 | WARNING | 表格必须包含 th 标签（表头） |
| MULTI-008 | INFO | 建议使用 figure/figcaption 标注图表 |
| MULTI-009 | INFO | 建议为音频内容提供 PodcastEpisode schema |
| MULTI-010 | WARNING | 页面必须支持移动端渲染 |

### 6. 国际化规则 (i18n Rules) — 8 条

| 规则 ID | 严重度 | 检查项 |
|---------|--------|--------|
| I18N-001 | ERROR | 多语言页面必须声明 hreflang |
| I18N-002 | WARNING | hreflang 必须包含 x-default |
| I18N-003 | ERROR | lang 属性必须与页面语言一致 |
| I18N-004 | WARNING | 建议为每个语言版本提供独立 URL |
| I18N-005 | INFO | 建议在 llms.txt 中声明支持的语言 |
| I18N-006 | WARNING | 翻译内容不应使用机器翻译痕迹明显的表述 |
| I18N-007 | INFO | 建议使用 schema 的 inLanguage 字段 |
| I18N-008 | WARNING | 日期/数字格式应符合目标地区习惯 |

## 评分模型

### 维度权重

| 维度 | 权重 | 理由 |
|------|------|------|
| Schema | 0.25 | 结构化数据直接影响 AI 理解和引用 |
| Crawler | 0.20 | 爬虫可达性是被引用的前提 |
| Citability | 0.25 | 内容质量决定引用概率 |
| Entity | 0.15 | 实体一致性影响品牌识别 |
| Multimodal | 0.08 | 多模态优化提升覆盖面 |
| i18n | 0.07 | 国际化扩展市场覆盖 |

### 严重度扣分

| 严重度 | 扣分 |
|--------|------|
| ERROR | -5 分/条 |
| WARNING | -2 分/条 |
| INFO | -0 分/条（仅记录） |

### 评级

| 分数 | 等级 | 含义 |
|------|------|------|
| 90-100 | A | GEO 就绪，可直接发布 |
| 75-89 | B | 良好，修复 WARNING 后发布 |
| 60-74 | C | 基础，需要修复部分 ERROR |
| 40-59 | D | 不合格，需要重大修改 |
| 0-39 | F | 严重不合格，不建议发布 |

## 输出格式

```json
{
  "schema_version": "1.0",
  "tool": "geo-lint",
  "tool_version": "1.9.0",
  "linted_at": "ISO-8601",
  "target_url": "string",
  "score": 0-100,
  "grade": "A|B|C|D|F",
  "dimension_scores": {
    "schema": { "score": 0-100, "pass": int, "fail": int, "warn": int },
    "crawler": { "score": 0-100, "pass": int, "fail": int, "warn": int },
    "citability": { "score": 0-100, "pass": int, "fail": int, "warn": int },
    "entity": { "score": 0-100, "pass": int, "fail": int, "warn": int },
    "multimodal": { "score": 0-100, "pass": int, "fail": int, "warn": int },
    "i18n": { "score": 0-100, "pass": int, "fail": int, "warn": int }
  },
  "issues": [
    {
      "rule_id": "SCHEMA-001",
      "dimension": "schema",
      "severity": "ERROR",
      "message": "string",
      "evidence": "string",
      "fix_suggestion": "string"
    }
  ],
  "summary": {
    "total_rules_checked": 92,
    "errors": 0,
    "warnings": 0,
    "info": 0,
    "pass_rate": 0.0
  }
}
```