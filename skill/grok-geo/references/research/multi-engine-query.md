# Multi-Engine Query — 多引擎真实 API 查询

## 设计目标

替代单一 `web_search` 模拟搜索，直接向多个 AI 引擎发送真实查询，获取原生 AI 回答。
覆盖 8 个 AI 搜索平台，支持同步/异步批量查询。

## 支持的 AI 引擎

| 引擎 | API 类型 | 认证方式 | 状态 |
|------|----------|----------|------|
| **ChatGPT Search** | OpenAI API (gpt-4o-search / gpt-5) | API Key | 稳定 |
| **Perplexity** | Perplexity API (sonar / sonar-pro) | API Key | 稳定 |
| **Claude Search** | Anthropic API (claude-sonnet-4 / claude-opus-4) | API Key | 稳定 |
| **Gemini** | Google AI API (gemini-2.5-pro) | API Key | 稳定 |
| **Google AI Overviews** | SerpAPI / 直接抓取 | API Key / Agent | 需代理 |
| **Microsoft Copilot** | Bing Chat API / SerpAPI | API Key | 需代理 |
| **Grok** | xAI API (grok-3) | API Key | 稳定 |
| **DeepSeek** | DeepSeek API (deepseek-chat) | API Key | 稳定 |

## 查询流程

```
┌─────────────────────────────────────────────────┐
│  Question Queue (from Phase 3)                  │
│  questions.json → [{id, text, template_type}]   │
└──────────────────────┬──────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────┐
│  Engine Router                                  │
│  - 根据引擎可用性分配查询                         │
│  - 负载均衡: 每个引擎分配不同问题子集              │
│  - 优先级: ChatGPT > Perplexity > Claude > Gemini│
└──────────────────────┬──────────────────────────┘
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
   ┌──────────┐ ┌──────────┐ ┌──────────┐
   │ ChatGPT  │ │Perplexity│ │  Claude  │  ... (8 engines)
   │ Adapter  │ │ Adapter  │ │ Adapter  │
   └────┬─────┘ └────┬─────┘ └────┬─────┘
        │            │            │
        ▼            ▼            ▼
   ┌─────────────────────────────────────────────┐
   │  Response Normalizer                        │
   │  - 统一响应格式                               │
   │  - 提取: answer_text, citations[], sources[] │
   │  - 平台特征标注                               │
   └──────────────────────┬──────────────────────┘
                          │
                          ▼
   ┌─────────────────────────────────────────────┐
   │  Cross-Engine Aggregator                    │
   │  - 跨引擎引用一致性                           │
   │  - 平台间品牌可见度对比                        │
   │  - 引用来源重叠分析                            │
   └─────────────────────────────────────────────┘
```

## 引擎适配器接口

每个适配器实现统一接口：

```python
class EngineAdapter:
    """统一的 AI 引擎查询接口。"""
    
    engine_name: str           # "chatgpt" / "perplexity" / "claude" / ...
    requires_api_key: bool     # 是否需要 API key
    supports_citations: bool   # 引擎是否返回引用信息
    max_batch_size: int        # 单次最大并发数
    rate_limit_rpm: int        # 每分钟请求限制
    
    def query(self, question: str, **kwargs) -> EngineResponse:
        """发送单个查询，返回标准化响应。"""
        ...
    
    def batch_query(self, questions: List[str], **kwargs) -> List[EngineResponse]:
        """批量查询（带速率限制）。"""
        ...
    
    def health_check(self) -> bool:
        """检查引擎是否可用。"""
        ...
```

## 统一响应格式

```json
{
  "engine": "chatgpt",
  "model": "gpt-4o-search-preview",
  "question_id": "q_001",
  "question_text": "What are the best project management tools?",
  "answer_text": "...",
  "citations": [
    {
      "title": "Page Title",
      "url": "https://example.com/page",
      "domain": "example.com",
      "snippet": "relevant snippet..."
    }
  ],
  "sources": ["example.com", "another.com"],
  "response_metadata": {
    "tokens_used": 1234,
    "latency_ms": 2500,
    "has_inline_citations": true,
    "response_format": "narrative",
    "list_detected": true,
    "table_detected": false
  },
  "query_timestamp": "2026-07-17T12:00:00Z",
  "status": "success",
  "error": null
}
```

## 引擎分配策略

### Standard 模式 (30 questions × 2 variants = 60 queries)

| 引擎 | 分配数 | 理由 |
|------|--------|------|
| ChatGPT | 18 (30%) | 市场份额最大，必须覆盖 |
| Perplexity | 15 (25%) | 引用最密集，高价值 |
| Claude | 12 (20%) | 分析深度最好 |
| Gemini | 9 (15%) | Google 生态覆盖 |
| Grok/DeepSeek | 6 (10%) | 补充覆盖 |

### Quick 模式 (10 questions × 1 variant = 10 queries)

| 引擎 | 分配数 |
|------|--------|
| ChatGPT | 4 |
| Perplexity | 3 |
| Claude | 2 |
| Gemini | 1 |

## 降级策略

当 API 不可用时的降级顺序：

1. **API 直接调用** → 成功则使用原生响应
2. **web_search 模拟** → 使用 agent 的 web_search 获取搜索结果
3. **offline_import** → 使用用户提供的历史数据

降级时在响应中标注 `"fallback": "web_search"` 或 `"fallback": "offline"`。

## 跨引擎分析

### 引用一致性指数 (Cross-Engine Citation Consistency)

```
CEC = 1 - (unique_cited_domains_across_all_engines / total_cited_domains)
```

- CEC = 1.0: 所有引擎引用相同来源（高度一致）
- CEC = 0.0: 每个引擎引用完全不同的来源（高度分散）

### 平台偏好矩阵

每个品牌在不同引擎中的表现差异：

| 维度 | ChatGPT | Perplexity | Claude | Gemini |
|------|---------|------------|--------|--------|
| 提及率 | 80% | 90% | 70% | 75% |
| 推荐率 | 60% | 70% | 50% | 55% |
| 引用率 | 40% | 80% | 30% | 45% |

### 引擎特异性发现

不同引擎的引用特征差异：
- **ChatGPT**: 偏好权威来源（G2, Capterra, 媒体报道）
- **Perplexity**: 引用密度最高，偏爱学术和长文内容
- **Claude**: 偏好结构化内容（列表、表格、定义）
- **Gemini**: 偏好 Google 生态内来源（YouTube, Google Reviews）

## 安全约束

- API key 通过环境变量传递，不写入文件
- 每个查询独立，不泄露跨查询上下文
- 不存储原始 API 响应中的用户数据
- 速率限制严格遵守各引擎 API 条款
- 查询内容不包含恶意指令或注入尝试