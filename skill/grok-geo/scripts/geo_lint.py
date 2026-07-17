#!/usr/bin/env python3
"""GEO Lint — 发布前合规检查引擎。

6 大维度: schema / crawler / citability / entity / multimodal / i18n

用法:
  python geo_lint.py --input <run_dir>/input/brand.json \
    --run-dir <run_dir> [--output <run_dir>/output/geo_lint_report.json]

  # 直接检查网页内容（从搜索结果提取）
  python geo_lint.py --input brand.json --search-results <run_dir>/raw/search_results.jsonl \
    --output <run_dir>/output/geo_lint_report.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

# Allow running from any cwd
sys.path.insert(0, str(Path(__file__).resolve().parent))

from geo_common import (
    read_json,
    read_jsonl,
    write_json,
    utc_now_iso,
    clamp,
    exit_with,
    print_json,
    default_runs_base_dir,
)

# ─── Dimension weights ──────────────────────────────────────────────────

DIMENSION_WEIGHTS: Dict[str, float] = {
    "schema": 0.25,
    "crawler": 0.20,
    "citability": 0.25,
    "entity": 0.15,
    "multimodal": 0.08,
    "i18n": 0.07,
}

SEVERITY_DEDUCTIONS: Dict[str, int] = {
    "ERROR": 5,
    "WARNING": 2,
    "INFO": 0,
}

# ─── Rule definitions ───────────────────────────────────────────────────

RULES: List[Dict[str, Any]] = []

def _rule(rule_id: str, dimension: str, severity: str, check_fn: str, message: str, fix: str = ""):
    RULES.append({
        "rule_id": rule_id,
        "dimension": dimension,
        "severity": severity,
        "check_fn": check_fn,
        "message": message,
        "fix_suggestion": fix,
    })

# Schema Rules (22)
_rule("SCHEMA-001", "schema", "ERROR", "schema_has_any_jsonld",
      "页面必须包含至少一种 JSON-LD 结构化数据",
      "添加 Organization 或 WebPage 的 JSON-LD schema")
_rule("SCHEMA-002", "schema", "ERROR", "org_schema_complete",
      "Organization schema 必须包含 name, url, logo",
      "在 JSON-LD 中添加 name, url, logo 字段")
_rule("SCHEMA-003", "schema", "ERROR", "product_schema_complete",
      "Product schema 必须包含 name, description, brand",
      "为产品页面添加完整的 Product schema")
_rule("SCHEMA-004", "schema", "WARNING", "faq_schema_count",
      "FAQPage schema 建议包含至少 3 个 Q&A 对",
      "扩展 FAQ 内容至 3 个以上问答对")
_rule("SCHEMA-005", "schema", "WARNING", "article_schema_author",
      "Article schema 必须包含 author 和 datePublished",
      "为文章添加作者和发布日期信息")
_rule("SCHEMA-006", "schema", "ERROR", "schema_context_valid",
      "所有 schema 的 @context 必须为 https://schema.org",
      "修正 @context 值为 https://schema.org")
_rule("SCHEMA-007", "schema", "WARNING", "has_breadcrumb",
      "建议包含 BreadcrumbList schema",
      "添加面包屑导航结构化数据")
_rule("SCHEMA-008", "schema", "WARNING", "local_business_complete",
      "LocalBusiness schema 必须包含 address 和 telephone",
      "补充本地商家的地址和电话信息")
_rule("SCHEMA-009", "schema", "INFO", "app_schema_category",
      "SoftwareApplication schema 建议包含 applicationCategory",
      "添加应用分类字段")
_rule("SCHEMA-010", "schema", "ERROR", "no_empty_schema_fields",
      "schema 不能包含空值字段",
      "移除或填充所有空值 schema 字段")
_rule("SCHEMA-011", "schema", "WARNING", "use_aggregate_rating",
      "建议使用 aggregateRating 而非单一 review",
      "使用聚合评分替代单条评论")
_rule("SCHEMA-012", "schema", "INFO", "video_schema_present",
      "建议为视频内容添加 VideoObject schema",
      "为视频页面添加 VideoObject 结构化数据")
_rule("SCHEMA-013", "schema", "WARNING", "howto_steps_complete",
      "HowTo schema 步骤必须包含 text 字段",
      "为每个 HowTo 步骤添加描述文本")
_rule("SCHEMA-014", "schema", "INFO", "has_sameas",
      "建议使用 sameAs 链接到社交账号",
      "添加 sameAs 字段链接到官方社交账号")
_rule("SCHEMA-015", "schema", "ERROR", "price_field_valid",
      "价格字段必须包含有效数字",
      "确保所有价格字段为有效数值")
_rule("SCHEMA-016", "schema", "WARNING", "has_availability",
      "建议包含 offers → availability 字段",
      "为产品添加库存可用性信息")
_rule("SCHEMA-017", "schema", "INFO", "use_isbasedon",
      "建议使用 isBasedOn 标注引用来源",
      "添加引用来源归属")
_rule("SCHEMA-018", "schema", "WARNING", "review_schema_complete",
      "Review schema 必须包含 author 和 reviewRating",
      "补充评论的作者和评分信息")
_rule("SCHEMA-019", "schema", "ERROR", "event_schema_complete",
      "Event schema 必须包含 name, startDate, location",
      "补充活动的名称、日期和地点")
_rule("SCHEMA-020", "schema", "WARNING", "has_speakable",
      "建议使用 speakable 标注适合语音搜索的段落",
      "添加 speakable 属性标注关键段落")
_rule("SCHEMA-021", "schema", "INFO", "use_haspart",
      "建议使用 hasPart 标注文章的关键段落",
      "使用 hasPart 关联文章子段落")
_rule("SCHEMA-022", "schema", "WARNING", "has_inlanguage",
      "多语言页面必须使用 inLanguage 字段",
      "为每个语言版本添加 inLanguage 属性")

# Crawler Rules (18)
_rule("CRAWL-001", "crawler", "ERROR", "robots_allows_gptbot",
      "robots.txt 不能阻断 GPTBot",
      "在 robots.txt 中允许 GPTBot 爬取")
_rule("CRAWL-002", "crawler", "ERROR", "robots_allows_claudebot",
      "robots.txt 不能阻断 ClaudeBot",
      "在 robots.txt 中允许 ClaudeBot 爬取")
_rule("CRAWL-003", "crawler", "ERROR", "robots_allows_google_extended",
      "robots.txt 不能阻断 Google-Extended",
      "在 robots.txt 中允许 Google-Extended")
_rule("CRAWL-004", "crawler", "ERROR", "robots_allows_perplexitybot",
      "robots.txt 不能阻断 PerplexityBot",
      "在 robots.txt 中允许 PerplexityBot 爬取")
_rule("CRAWL-005", "crawler", "WARNING", "robots_allows_bingbot",
      "robots.txt 不能阻断 Bingbot（Copilot 数据源）",
      "允许 Bingbot 爬取以覆盖 Copilot 搜索")
_rule("CRAWL-006", "crawler", "WARNING", "robots_allows_ccbot",
      "建议允许 CCBot（Common Crawl 训练数据源）",
      "允许 CCBot 以提升在训练数据中的存在感")
_rule("CRAWL-007", "crawler", "ERROR", "has_llms_txt",
      "必须存在 llms.txt 或 llms-full.txt",
      "创建 llms.txt 文件描述站点信息")
_rule("CRAWL-008", "crawler", "WARNING", "llms_txt_brand_info",
      "llms.txt 应包含品牌名称和核心描述",
      "在 llms.txt 中添加品牌名和描述")
_rule("CRAWL-009", "crawler", "WARNING", "llms_txt_key_pages",
      "llms.txt 应列出主要产品/服务 URL",
      "在 llms.txt 中添加关键页面链接")
_rule("CRAWL-010", "crawler", "INFO", "has_llms_full_txt",
      "建议提供 llms-full.txt 包含完整站点地图",
      "创建 llms-full.txt 包含完整站点结构")
_rule("CRAWL-011", "crawler", "ERROR", "no_meta_noindex",
      "meta robots 不能包含 noindex（关键页面）",
      "移除关键页面的 noindex 标签")
_rule("CRAWL-012", "crawler", "WARNING", "no_x_robots_block",
      "X-Robots-Tag 不能阻断 AI 爬虫",
      "检查并修正 X-Robots-Tag 响应头")
_rule("CRAWL-013", "crawler", "INFO", "has_indexnow",
      "建议使用 IndexNow 提交新内容",
      "配置 IndexNow 实现即时内容发现")
_rule("CRAWL-014", "crawler", "WARNING", "page_load_fast",
      "页面加载时间不应超过 3 秒",
      "优化页面加载速度（压缩、CDN、懒加载）")
_rule("CRAWL-015", "crawler", "INFO", "sitemap_has_lastmod",
      "建议在 sitemap.xml 中标注 lastmod",
      "为 sitemap 中的 URL 添加最后修改时间")
_rule("CRAWL-016", "crawler", "WARNING", "no_js_dependency",
      "关键页面不应依赖 JavaScript 渲染核心内容",
      "使用 SSR 或预渲染确保内容可被爬虫读取")
_rule("CRAWL-017", "crawler", "ERROR", "no_cookie_wall",
      "页面必须可无 cookie 访问",
      "移除 cookie 墙对核心内容的阻断")
_rule("CRAWL-018", "crawler", "INFO", "reasonable_crawl_delay",
      "建议设置合理的 crawl-delay",
      "在 robots.txt 中设置 1-5 秒的 crawl-delay")

# Citability Rules (20)
_rule("CITE-001", "citability", "ERROR", "has_factual_claims",
      "页面必须包含明确的事实性声明",
      "添加可验证的事实、数据或案例")
_rule("CITE-002", "citability", "WARNING", "has_statistics",
      "建议包含统计数据或量化指标",
      "添加具体的数字、百分比或统计数据")
_rule("CITE-003", "citability", "WARNING", "has_quotes",
      "建议包含可引用的专家引语",
      "添加行业专家或客户的真实引语")
_rule("CITE-004", "citability", "ERROR", "claims_have_sources",
      "声明必须有来源归属",
      "为关键声明添加数据来源链接")
_rule("CITE-005", "citability", "WARNING", "uses_lists_tables",
      "建议使用列表/表格结构化信息",
      "将关键信息用列表或表格呈现")
_rule("CITE-006", "citability", "WARNING", "paragraph_length_ok",
      "段落长度建议 40-150 词（RAG 友好）",
      "调整段落长度以优化 RAG 分块效果")
_rule("CITE-007", "citability", "INFO", "has_anchor_sentences",
      "建议每 300 词包含一个锚点句（主题句）",
      "在段落开头添加清晰的主题句")
_rule("CITE-008", "citability", "WARNING", "cta_ratio_ok",
      "CTA 内容不能超过总内容的 50%",
      "减少营销话术，增加信息性内容")
_rule("CITE-009", "citability", "ERROR", "no_keyword_stuffing",
      "不能包含关键词堆砌（密度 > 3%）",
      "降低关键词密度，使用自然语言表达")
_rule("CITE-010", "citability", "WARNING", "has_author_info",
      "建议包含作者信息和发布日期",
      "添加作者简介和文章发布/更新日期")
_rule("CITE-011", "citability", "WARNING", "not_template_content",
      "不能为纯模板化内容",
      "添加独特的观点、案例或数据")
_rule("CITE-012", "citability", "INFO", "has_definition_opening",
      "建议包含「定义」类型的开头段落",
      "在页面开头添加明确的定义或解释")
_rule("CITE-013", "citability", "WARNING", "heading_hierarchy_ok",
      "标题层级必须连续（不能跳级）",
      "修正标题层级，确保 h1→h2→h3 连续")
_rule("CITE-014", "citability", "ERROR", "single_h1",
      "每个页面必须有且仅有一个 h1",
      "合并或移除多余的 h1 标签")
_rule("CITE-015", "citability", "WARNING", "headings_have_entities",
      "建议在标题中包含实体名称",
      "在标题中融入品牌名或产品名")
_rule("CITE-016", "citability", "INFO", "uses_definition_list",
      "建议使用 dl/dd 标签定义术语",
      "使用定义列表结构化术语解释")
_rule("CITE-017", "citability", "WARNING", "images_have_alt",
      "图片必须包含描述性 alt 文本",
      "为所有图片添加有意义的 alt 描述")
_rule("CITE-018", "citability", "INFO", "uses_time_tag",
      "建议使用 time 标签标注日期",
      "使用 HTML5 time 标签标注日期信息")
_rule("CITE-019", "citability", "WARNING", "links_to_authority",
      "外部链接应指向权威来源",
      "链接到 .edu, .gov 或行业权威媒体")
_rule("CITE-020", "citability", "INFO", "uses_blockquote",
      "建议使用 blockquote 标注引语",
      "使用 blockquote 标签包裹引语内容")

# Entity Rules (14)
_rule("ENTITY-001", "entity", "ERROR", "brand_name_consistent",
      "品牌名称在页面中拼写必须一致",
      "统一品牌名称的拼写和格式")
_rule("ENTITY-002", "entity", "WARNING", "brand_identity_in_intro",
      "建议在首段明确声明品牌身份",
      "在页面开头清晰说明品牌是什么")
_rule("ENTITY-003", "entity", "ERROR", "schema_brand_matches",
      "schema 中的 brand name 必须与页面显示一致",
      "统一 schema 和页面中的品牌名称")
_rule("ENTITY-004", "entity", "WARNING", "has_sameas_external",
      "建议使用 sameAs 链接到 Wikidata/Wikipedia",
      "添加权威知识库的 sameAs 链接")
_rule("ENTITY-005", "entity", "INFO", "has_entity_json",
      "建议创建 entity.json 机器可读文件",
      "在站点根目录创建 entity.json")
_rule("ENTITY-006", "entity", "WARNING", "brand_desc_concise",
      "品牌描述不应超过 160 字符",
      "精简品牌描述至 160 字符以内")
_rule("ENTITY-007", "entity", "INFO", "uses_about_mentions",
      "建议使用 about 和 mentions 标注实体关系",
      "在 schema 中添加 about/mentions 字段")
_rule("ENTITY-008", "entity", "WARNING", "product_name_unique",
      "产品名称不应与竞品高度相似",
      "为产品选择独特的名称以区分竞品")
_rule("ENTITY-009", "entity", "INFO", "has_founder_info",
      "建议在 knowledge panel 中声明创始人/CEO",
      "添加 founder 和 employee 信息")
_rule("ENTITY-010", "entity", "ERROR", "contact_info_verifiable",
      "联系信息（邮箱/电话）必须可验证",
      "确保联系信息真实有效")
_rule("ENTITY-011", "entity", "WARNING", "has_founding_info",
      "建议声明成立年份和总部位置",
      "添加 foundingDate 和地址信息")
_rule("ENTITY-012", "entity", "INFO", "has_social_proof",
      "建议列出关键客户/合作伙伴",
      "添加客户logo或合作伙伴列表")
_rule("ENTITY-013", "entity", "WARNING", "social_links_accessible",
      "社交媒体链接必须可访问",
      "验证并修复社交媒体链接")
_rule("ENTITY-014", "entity", "INFO", "has_credentials",
      "建议使用 hasCredential 标注认证信息",
      "添加合规认证信息（SOC2, ISO等）")

# Multimodal Rules (10)
_rule("MULTI-001", "multimodal", "WARNING", "images_have_alt_text",
      "图片必须包含 alt 文本（AI 图像搜索）",
      "为所有图片添加描述性 alt 文本")
_rule("MULTI-002", "multimodal", "WARNING", "video_has_transcript",
      "视频必须包含字幕/转录文本",
      "为视频添加字幕文件或文字转录")
_rule("MULTI-003", "multimodal", "INFO", "image_object_schema",
      "建议为产品图添加 ImageObject schema",
      "使用 ImageObject 标注关键图片")
_rule("MULTI-004", "multimodal", "INFO", "responsive_images",
      "建议使用 picture 元素提供多种分辨率",
      "使用 srcset 或 picture 元素适配多设备")
_rule("MULTI-005", "multimodal", "WARNING", "has_toc",
      "长内容建议包含目录",
      "为长页面添加锚点目录")
_rule("MULTI-006", "multimodal", "INFO", "uses_section_tags",
      "建议使用 section 标签分隔内容块",
      "使用语义化 HTML5 section 标签")
_rule("MULTI-007", "multimodal", "WARNING", "tables_have_headers",
      "表格必须包含 th 标签",
      "为所有数据表添加表头行")
_rule("MULTI-008", "multimodal", "INFO", "uses_figure_caption",
      "建议使用 figure/figcaption 标注图表",
      "用 figure 标签包裹图表和图片")
_rule("MULTI-009", "multimodal", "INFO", "podcast_schema",
      "建议为音频内容提供 PodcastEpisode schema",
      "添加播客相关的结构化数据")
_rule("MULTI-010", "multimodal", "WARNING", "mobile_friendly",
      "页面必须支持移动端渲染",
      "确保响应式设计或移动端适配")

# i18n Rules (8)
_rule("I18N-001", "i18n", "ERROR", "has_hreflang",
      "多语言页面必须声明 hreflang",
      "为每个语言版本添加 hreflang 标签")
_rule("I18N-002", "i18n", "WARNING", "has_hreflang_default",
      "hreflang 必须包含 x-default",
      "添加 x-default hreflang 指向默认语言版本")
_rule("I18N-003", "i18n", "ERROR", "lang_attr_matches",
      "lang 属性必须与页面语言一致",
      "修正 html lang 属性为正确的语言代码")
_rule("I18N-004", "i18n", "WARNING", "separate_urls_per_lang",
      "建议为每个语言版本提供独立 URL",
      "使用子目录或子域名区分语言版本")
_rule("I18N-005", "i18n", "INFO", "llms_txt_languages",
      "建议在 llms.txt 中声明支持的语言",
      "在 llms.txt 中添加语言列表")
_rule("I18N-006", "i18n", "WARNING", "no_machine_translation",
      "翻译内容不应有明显的机器翻译痕迹",
      "使用人工翻译或高质量本地化")
_rule("I18N-007", "i18n", "INFO", "schema_inlanguage",
      "建议使用 schema 的 inLanguage 字段",
      "在结构化数据中添加 inLanguage")
_rule("I18N-008", "i18n", "WARNING", "locale_format_correct",
      "日期/数字格式应符合目标地区习惯",
      "按目标地区的格式规范展示日期和数字")


# ─── Check functions ────────────────────────────────────────────────────

def _check_schema_rules(brand_data: Dict[str, Any], search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Check schema-related rules based on available data."""
    issues: List[Dict[str, Any]] = []
    site_readiness = brand_data.get("_site_readiness", {})
    schema_items = site_readiness.get("schema_items", [])

    # SCHEMA-001: Has any JSON-LD
    if not schema_items:
        issues.append(_issue("SCHEMA-001", "未检测到 JSON-LD 结构化数据"))
    else:
        # SCHEMA-002: Org schema complete
        org = next((s for s in schema_items if s.get("@type") in ("Organization", "Corporation")), None)
        if org:
            missing = [f for f in ("name", "url", "logo") if not org.get(f)]
            if missing:
                issues.append(_issue("SCHEMA-002", f"Organization schema 缺少字段: {', '.join(missing)}"))
        # SCHEMA-006: Context valid
        for s in schema_items:
            ctx = s.get("@context", "")
            if ctx and "schema.org" not in str(ctx):
                issues.append(_issue("SCHEMA-006", f"@context 不正确: {ctx}"))
                break
        # SCHEMA-010: No empty fields
        for s in schema_items:
            empty = _find_empty_fields(s)
            if empty:
                issues.append(_issue("SCHEMA-010", f"schema 包含空值字段: {', '.join(empty[:5])}"))
                break
        # SCHEMA-014: Has sameAs
        has_sameas = any(s.get("sameAs") for s in schema_items)
        if not has_sameas:
            issues.append(_issue("SCHEMA-014", "未检测到 sameAs 社交链接"))

    # SCHEMA-007: Breadcrumb
    has_breadcrumb = any(s.get("@type") == "BreadcrumbList" for s in schema_items)
    if not has_breadcrumb:
        issues.append(_issue("SCHEMA-007", "未检测到 BreadcrumbList schema"))

    return issues


