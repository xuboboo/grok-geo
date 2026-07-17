# AI 爬虫日志分析指南

## 目标

通过分析网站的服务器访问日志（access log），识别 **AI 爬虫的实际访问行为**——哪些 AI 引擎在爬取品牌网站、爬取频率如何、是否被 CDN/WAF 阻断。

## 适用场景

- 用户提供了 access log 文件（Apache / Nginx 格式）
- 需要验证 robots.txt 配置是否真正生效
- 需要确认 AI 爬虫是否实际访问了目标页面

## AI 爬虫 User-Agent 清单

### 第一梯队：训练 + 搜索爬虫

| User-Agent 标识 | 运营方 | 用途 |
|-----------------|--------|------|
| `GPTBot` | OpenAI | 训练 + 搜索 |
| `OAI-SearchBot` | OpenAI | ChatGPT Search 实时检索 |
| `ChatGPT-User` | OpenAI | 代理式浏览（用户触发） |
| `ClaudeBot` | Anthropic | 训练 + 搜索 |
| `anthropic-ai` | Anthropic | API 爬取 |
| `Claude-Web` | Anthropic | 代理式浏览 |
| `PerplexityBot` | Perplexity | 搜索引用 |
| `Perplexity-User` | Perplexity | 用户触发爬取 |
| `Google-Extended` | Google | Gemini / AI Overviews 训练 |
| `GoogleOther` | Google | 其他 AI 用途 |
| `Gemini` | Google | Gemini 代理浏览 |
| `cohere-ai` | Cohere | 训练 |
| `Bytespider` | ByteDance | 训练（豆包/Coze） |
| `AmazonBot` | Amazon | Alexa / Q 训练 |

### 第二梯队：SEO/数据聚合

| User-Agent 标识 | 运营方 |
|-----------------|--------|
| `CCBot` | Common Crawl |
| `facebookexternalhit` | Meta |
| `Twitterbot` | X/Twitter |
| `LinkedInBot` | LinkedIn |
| `Applebot-Extended` | Apple |

## 日志分析方法

### 单行解析（Apache/Nginx Combined 格式）

```text
203.0.113.42 - - [17/Jul/2026:10:30:15 +0000] "GET /products HTTP/1.1" 200 12345 "https://example.com" "GPTBot/1.0 (+https://openai.com/gptbot)"
```

提取字段：
- IP 地址
- 时间戳
- 请求路径
- HTTP 状态码
- User-Agent

### 分析维度

#### 1. 爬虫访问频率

```json
{
  "crawler_frequency": {
    "GPTBot":          { "hits": 1247, "unique_pages": 89, "last_seen": "2026-07-17" },
    "OAI-SearchBot":   { "hits": 856,  "unique_pages": 45, "last_seen": "2026-07-17" },
    "ClaudeBot":       { "hits": 432,  "unique_pages": 67, "last_seen": "2026-07-16" },
    "PerplexityBot":   { "hits": 321,  "unique_pages": 34, "last_seen": "2026-07-15" },
    "Google-Extended": { "hits": 2890, "unique_pages": 156, "last_seen": "2026-07-17" }
  }
}
```

#### 2. 被爬取最多/最少的页面

```json
{
  "most_crawled": [
    {"path": "/products", "hits": 450, "crawlers": ["GPTBot", "ClaudeBot", "PerplexityBot"]},
    {"path": "/pricing", "hits": 380, "crawlers": ["GPTBot", "OAI-SearchBot"]},
    {"path": "/blog/guide", "hits": 210, "crawlers": ["GPTBot", "ClaudeBot"]}
  ],
  "never_crawled": [
    "/api/docs",
    "/changelog",
    "/case-studies"
  ]
}
```

#### 3. 阻断检测

```json
{
  "blocked_requests": {
    "total": 156,
    "by_status": {
      "403": 89,
      "429": 45,
      "503": 22
    },
    "by_crawler": {
      "GPTBot": 12,
      "ClaudeBot": 87,
      "PerplexityBot": 57
    },
    "blocked_by": "Cloudflare WAF rule",
    "impact": "ClaudeBot 和 PerplexityBot 访问被严重阻断"
  }
}
```

#### 4. 爬取深度

```json
{
  "crawl_depth": {
    "depth_1": { "pages": 15, "crawlers": 4 },
    "depth_2": { "pages": 34, "crawlers": 3 },
    "depth_3_plus": { "pages": 8, "crawlers": 1 },
    "interpretation": "大部分爬虫只访问到第2层，深层内容未被索引"
  }
}
```

## 输出结构

```json
{
  "log_analysis": {
    "period": "2026-06-17 to 2026-07-17",
    "total_requests_analyzed": 15678,
    "ai_crawler_requests": 5746,
    "ai_crawler_ratio": 0.366,
    "crawler_frequency": {...},
    "most_crawled": [...],
    "never_crawled": [...],
    "blocked_requests": {...},
    "crawl_depth": {...},
    "health_score": 72,
    "recommendations": [
      "解除 Cloudflare 对 ClaudeBot 的阻断",
      "将 /case-studies 加入 AI 爬虫允许列表",
      "为深层内容添加 sitemap 条目"
    ]
  }
}
```

## 健康分（Health Score，0-100）

```text
health = 基础分 100
  - 爬虫被阻断扣分（按严重程度 0-40）
  - 高价值页面未被爬取扣分（0-20）
  - 爬取深度不足扣分（0-15）
  - 请求频率异常（过低或过高）扣分（0-15）
  - 非预期状态码比例扣分（0-10）
```

## Agent 使用指南

1. **仅当用户提供 access log 时**才执行此分析（Phase 2 可选步骤）
2. 解析方法：将 log 文件通过 shell 写入临时文件，用 Python 脚本逐行解析
3. 不依赖外部日志分析工具，仅用正则 + 标准库
4. 分析结果写入 `report.json` → `crawler_analysis`
5. 阻断检测结果自动纳入机会生成的高优先级输入
6. **安全**：不从日志中提取任何用户凭据、Cookie 或个人信息