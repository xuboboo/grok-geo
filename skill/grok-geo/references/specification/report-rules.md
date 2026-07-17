# 报告生成规则

## 必须输出的文件

| 文件 | 格式 | 内容 |
| --- | --- | --- |
| report.md | Markdown | 完整诊断报告（17 个章节） |
| report.json | JSON | 结构化报告数据 |
| questions.csv | CSV | 问题地图及分析 |
| evidence.csv | CSV | 证据索引 |
| opportunities.csv | CSV | 内容机会列表 |
| manifest.json | JSON | 运行元数据和状态 |

## Markdown 报告章节

1. 执行摘要（品牌提及率、推荐率、可见度分）
2. 品牌和诊断范围
3. 方法说明
4. 搜索样本统计
5. 核心指标表格
6. 用户问题地图
7. 品牌出现和推荐分析
8. 竞争对手分析
9. 引用来源分析
10. 自有官网引用情况
11. 错误和过期信息
12. 内容缺口
13. 十项优先机会（最多 10 条）
14. 五份内容 Brief（最多 5 份）
15. 三十天行动计划
16. 方法限制声明
17. 证据索引

## 关键约束

- 机会数 ≤ 10
- Brief 数 ≤ 5
- 必须包含方法限制声明（LIMITATION_TEXT）
- 报告中所有 URL 必须可追溯到 raw/search_results.jsonl 或用户输入
- 不得包含禁止的承诺性语言（FORBIDDEN_PROMISE_PATTERNS）
- 外部事实引用必须紧邻真实 URL

## 校验流程

`validate_report.py` 检查：
1. 所有必须文件是否存在
2. report.json 是否符合 schema
3. 机会数和 Brief 数是否超限
4. 方法限制声明是否存在
5. 报告中 URL 是否可追溯
6. 指标数值是否与 metrics.json 一致
7. 是否包含禁止的承诺性语言