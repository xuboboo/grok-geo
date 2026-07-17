# GEO 品牌诊断报告：示例科技

- Run ID: `geo_offline_demo_00000001`
- 生成时间: 2026-07-17T17:40:25Z
- 模式: offline_import
- Skill: grok-geo v5.0.0

## 1. 执行摘要

本次诊断覆盖 10 个问题，成功搜索 10/10。
目标品牌提及率 40.0% (4/10)（Wilson 95% [16.8%, 68.7%]），推荐率 60.0% (3/5)，可见度分 21.36184210526316。

## 2. 品牌和诊断范围

- 品牌：示例科技
- 官网：https://example.com
- 行业：项目管理软件
- 目标客户：20至200人的研发和项目团队
- 地区：中国大陆
- 竞争对手：竞争品牌A、竞争品牌B

## 3. 方法说明

- 所有数值指标由确定性脚本计算。
- 引用必须来自实际搜索结果或用户输入。

## 4. 搜索样本

- 问题数：10
- 搜索结果：10
- 成功：10
- 失败：0
- 成功率：100.0%

## 5. 核心指标

| 指标 | 值 | 分子/分母 | Wilson 95% |
| --- | --- | --- | --- |
| 提及率 | 40.00% | 4/10 | [16.8%, 68.7%] |
| 推荐率 | 60.00% | 3/5 | [23.1%, 88.2%] |
| 自有引用率 | 30.00% | 3/10 | [10.8%, 60.3%] |
| 第三方支持率 | 0.00% | 0/10 | [0.0%, 27.8%] |
| 问题覆盖率 | 40.00% | 4/10 | [16.8%, 68.7%] |
| 可见度分 | 21.36184210526316 | 1.6235/7.6000 | n/a |
| 推荐份额 | 19.07% | 1.5910000000000002/8.343499999999999 | n/a |
| 信息准确率 | 50.00% | correct+0.5*partial / verifiable | n/a |

## 6. 用户问题地图

- [✓] `q-001` (recommendation, bv=90): 适合五十人研发团队的项目管理软件有哪些？
- [·] `q-002` (recommendation, bv=85): 中小企业项目管理工具怎么选？
- [✓] `q-003` (recommendation, bv=88): 研发团队协作平台推荐
- [·] `q-004` (category_awareness, bv=60): 项目管理软件和问题跟踪工具有什么区别？
- [✓] `q-005` (purchase, bv=92): 支持私有化部署的项目管理系统有哪些？
- [·] `q-006` (comparison, bv=80): 竞争品牌A和竞争品牌B哪个更适合研发团队？
- [·] `q-007` (use_case, bv=75): 敏捷研发场景下如何选择协作工具？
- [·] `q-008` (trust_risk, bv=70): 项目管理软件的数据安全要注意什么？
- [✓] `q-009` (brand_fact, bv=65): 示例科技支持私有化部署吗？
- [·] `q-010` (support, bv=55): 项目管理工具售后和服务响应一般如何评估？

## 7. 品牌出现和推荐分析

目标品牌在 4 个有效问题中被提及。
- q-001: recommended rank=3
- q-003: weakly_recommended rank=None
- q-005: recommended rank=1
- q-009: neutral_mention rank=None

## 8. 竞争对手分析

- 竞争品牌A: 提及 6，推荐 5
- 竞争品牌B: 提及 4，推荐 4

## 9. 引用来源分析

总引用数：14
- community: 1
- competitor_owned: 1
- earned_media: 5
- institutional: 1
- owned: 3
- unknown: 3

## 10. 自有官网引用情况

自有域名引用率：30.0% (3/10)
- [示例科技官网](https://example.com/product)
- [私有化部署说明](https://example.com/private-deployment)
- [官方私有化页](https://example.com/private-deployment)

## 11. 错误和过期信息

- [incorrect/high] 示例科技不支持私有化部署。 来源: https://example.com/private-deployment
- [correct/high] 示例科技支持私有化部署。 来源: https://example.com/private-deployment
- [partially_correct/medium] 示例科技适合需要私有化部署的团队。 来源: https://example.com/product

## 12. 内容缺口

基于高价值问题中品牌缺席、竞品占优、自有引用不足与事实错误识别内容缺口。

## 13. 十项优先机会

### opp-001: 建设适合五十人研发团队的选购指南
- 类型: missing_recommendation_content
- 缺口: 目标品牌在部分高价值推荐问题中出现不足或排名靠后。
- 竞品证据: 竞争品牌A在多次回答中被首选推荐。
- 推荐资产: website_buying_guide
- 总分: 80.25

### opp-002: 发布与竞争品牌A/B的客观对比页
- 类型: competitor_comparison_gap
- 缺口: 对比类问题几乎只出现竞品。
- 竞品证据: A/B 对比页被第三方媒体引用。
- 推荐资产: comparison_page
- 总分: 72.75

### opp-003: 补强私有化部署权威说明页
- 类型: incorrect_claim_correction
- 缺口: 搜索回答中出现“不支持私有化”的错误信息。
- 竞品证据: 竞品混合部署信息更常被引用。
- 推荐资产: official_capability_page
- 总分: 72.6

### opp-004: 提升官网在推荐答案中的被引概率
- 类型: owned_citation_gap
- 缺口: 自有域名引用率偏低。
- 竞品证据: 竞品官网定价页被引用。
- 推荐资产: structured_product_pages
- 总分: 70.0

## 14. 五份内容 Brief

### 五十人研发团队如何选择项目管理软件
- 渠道: website
- 受众: 研发负责人
- 目标: 进入推荐型AI搜索答案
- 人工审核: True

### 示例科技私有化部署能力说明
- 渠道: website
- 受众: IT负责人
- 目标: 纠正错误事实并提升权威引用
- 人工审核: True

## 15. 三十天行动计划

- 第1周：修复高风险错误声明，补齐官网核心事实页。
- 第2周：发布 Top3 机会对应的选购/对比内容。
- 第3周：补充第三方可引用证据与案例。
- 第4周：用相同问题样本复测提及率与推荐率。

## 16. 方法限制

本次结果基于指定时间、问题样本、地区和当前搜索运行环境。AI 搜索回答可能随时间、模型、平台、用户上下文和搜索索引变化。本报告不代表所有 AI 产品、所有账号或全部用户的绝对排名，也不保证采取建议后能进入 AI 推荐结果。

## 17. 证据索引

- [研发团队项目管理软件对比](https://media.example.org/pm-compare?utm_source=test) (q=q-001, search_result)
- [示例科技官网](https://example.com/product) (q=q-001, search_result)
- [中小企业工具指南](https://news.example.org/sme-tools) (q=q-002, search_result)
- [竞争品牌A官网](https://competitor-a.example/pricing) (q=q-002, search_result)
- [协作平台推荐2026](https://blog.review.example/collab-2026) (q=q-003, search_result)
- [PM vs Issue Tracker](https://zh.wikipedia.org/wiki/项目管理软件) (q=q-004, search_result)
- [私有化部署说明](https://example.com/private-deployment) (q=q-005, search_result)
- [部署方式对比](https://community.zhihu.com/question/pm-private) (q=q-005, search_result)
- [A vs B 对比](https://media.example.org/a-vs-b) (q=q-006, search_result)
- [敏捷工具选择](https://news.example.org/agile-tools) (q=q-007, search_result)
- [安全基线](https://www.nist.gov/publications) (q=q-008, search_result)
- [第三方转述](https://forum.example.org/thread/123) (q=q-009, search_result)
- [SLA 指南](https://directory.example.org/sla-guide) (q=q-010, search_result)
