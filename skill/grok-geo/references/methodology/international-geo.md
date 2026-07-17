# International GEO — 国际化与多语言 GEO 优化

## 设计目标

确保品牌在不同语言和地区的 AI 搜索中具有一致、高质量的可见度。
覆盖 hreflang、多语言 schema、区域化内容策略、本地化实体声明。

## 国际化评估维度

### 1. 多语言技术基础 (i18n Technical) — 30 分

| 检查项 | 分值 | 说明 |
|--------|------|------|
| hreflang 标签完整 | 8 | 每个语言版本有正确的 hreflang |
| x-default 声明 | 4 | 默认语言版本指向正确 |
| lang 属性正确 | 4 | html lang 与内容语言一致 |
| 独立 URL 结构 | 4 | 子目录 / 子域名 / ccTLD |
| inLanguage schema | 3 | 结构化数据中声明语言 |
| 字符编码 UTF-8 | 3 | 正确的字符编码 |
| 日期/数字本地化 | 2 | 符合目标地区格式 |
| 货币本地化 | 2 | 本地货币显示 |

### 2. 多语言内容质量 (Content Quality) — 30 分

| 检查项 | 分值 | 说明 |
|--------|------|------|
| 人工翻译质量 | 10 | 非机器翻译痕迹 |
| 文化本地化 | 6 | 适应当地文化表达 |
| 关键词本地化 | 6 | 使用当地搜索习惯 |
| 本地案例/引用 | 4 | 当地客户案例和引用 |
| 本地媒体引用 | 4 | 当地权威媒体引用 |

### 3. 区域实体声明 (Regional Entity) — 20 分

| 检查项 | 分值 | 说明 |
|--------|------|------|
| 本地地址 | 5 | 目标地区办公地址 |
| 本地联系方式 | 4 | 本地电话/邮箱 |
| 本地社交账号 | 4 | 当地主流社交平台 |
| 本地知识库注册 | 4 | 当地 Wikipedia/Wikidata |
| 本地行业目录 | 3 | 当地行业目录注册 |

### 4. AI 引擎区域覆盖 (AI Engine Coverage) — 20 分

| 检查项 | 分值 | 说明 |
|--------|------|------|
| ChatGPT 多语言 | 5 | 在目标语言中的可见度 |
| Perplexity 多语言 | 5 | 引用密度 |
| Gemini 多语言 | 4 | Google 生态覆盖 |
| 本地 AI 引擎 | 3 | DeepSeek(中文) / Yandex Alice(俄文) 等 |
| 引擎间一致性 | 3 | 跨语言的引用一致性 |

## 区域优先级矩阵

| 区域 | 主要语言 | 关键 AI 引擎 | 本地知识库 |
|------|----------|-------------|-----------|
| 北美 | en | ChatGPT, Perplexity, Gemini | Wikipedia EN |
| 欧洲 | de, fr, es, it | ChatGPT, Perplexity, Peec | Wikipedia 多语言 |
| 中国 | zh | DeepSeek, 文心一言, 通义千问 | 百度百科, 知乎 |
| 日本 | ja | ChatGPT, Gemini | Wikipedia JA |
| 韩国 | ko | ChatGPT, Gemini, Clova | Naver 知识 |
| 东南亚 | th, vi, id | ChatGPT, Gemini | 本地 Wikipedia |
| 中东 | ar | ChatGPT, Gemini | 阿拉伯语 Wikipedia |
| 拉美 | pt-BR, es | ChatGPT, Perplexity | 葡/西语 Wikipedia |

## 输出格式

```json
{
  "schema_version": "1.0",
  "i18n_score": 0-100,
  "grade": "A|B|C|D|F",
  "target_regions": ["en-US", "zh-CN", "ja-JP"],
  "dimensions": {
    "technical": { "score": 0-30, "items": [...] },
    "content_quality": { "score": 0-30, "items": [...] },
    "regional_entity": { "score": 0-20, "items": [...] },
    "ai_coverage": { "score": 0-20, "items": [...] }
  },
  "per_language_scores": { "en": 85, "zh": 60, "ja": 45 },
  "action_items": [...]
}
```