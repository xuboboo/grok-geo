# Entity SEO & Knowledge Graph — 实体 SEO 与知识图谱优化

## 设计目标

确保品牌实体在 AI 训练数据、知识图谱和结构化数据中具有一致、完整、权威的存在。
AI 引擎通过实体解析来理解「这个品牌是谁、做什么、为什么值得推荐」。

## 实体 SEO 三层模型

```
┌─────────────────────────────────────────────────┐
│  Layer 3: AI 引擎实体解析                         │
│  ChatGPT / Perplexity / Claude / Gemini 如何     │
│  将你的品牌解析为可引用的实体                       │
└──────────────────────┬──────────────────────────┘
                       │ 依赖
┌──────────────────────┴──────────────────────────┐
│  Layer 2: 知识图谱注册                            │
│  Wikidata / Wikipedia / Google Knowledge Panel   │
│  / Crunchbase / LinkedIn 等权威知识库              │
└──────────────────────┬──────────────────────────┘
                       │ 依赖
┌──────────────────────┴──────────────────────────┐
│  Layer 1: 本地实体声明                            │
│  schema.org JSON-LD / entity.json / brand.json   │
│  / llms.txt / aeo.json / sameAs 链接             │
└─────────────────────────────────────────────────┘
```

## 实体完整性评估维度

### 1. 基础实体声明 (Basic Entity Declaration) — 25 分

| 检查项 | 分值 | 说明 |
|--------|------|------|
| Organization schema 完整 | 5 | name + url + logo + description |
| sameAs 外链 ≥ 3 | 5 | 社交 + 知识库 + 行业目录 |
| entity.json 存在 | 3 | 根目录机器可读文件 |
| brand.json 存在 | 3 | AI 优化品牌上下文 |
| aeo.json 存在 | 3 | AI 引擎优化配置 |
| llms.txt 品牌信息 | 3 | 品牌名 + 描述 + 关键页面 |
| 联系信息可验证 | 3 | 邮箱/电话/地址 |

### 2. 知识图谱注册 (Knowledge Graph Presence) — 25 分

| 检查项 | 分值 | 说明 |
|--------|------|------|
| Wikidata 条目存在 | 8 | 有 Q-ID 的实体条目 |
| Wikipedia 页面存在 | 6 | 非删除、非重定向 |
| Google Knowledge Panel | 4 | 搜索品牌名出现知识面板 |
| Crunchbase/PitchBook | 3 | 商业数据库注册 |
| 行业目录注册 | 2 | G2/Capterra/Trustpilot 等 |
| 垂直知识库 | 2 | 行业特定数据库 |

### 3. 实体关系图谱 (Entity Relationships) — 20 分

| 检查项 | 分值 | 说明 |
|--------|------|------|
| founder → Person 关联 | 4 | 创始人实体链接 |
| product → Organization 关联 | 4 | 产品-品牌关系 |
| competitor → Organization 关联 | 3 | 竞品关系声明 |
| parentOrg / subsidiary | 3 | 母子公司关系 |
| award → Organization | 2 | 获奖记录 |
| knowsAbout → Topic | 2 | 专业领域声明 |
| memberOf → Organization | 2 | 行业协会会员 |

### 4. 实体一致性 (Entity Consistency) — 15 分

| 检查项 | 分值 | 说明 |
|--------|------|------|
| 品牌名跨平台一致 | 5 | 所有平台使用相同名称 |
| 描述语义一致 | 4 | 核心定位在各平台一致 |
| 分类/行业一致 | 3 | 行业标签统一 |
| 关键事实一致 | 3 | 成立年份/总部/员工数一致 |

### 5. 实体权威信号 (Entity Authority) — 15 分

| 检查项 | 分值 | 说明 |
|--------|------|------|
| 外部引用 ≥ 10 个域名 | 5 | 第三方独立引用 |
| 媒体报道 ≥ 3 篇 | 4 | 权威媒体报道 |
| 学术引用 | 3 | 学术论文或研究引用 |
| 政府/标准组织引用 | 3 | 官方机构引用 |

## 评分模型

| 分数 | 等级 | 含义 |
|------|------|------|
| 90-100 | A | 实体权威，在知识图谱中有强存在 |
| 75-89 | B | 实体完整，大部分检查通过 |
| 60-74 | C | 实体基础，需要补充知识图谱注册 |
| 40-59 | D | 实体薄弱，AI 引擎难以正确解析 |
| 0-39 | F | 实体缺失，品牌在 AI 中几乎不存在 |

## 知识图谱优化行动清单

### 优先级 P0（必须）

1. 创建/完善 Wikidata 条目
   - 确保有唯一的 Q-ID
   - 填充所有核心属性（label, description, aliases, instance of, inception, headquarters, official website）
   - 添加 sameAs 链接

2. 完善 Organization schema
   - 包含所有核心属性
   - sameAs 链接到 Wikidata, Wikipedia, 社交账号

3. 创建 entity.json + brand.json + aeo.json
   - 已在 v1.9 的 Schema Automation 中实现

### 优先级 P1（强烈建议）

4. 申请 Google Knowledge Panel
   - 通过 Google 搜索控制面板申请
   - 确保 schema 数据与 Knowledge Panel 一致

5. 注册行业目录
   - G2 / Capterra / Trustpilot / Product Hunt
   - 确保名称和描述一致

6. 建立创始人实体
   - 为创始人创建 Wikidata 条目
   - 在 Organization schema 中添加 founder 关联

### 优先级 P2（建议）

7. 获取媒体报道
   - 争取 ≥3 家权威媒体的独立报道
   - 确保报道中使用一致的品牌名

8. 学术存在
   - 在 Google Scholar 中有可引用的存在
   - 发布白皮书或研究报告

9. 行业协会
   - 加入相关行业协会
   - 在 schema 中声明 memberOf

## AI 引擎实体解析差异

| 引擎 | 实体来源偏好 | 引用偏好 |
|------|-------------|----------|
| ChatGPT | Wikipedia + 媒体报道 + G2 | 权威第三方 |
| Perplexity | 实时搜索 + 学术 + 官网 | 引用密度最高 |
| Claude | 结构化内容 + 官网 + 文档 | 分析深度最好 |
| Gemini | Google 生态 (KP, Maps, Reviews) | Google 来源优先 |
| Grok | X/Twitter + 实时搜索 | 社交信号 |
| DeepSeek | 中文知识库 + 百度百科 | 中文来源 |

## 输出格式

```json
{
  "schema_version": "1.0",
  "entity_score": 0-100,
  "grade": "A|B|C|D|F",
  "dimensions": {
    "basic_declaration": { "score": 0-25, "items": [...] },
    "knowledge_graph": { "score": 0-25, "items": [...] },
    "entity_relationships": { "score": 0-20, "items": [...] },
    "entity_consistency": { "score": 0-15, "items": [...] },
    "entity_authority": { "score": 0-15, "items": [...] }
  },
  "action_items": [
    { "priority": "P0|P1|P2", "action": "string", "impact": "string" }
  ]
}
```