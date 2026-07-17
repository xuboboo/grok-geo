# 信任栈评分

## 目标

从 5 个维度综合评估品牌在 AI 引擎眼中的**整体可信度**——AI 引擎不仅看内容质量，还通过多层信号判断品牌是否值得信任和引用。

## 5 层信任模型

### Layer 1: 技术信任（Technical Trust）— 权重 25%

AI 引擎能否**无障碍访问和解析**品牌内容。

| 检查项 | 分值 | 来源 |
|--------|------|------|
| robots.txt 允许 AI 爬虫 | /5 | site-readiness-checklist §1 |
| llms.txt 存在且质量良好 | /4 | site-readiness-checklist §2 |
| HTTPS 正常 | /3 | 基础安全 |
| 页面加载可被 AI 解析（非纯 JS 渲染） | /3 | 负面信号 §7 |
| 结构化数据存在 | /5 | site-readiness-checklist §3 |
| sitemap 存在且可访问 | /3 | 基础发现 |
| CDN/WAF 未阻断 AI 爬虫 | /2 | crawler-log-analysis |

**总分：/25 → 归一化到 0-100**

### Layer 2: 身份信任（Identity Trust）— 权重 20%

品牌是否有**清晰、一致、可验证的身份**。

| 检查项 | 分值 |
|--------|------|
| 品牌名在官网一致出现 ≥ 3 次 | /4 |
| Knowledge Graph 链接（Wikipedia/Wikidata/LinkedIn/Crunchbase） | /6 |
| About 页面存在且内容完整 | /4 |
| 团队/创始人信息可查 | /3 |
| 联系方式和地址存在 | /3 |

**总分：/20 → 归一化到 0-100**

### Layer 3: 社交信任（Social Trust）— 权重 20%

品牌是否有**第三方背书和社交证明**。

| 检查项 | 分值 |
|--------|------|
| 被 ≥ 3 个独立域名引用（earned media） | /6 |
| 客户评价或案例存在 | /5 |
| 行业媒体或权威站点提及 | /5 |
| 社交媒体存在且活跃 | /2 |
| 用户生成内容（评论、论坛讨论） | /2 |

**总分：/20 → 归一化到 0-100**

### Layer 4: 学术/权威信任（Academic Trust）— 权重 15%

品牌内容是否具有**学术级别的可信度**。

| 检查项 | 分值 |
|--------|------|
| 引用权威数据源（研究报告、政府数据） | /5 |
| 包含可验证的统计数据 | /4 |
| 作者具备相关领域专业背景 | /3 |
| 内容经过事实核查 | /2 |
| 无虚假或误导性声明 | /4 |

**总分：/18 → 归一化到 0-100**

### Layer 5: 一致性信任（Consistency Trust）— 权重 20%

品牌信息在**不同来源间是否一致**。

| 检查项 | 分值 |
|--------|------|
| 官网信息与第三方描述一致 | /5 |
| 不同页面间信息一致（价格、功能、版本） | /4 |
| 跨平台信息一致（搜索结果 vs 官网） | /4 |
| 时间一致性（无过期信息与新信息矛盾） | /4 |
| 无实体混淆（品牌与竞品信息不混淆） | /3 |

**总分：/20 → 归一化到 0-100**

## 综合评分

```text
trust_stack_score = technical × 0.25
                  + identity × 0.20
                  + social × 0.20
                  + academic × 0.15
                  + consistency × 0.20
```

## 综合等级

| 等级 | 分数段 | 含义 |
|------|--------|------|
| **A** | 90-100 | 高度可信，AI 优先引用 |
| **B** | 75-89 | 可信，多数信号到位 |
| **C** | 60-74 | 基础可信，需加强部分层 |
| **D** | 40-59 | 信任信号不足，引用概率低 |
| **F** | 0-39 | 严重缺乏信任信号 |

## 输出结构

```json
{
  "trust_stack_score": 72,
  "grade": "C",
  "layers": {
    "technical": {"score": 80, "max": 100, "weight": 0.25, "issues": ["llms.txt 缺失"]},
    "identity": {"score": 65, "max": 100, "weight": 0.20, "issues": ["无 Knowledge Graph 链接"]},
    "social": {"score": 70, "max": 100, "weight": 0.20, "issues": ["仅 2 个独立域名引用"]},
    "academic": {"score": 85, "max": 100, "weight": 0.15, "issues": []},
    "consistency": {"score": 60, "max": 100, "weight": 0.20, "issues": ["定价页面与博客信息不一致"]}
  },
  "weakest_layer": "consistency",
  "strongest_layer": "academic",
  "recommendations": [
    "创建 llms.txt 文件",
    "在 About 页面添加 Wikipedia/LinkedIn 链接",
    "统一各页面的定价信息"
  ]
}
```

## Agent 使用指南

1. 在 Phase 2（Brand Research）阶段计算，复用已有检查结果
2. **技术层**直接复用 `site_readiness` 的结果
3. **身份层**从品牌研究阶段提取
4. **社交层**从搜索结果中的第三方引用统计
5. **学术层**从已知事实和引用来源推断
6. **一致性层**从搜索结果与官网信息对比推断
7. 结果写入 `metrics.json` → `trust_stack`