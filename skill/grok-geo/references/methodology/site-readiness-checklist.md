# 站点 GEO 就绪检查清单

Agent 在 Phase 2（Brand Research）阶段对品牌官网执行以下检查。每项仅需一次 `web_search` + 目标 URL 的 HTML 解析即可完成，不需要持续监测或 CI/CD 集成。

---

## 1. AI 爬虫访问（Robots.txt）— /18

检查品牌 `robots.txt` 中对以下 AI 爬虫的 `Allow` / `Disallow` 状态：

| 层级 | Bot 名称 | 覆盖引擎 |
|------|----------|----------|
| Training | `GPTBot`, `CCBot`, `anthropic-ai`, `ClaudeBot` | OpenAI, Common Crawl, Anthropic |
| Search | `OAI-SearchBot`, `PerplexityBot`, `Google-Extended` | ChatGPT Search, Perplexity, Gemini |
| User | `ChatGPT-User`, `Claude-Web`, `cohere-ai` | 对话式代理 |

**评分规则：**
- 全部 Allow = 18
- Search 层全部 Allow = 12
- 仅 GPTBot Allow = 6
- 全部 Disallow 或不存在 = 0

---

## 2. llms.txt 存在与质量 — /18

检查 `/.well-known/llms.txt` 或 `/llms.txt`：

| 检查项 | 分值 |
|--------|------|
| 文件存在且可访问 | +4 |
| 包含 H1 标题 + blockquote 摘要 | +3 |
| 包含结构化分区（## 章节） | +3 |
| 包含相关链接（产品页、文档、定价） | +3 |
| 同时存在 `llms-full.txt` | +3 |
| 总字数 ≥ 200 | +2 |

---

## 3. 结构化数据（JSON-LD Schema）— /16

检查页面 `<head>` 中的 JSON-LD：

| Schema 类型 | 分值 | 说明 |
|-------------|------|------|
| `WebSite` 或 `Organization` | +4 | 基础实体定义 |
| `Product` 或 `SoftwareApplication` | +4 | 产品描述 |
| `FAQPage` | +3 | FAQ 结构（AI 最爱引用） |
| `Article` 或 `BlogPosting` | +3 | 内容页面 |
| 属性 ≥ 5 个（name, url, description, sameAs, ...） | +2 | 丰富度加分 |

---

## 4. Meta 标签完整性 — /14

| 检查项 | 分值 |
|--------|------|
| `<title>` 存在且 ≤ 60 字符 | +3 |
| `<meta name="description">` 存在且 ≤ 160 字符 | +3 |
| `<link rel="canonical">` 存在 | +2 |
| Open Graph（og:title, og:description, og:image）完整 | +3 |
| `<html lang="...">` 指定语言 | +2 |
| Twitter Card 标签 | +1 |

---

## 5. 内容可引用性 — /12

| 检查项 | 分值 |
|--------|------|
| 页面有且仅有一个 `<h1>` | +2 |
| 包含可验证的统计数据或指标 | +3 |
| 包含外部引用链接（≥ 2 个权威来源） | +3 |
| 标题层级合理（h1 → h2 → h3 无跳跃） | +2 |
| 包含列表或表格 | +2 |

---

## 6. 品牌实体一致性 — /10

| 检查项 | 分值 |
|--------|------|
| 品牌名在页面中出现 ≥ 3 次 | +2 |
| Knowledge Graph 链接（Wikipedia / Wikidata / LinkedIn / Crunchbase） | +3 |
| 存在 `/about` 页面 | +2 |
| 包含地理位置信号（address / geo / areaServed） | +1 |
| 主题权威性（同一域名下 ≥ 5 篇相关文章） | +2 |

---

## 7. 技术信号 — /6

| 检查项 | 分值 |
|--------|------|
| `<html lang="...">` 正确 | +2 |
| 存在 RSS/Atom feed | +2 |
| 页面 `dateModified` 或 `datePublished` 在 12 个月内 | +2 |

---

## 8. AI 发现端点 — /6

| 检查项 | 分值 |
|--------|------|
| `/.well-known/ai.txt` 存在 | +2 |
| `/ai/summary.json` 存在 | +2 |
| `/ai/faq.json` 存在 | +2 |

---

## 评分汇总

| 等级 | 分数段 | 含义 |
|------|--------|------|
| **Excellent** | 86-100 | AI 爬虫无障碍、结构化数据完整、内容高度可引用 |
| **Good** | 68-85 | 基础设施到位，部分优化空间 |
| **Foundation** | 36-67 | 需要显著改进才能被 AI 有效引用 |
| **Critical** | 0-35 | AI 爬虫可能无法读取或理解网站内容 |

---

## 使用说明

1. Agent 在 Phase 2 品牌研究阶段执行此检查
2. 每项检查结果写入 `report.json` 的 `site_readiness` 字段
3. 检查失败的项目自动纳入机会生成（Phase 7）的输入
4. 总分写入 `metrics.json` 的 `site_readiness_score` 字段
5. **此检查为辅助信息**，不影响核心 GEO 品牌可见度指标