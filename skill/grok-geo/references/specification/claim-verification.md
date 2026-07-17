# 声明校验规则

## Verification 状态

| 状态 | 说明 |
| --- | --- |
| correct | 与已知事实完全一致 |
| partially_correct | 部分正确但有遗漏或不精确 |
| incorrect | 与已知事实矛盾 |
| outdated | 曾经正确但已过时 |
| unsupported | 无法找到支持证据 |
| entity_confusion | 混淆了不同实体的信息 |
| unverifiable | 证据不足，无法判定 |

## 判定要求

- 声明来源必须来自实际搜索结果或用户输入的 known_facts
- 无足够证据时使用 `unverifiable`，而非 `incorrect`
- 模型记忆不得作为事实基准
- 已知事实通过 input.known_facts 提供，包含 statement、source_url、valid_from、valid_to

## 风险级别

### High（高风险，需人工审核）
- 价格信息
- 安全认证
- 核心功能声明
- 地区可用性
- 法律主体信息
- 法律/医疗/金融声明
- 品牌归属混淆

### Medium
- 技术规格
- 性能数据
- 客户数量
- 合作伙伴

### Low
- 通用行业描述
- 产品类别
- 一般性评价

## 声明对象

```json
{
  "claim_id": "C001",
  "question_id": "q-003",
  "claim_text": "示例科技成立于2020年",
  "reference_url": "https://example.com/about",
  "known_fact_match": "支持私有化部署",
  "verification_status": "correct",
  "risk_level": "medium",
  "evidence": "官网关于页面明确标注成立年份"
}
```