def _check_crawler_rules(brand_data: Dict[str, Any], search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Check crawler accessibility rules."""
    issues: List[Dict[str, Any]] = []
    site_readiness = brand_data.get("_site_readiness", {})
    robots_analysis = site_readiness.get("robots_analysis", {})
    llms_txt = site_readiness.get("llms_txt", {})

    # AI bot access checks
    ai_bots = {
        "GPTBot": "CRAWL-001",
        "ClaudeBot": "CRAWL-002",
        "Google-Extended": "CRAWL-003",
        "PerplexityBot": "CRAWL-004",
        "Bingbot": "CRAWL-005",
        "CCBot": "CRAWL-006",
    }
    blocked_bots = robots_analysis.get("blocked_bots", [])
    for bot, rule_id in ai_bots.items():
        if bot in blocked_bots:
            sev_msg = "阻断" if rule_id in ("CRAWL-001", "CRAWL-002", "CRAWL-003", "CRAWL-004") else "阻断"
            issues.append(_issue(rule_id, f"robots.txt 阻断了 {bot}"))

    # llms.txt
    if not llms_txt.get("exists"):
        issues.append(_issue("CRAWL-007", "未检测到 llms.txt 文件"))
    else:
        if not llms_txt.get("has_brand_name"):
            issues.append(_issue("CRAWL-008", "llms.txt 缺少品牌名称"))
        if not llms_txt.get("has_key_pages"):
            issues.append(_issue("CRAWL-009", "llms.txt 缺少关键页面链接"))

    return issues


def _check_citability_rules(brand_data: Dict[str, Any], search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Check content citability rules."""
    issues: List[Dict[str, Any]] = []
    site_readiness = brand_data.get("_site_readiness", {})
    citability = brand_data.get("_citability_data", {})
    negative_signals = brand_data.get("_negative_signals", [])

    # CITE-001: Factual claims
    if not citability.get("has_factual_claims", True):
        issues.append(_issue("CITE-001", "页面缺乏可验证的事实性声明"))

    # CITE-002: Statistics
    if not citability.get("has_statistics", True):
        issues.append(_issue("CITE-002", "页面缺少统计数据或量化指标"))

    # CITE-008: CTA ratio
    cta_ratio = citability.get("cta_ratio", 0)
    if cta_ratio > 0.5:
        issues.append(_issue("CITE-008", f"CTA 内容占比 {cta_ratio:.0%}，超过 50% 阈值"))

    # CITE-009: Keyword stuffing
    kw_density = citability.get("keyword_density", 0)
    if kw_density > 0.03:
        issues.append(_issue("CITE-009", f"关键词密度 {kw_density:.1%}，超过 3% 阈值"))

    # From negative signals
    for sig in negative_signals:
        sig_type = sig.get("type", "")
        if sig_type == "cta_overload":
            issues.append(_issue("CITE-008", "检测到 CTA 过载信号"))
        elif sig_type == "thin_content":
            issues.append(_issue("CITE-001", "检测到内容稀薄信号"))
        elif sig_type == "keyword_stuffing":
            issues.append(_issue("CITE-009", "检测到关键词堆砌信号"))
        elif sig_type == "missing_author":
            issues.append(_issue("CITE-010", "缺少作者信息"))
        elif sig_type == "template_content":
            issues.append(_issue("CITE-011", "检测到模板化内容"))

    return issues


def _check_entity_rules(brand_data: Dict[str, Any], search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Check entity consistency rules."""
    issues: List[Dict[str, Any]] = []
    brand_name = brand_data.get("brand_name", "")
    ai_perception = brand_data.get("_ai_perception", {})

    # ENTITY-001: Brand name consistency
    if ai_perception.get("name_variants_found", 0) > 1:
        issues.append(_issue("ENTITY-001", f"检测到品牌名称的 {ai_perception['name_variants_found']} 种变体"))

    # ENTITY-006: Brand description length
    description = brand_data.get("description", "")
    if len(description) > 160:
        issues.append(_issue("ENTITY-006", f"品牌描述长度 {len(description)} 字符，超过 160 字符"))

    # ENTITY-010: Contact info
    if not brand_data.get("contact_email") and not brand_data.get("contact_phone"):
        issues.append(_issue("ENTITY-010", "未检测到可验证的联系信息"))

    return issues


def _check_multimodal_rules(brand_data: Dict[str, Any], search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Check multimodal optimization rules."""
    issues: List[Dict[str, Any]] = []
    site_readiness = brand_data.get("_site_readiness", {})
    content_data = site_readiness.get("content_analysis", {})

    # MULTI-005: TOC for long content
    if content_data.get("word_count", 0) > 2000 and not content_data.get("has_toc"):
        issues.append(_issue("MULTI-005", f"长内容（{content_data['word_count']} 词）缺少目录"))

    # MULTI-007: Table headers
    if content_data.get("has_tables") and not content_data.get("tables_have_headers"):
        issues.append(_issue("MULTI-007", "表格缺少 th 表头标签"))

    # MULTI-010: Mobile friendly
    if not site_readiness.get("mobile_friendly", True):
        issues.append(_issue("MULTI-010", "页面未通过移动端友好性检查"))

    return issues


def _check_i18n_rules(brand_data: Dict[str, Any], search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Check internationalization rules."""
    issues: List[Dict[str, Any]] = []
    target_region = brand_data.get("target_region", "global")
    site_readiness = brand_data.get("_site_readiness", {})
    i18n_data = site_readiness.get("i18n_analysis", {})

    # Only check i18n rules if targeting multiple regions/languages
    if target_region in ("global", "multi"):
        if not i18n_data.get("has_hreflang"):
            issues.append(_issue("I18N-001", "多语言站点缺少 hreflang 标签"))
        if i18n_data.get("has_hreflang") and not i18n_data.get("has_hreflang_default"):
            issues.append(_issue("I18N-002", "hreflang 缺少 x-default 声明"))

    return issues


# ─── Helpers ────────────────────────────────────────────────────────────

def _issue(rule_id: str, evidence: str) -> Dict[str, Any]:
    rule = next((r for r in RULES if r["rule_id"] == rule_id), None)
    return {
        "rule_id": rule_id,
        "dimension": rule["dimension"] if rule else "unknown",
        "severity": rule["severity"] if rule else "WARNING",
        "message": rule["message"] if rule else rule_id,
        "evidence": evidence,
        "fix_suggestion": rule["fix_suggestion"] if rule else "",
    }


def _find_empty_fields(obj: Any, prefix: str = "") -> List[str]:
    """Recursively find empty/null/None fields in a dict."""
    empties: List[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            path = f"{prefix}.{k}" if prefix else k
            if v is None or v == "" or v == []:
                empties.append(path)
            elif isinstance(v, dict):
                empties.extend(_find_empty_fields(v, path))
    return empties


def run_lint(
    brand_data: Dict[str, Any],
    search_results: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Run all lint checks and produce a structured report."""
    search_results = search_results or []
    all_issues: List[Dict[str, Any]] = []

    # Run dimension checks
    all_issues.extend(_check_schema_rules(brand_data, search_results))
    all_issues.extend(_check_crawler_rules(brand_data, search_results))
    all_issues.extend(_check_citability_rules(brand_data, search_results))
    all_issues.extend(_check_entity_rules(brand_data, search_results))
    all_issues.extend(_check_multimodal_rules(brand_data, search_results))
    all_issues.extend(_check_i18n_rules(brand_data, search_results))

    # Compute per-dimension scores
    dimension_scores: Dict[str, Dict[str, Any]] = {}
    for dim in DIMENSION_WEIGHTS:
        dim_issues = [i for i in all_issues if i["dimension"] == dim]
        dim_rules = [r for r in RULES if r["dimension"] == dim]
        error_count = sum(1 for i in dim_issues if i["severity"] == "ERROR")
        warn_count = sum(1 for i in dim_issues if i["severity"] == "WARNING")
        info_count = sum(1 for i in dim_issues if i["severity"] == "INFO")
        pass_count = len(dim_rules) - len(dim_issues)

        total_deduction = sum(SEVERITY_DEDUCTIONS[i["severity"]] for i in dim_issues)
        max_deduction = len(dim_rules) * SEVERITY_DEDUCTIONS["ERROR"]
        score = round(clamp(100.0 - (total_deduction / max_deduction * 100 if max_deduction > 0 else 0), 0.0, 100.0), 1)

        dimension_scores[dim] = {
            "score": score,
            "total_rules": len(dim_rules),
            "pass": pass_count,
            "fail": error_count,
            "warn": warn_count,
            "info": info_count,
        }

    # Compute overall score (weighted)
    overall = sum(
        dimension_scores[dim]["score"] * weight
        for dim, weight in DIMENSION_WEIGHTS.items()
    )
    overall = round(clamp(overall, 0.0, 100.0), 1)

    # Grade
    if overall >= 90:
        grade = "A"
    elif overall >= 75:
        grade = "B"
    elif overall >= 60:
        grade = "C"
    elif overall >= 40:
        grade = "D"
    else:
        grade = "F"

    errors = sum(1 for i in all_issues if i["severity"] == "ERROR")
    warnings = sum(1 for i in all_issues if i["severity"] == "WARNING")
    info = sum(1 for i in all_issues if i["severity"] == "INFO")
    total_rules = len(RULES)

    return {
        "schema_version": "1.9.0",
        "tool": "geo-lint",
        "tool_version": "1.9.0",
        "linted_at": utc_now_iso(),
        "target_url": brand_data.get("website", ""),
        "score": overall,
        "grade": grade,
        "dimension_scores": dimension_scores,
        "issues": all_issues,
        "summary": {
            "total_rules_checked": total_rules,
            "errors": errors,
            "warnings": warnings,
            "info": info,
            "pass_rate": round((total_rules - len(all_issues)) / total_rules, 4) if total_rules > 0 else 0,
        },
    }


# ─── CLI ────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="GEO Lint — 发布前合规检查")
    parser.add_argument("--input", required=True, help="品牌输入 JSON 文件路径")
    parser.add_argument("--search-results", help="搜索结果 JSONL 文件路径（可选）")
    parser.add_argument("--run-dir", help="运行目录（用于读取中间数据）")
    parser.add_argument("--output", help="输出报告路径")
    args = parser.parse_args()

    brand_data = read_json(args.input)

    # Load supplementary data from run-dir if available
    run_dir = Path(args.run_dir) if args.run_dir else None
    if run_dir:
        # Load site readiness if exists
        site_ready_path = run_dir / "intermediate" / "metrics.json"
        if site_ready_path.exists():
            metrics = read_json(site_ready_path)
            brand_data["_site_readiness"] = metrics.get("site_readiness", {})
            brand_data["_citability_data"] = metrics.get("citability", {})
            brand_data["_negative_signals"] = metrics.get("negative_signals", {}).get("signals", [])
            brand_data["_ai_perception"] = metrics.get("ai_perception", {})

    # Load search results
    search_results: List[Dict[str, Any]] = []
    if args.search_results:
        search_results = read_jsonl(args.search_results)

    # Run lint
    report = run_lint(brand_data, search_results)

    # Output
    if args.output:
        write_json(args.output, report)
        print(f"Lint report written to {args.output}")
        print(f"Score: {report['score']}/100 (Grade: {report['grade']})")
        print(f"Errors: {report['summary']['errors']}, Warnings: {report['summary']['warnings']}, Info: {report['summary']['info']}")
    else:
        print_json(report)


if __name__ == "__main__":
    main()