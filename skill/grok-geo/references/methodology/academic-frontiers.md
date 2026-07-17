# Academic Frontiers — 学术前沿研究

## 设计目标

将最新 GEO 学术研究转化为可操作的优化策略。
确保 skill 的方法论始终基于经过同行评审的科学发现。

## 核心研究发现

### 1. Princeton GEO 框架 (KDD 2024)

**9 种优化方法**（按效果排序）：

| 方法 | 可见度提升 | 实现方式 |
|------|-----------|----------|
| Cite Sources | +115.0% | 引用权威来源 |
| Quotation Addition | +41.3% | 添加专家引语 |
| Statistics Addition | +40.4% | 添加统计数据 |
| Fluency Optimization | +29.3% | 优化文本流畅度 |
| Authoritative Content | +28.0% | 使用权威语调 |
| Technical Terms | +22.5% | 使用专业术语 |
| Easy-to-Understand | +18.4% | 简化表达 |
| Unique Words | +14.7% | 使用独特词汇 |
| Schema Markup | +12.8% | 结构化数据标记 |

### 2. 结构特征工程 (2026)

**关键发现**: 内容的结构特征对 AI 引用选择有显著影响。

| 结构特征 | 影响权重 | 说明 |
|----------|----------|------|
| 标题层级清晰 | 0.85 | H1→H2→H3 连续层级 |
| 段落自包含 | 0.78 | 每段可独立理解 |
| 列表/表格结构 | 0.72 | 结构化信息呈现 |
| 定义式开头 | 0.68 | 首句即定义/结论 |
| 锚点句密度 | 0.65 | 每 200-300 词一个主题句 |
| 引用密度 | 0.60 | 每 500 词至少 1 个引用 |
| FAQ 格式 | 0.55 | 问答对结构 |
| 术语表 | 0.45 | dl/dd 定义列表 |

### 3. 引用选择到引用吸收 (2026)

**两阶段模型**:

```
阶段 1: 引用选择 (Citation Selection)
  AI 模型从候选来源中选择引用
  影响因素: 权威性、相关性、新鲜度、结构化程度

阶段 2: 引用吸收 (Citation Absorption)
  AI 模型将引用内容整合到回答中
  影响因素: 可引用性、自包含性、事实密度
```

**优化策略**:
- 阶段 1 优化: 提升来源权威性（外链、媒体引用、知识图谱）
- 阶段 2 优化: 提升内容可引用性（统计数据、引语、定义式段落）

### 4. GEO 综述 (Jul 2026, 45 项研究)

**共识性发现**:

1. **结构化数据是基础**: Schema markup 的效果在所有研究中一致正向
2. **引用权威来源最有效**: Cite Sources 方法的提升幅度最大且最稳定
3. **内容质量 > 技术优化**: 内容本身的质量比技术 SEO 更重要
4. **多引擎差异显著**: 不同 AI 引擎的引用偏好差异很大
5. **时间维度重要**: 内容新鲜度对引用率有显著影响

**争议性发现**:

1. **llms.txt 效果不确定**: 部分研究显示正面效果，部分显示无显著影响
2. **关键词密度**: 过度优化可能产生负面效果
3. **长内容 vs 短内容**: 取决于查询类型，无一致结论

## 可操作转化

### 从学术到实践的映射

| 学术发现 | 实践动作 | 已实现版本 |
|----------|----------|-----------|
| Cite Sources (+115%) | 添加权威来源引用 | v1.3 citability |
| Quotation (+41%) | 添加专家引语 | v1.3 citability |
| Statistics (+40%) | 添加量化数据 | v1.3 citability |
| Fluency (+29%) | 优化文本流畅度 | v1.3 citability |
| 结构特征 | 标题层级/段落结构 | v1.3 negative_signals |
| 两阶段引用 | 权威性 + 可引用性 | v1.3 trust_stack |
| Schema markup | JSON-LD 完整性 | v1.9 geo_lint |
| 内容新鲜度 | 更新频率监控 | v1.2 freshness |
| 多引擎差异 | 跨引擎分析 | v2.0 multi_engine |

### 新增优化建议

基于最新研究，以下优化策略尚未被现有版本覆盖：

1. **Authoritative Content Score** — 权威语调评分
   - 检测内容是否使用权威表达（"研究表明"、"数据显示"、"专家建议"）
   - 避免不确定表达（"可能"、"也许"、"据说"）

2. **Technical Terms Density** — 专业术语密度
   - 检测行业专业术语的使用频率
   - 平衡专业性与可理解性

3. **Unique Vocabulary Score** — 独特词汇评分
   - 检测内容是否使用差异化表达
   - 避免模板化、千篇一律的表述

4. **Definition Opening Pattern** — 定义式开头模式
   - 检测段落首句是否为定义或结论
   - 优化 RAG 分块时的信息密度

## 输出格式

```json
{
  "schema_version": "1.0",
  "research_basis": [
    {
      "paper": "string",
      "venue": "string",
      "year": 0,
      "key_finding": "string",
      "implemented_in": "vX.Y"
    }
  ],
  "optimization_methods": [
    {
      "method": "string",
      "visibility_lift": 0.0,
      "implementation_status": "implemented|partial|missing",
      "action": "string"
    }
  ],
  "emerging_strategies": [...]
}
```