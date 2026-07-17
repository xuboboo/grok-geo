# 负面信号检测

## 目标

检测品牌官网中**降低 AI 引用概率的负面信号**——这些信号不会直接导致 AI 不引用你，但会显著降低被选中的优先级。

## 8 种负面信号

### 1. CTA 过载（CTA Overload）

| 检测项 | 严重度 | 说明 |
|--------|--------|------|
| 页面首屏 ≥ 3 个 CTA 按钮 | high | AI 视为"推销页面"而非信息页面 |
| 每 200 词出现 ≥ 1 个行动号召 | medium | 过度商业化降低可信度 |
| 弹窗覆盖主要内容 | high | 阻断内容提取 |

**信号词：** "立即购买"、"免费试用"、"限时优惠"、"Sign Up Now"、"Get Started Free"

### 2. 内容稀薄（Thin Content）

| 检测项 | 严重度 | 说明 |
|--------|--------|------|
| 主内容 < 300 词 | high | 信息量不足以被引用 |
| 有效内容占比 < 40%（排除导航/页脚/侧边栏） | medium | 噪音比过高 |
| 无 H2/H3 子标题 | medium | 缺乏结构化信息 |

### 3. 关键词堆砌（Keyword Stuffing）

| 检测项 | 严重度 | 说明 |
|--------|--------|------|
| 同一关键词在 200 词内出现 ≥ 5 次 | high | AI 识别为低质量内容 |
| 隐藏文本（font-size:0, display:none） | critical | 直接触发负面判断 |
| 不自然的关键词变体堆叠 | medium | 降低可读性 |

### 4. 缺少作者信息（Missing Author）

| 检测项 | 严重度 | 说明 |
|--------|--------|------|
| 文章无作者署名 | medium | AI 无法验证信息来源 |
| 无作者页面或团队介绍 | medium | 缺乏实体权威性 |
| 无 `author` Schema 标记 | low | 技术信号缺失 |

### 5. 模板化内容（Boilerplate Content）

| 检测项 | 严重度 | 说明 |
|--------|--------|------|
| 页脚/侧边栏占页面 > 30% | medium | 主内容被稀薄化 |
| 大量重复的免责声明 | low | 占用有效内容空间 |
| 自动生成的模板文本未定制 | medium | 缺乏独特性 |

### 6. 社交证明缺失（Missing Social Proof）

| 检测项 | 严重度 | 说明 |
|--------|--------|------|
| 无客户评价或案例 | medium | 缺乏第三方验证 |
| 无合作伙伴/客户 logo | low | 缺乏可信度信号 |
| 无行业认证或奖项 | medium | 权威性不足 |

### 7. 技术障碍（Technical Barriers）

| 检测项 | 严重度 | 说明 |
|--------|--------|------|
| JS 渲染阻断内容加载 | high | AI 爬虫无法获取内容 |
| 登录墙/付费墙 | critical | 完全阻断引用 |
| 验证码/CAPTCHA | critical | 阻断爬取 |
| iframe 嵌套主内容 | high | 内容不可见 |

### 8. 可信度信号缺失（Missing Trust Signals）

| 检测项 | 严重度 | 说明 |
|--------|--------|------|
| 无 HTTPS | critical | 基本安全信号缺失 |
| 无隐私政策页面 | medium | 合规性信号缺失 |
| 无联系方式 | medium | 可追溯性不足 |
| 域名年龄 < 1 年 | low | 新域名信任度低 |

## 评分模型（0-100，越高越好/越少负面信号）

```text
negative_signal_score = 100
  - critical 信号 × 15（每发现一个）
  - high 信号 × 10
  - medium 信号 × 5
  - low 信号 × 2
```

分数裁剪到 [0, 100]。

## 输出结构

```json
{
  "negative_signal_score": 65,
  "signal_count": 5,
  "signals": [
    {
      "type": "cta_overload",
      "severity": "high",
      "evidence": "首屏发现 4 个 CTA 按钮",
      "deduction": 10,
      "recommendation": "将首屏 CTA 减少到 1-2 个，优先展示信息内容"
    },
    {
      "type": "missing_author",
      "severity": "medium",
      "evidence": "文章无作者署名",
      "deduction": 5,
      "recommendation": "添加作者简介和 Schema.org/author 标记"
    }
  ],
  "recommendations": [
    "移除首屏多余 CTA，改为信息优先布局",
    "为所有文章添加作者署名",
    "增加客户案例和第三方评价"
  ]
}
```

## 评分等级

| 等级 | 分数段 | 含义 |
|------|--------|------|
| **Clean** | 86-100 | 几乎无负面信号 |
| **Minor Issues** | 68-85 | 少量可修复的负面信号 |
| **Problematic** | 36-67 | 多个负面信号影响引用 |
| **Severe** | 0-35 | 严重负面信号，大幅降低引用概率 |

## Agent 使用指南

1. 在 Phase 2（Brand Research）阶段，通过搜索结果 snippet 和已知事实检测
2. 不做全站爬取，仅通过搜索结果推断
3. critical 和 high 信号立即写入机会生成的高优先级输入
4. 检测结果写入 `report.json` → `negative_signals`