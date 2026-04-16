"""Built-in ingredient knowledge base — common food additives and their safety ratings."""

# Safety categories:
# - safe: Generally recognized as safe, natural ingredients
# - caution: Synthetic but widely used, moderate concern
# - avoid: Known health concerns, banned in some countries

ADDITIVE_DATABASE: dict[str, dict] = {
    # Preservatives (防腐剂)
    "山梨酸钾": {"category": "caution", "type": "防腐剂", "desc": "常用防腐剂，适量安全"},
    "苯甲酸钠": {"category": "avoid", "type": "防腐剂", "desc": "可能与维C反应生成苯，部分国家限制使用"},
    "脱氢乙酸钠": {"category": "caution", "type": "防腐剂", "desc": "广谱防腐剂"},
    "亚硝酸钠": {"category": "avoid", "type": "防腐剂/发色剂", "desc": "肉制品常用，过量有致癌风险"},
    "丙酸钙": {"category": "caution", "type": "防腐剂", "desc": "面包常用防腐剂"},

    # Sweeteners (甜味剂)
    "阿斯巴甜": {"category": "caution", "type": "人工甜味剂", "desc": "WHO 列为可能致癌物 (2B)"},
    "安赛蜜": {"category": "caution", "type": "人工甜味剂", "desc": "合成甜味剂，长期安全性有争议"},
    "三氯蔗糖": {"category": "caution", "type": "人工甜味剂", "desc": "蔗糖衍生物，热稳定性争议"},
    "糖精钠": {"category": "avoid", "type": "人工甜味剂", "desc": "最早的人工甜味剂，多国限制使用"},
    "甜蜜素": {"category": "avoid", "type": "人工甜味剂", "desc": "美国禁用，中国限量使用"},
    "赤藓糖醇": {"category": "safe", "type": "天然甜味剂", "desc": "天然糖醇，零热量"},
    "木糖醇": {"category": "safe", "type": "天然甜味剂", "desc": "天然糖醇"},

    # Colorants (着色剂)
    "日落黄": {"category": "caution", "type": "合成色素", "desc": "合成色素，部分国家要求警示标签"},
    "柠檬黄": {"category": "caution", "type": "合成色素", "desc": "合成色素"},
    "胭脂红": {"category": "caution", "type": "合成色素", "desc": "合成色素"},
    "焦糖色": {"category": "safe", "type": "天然色素", "desc": "天然着色剂"},

    # Flavor enhancers (增味剂)
    "谷氨酸钠": {"category": "safe", "type": "增味剂", "desc": "味精，GRAS认证安全"},
    "呈味核苷酸二钠": {"category": "safe", "type": "增味剂", "desc": "常与味精配合使用"},
    "5'-肌苷酸二钠": {"category": "safe", "type": "增味剂", "desc": "鲜味增强剂"},

    # Thickeners / Stabilizers
    "黄原胶": {"category": "safe", "type": "增稠剂", "desc": "天然多糖，广泛使用"},
    "卡拉胶": {"category": "caution", "type": "增稠剂", "desc": "海藻提取，部分研究指出可能刺激肠道"},
    "瓜尔胶": {"category": "safe", "type": "增稠剂", "desc": "天然植物胶"},
    "果胶": {"category": "safe", "type": "增稠剂", "desc": "天然果实提取"},

    # Positive keywords (正面关键词)
    "NFC": {"category": "safe", "type": "工艺标识", "desc": "非浓缩还原，更接近鲜榨"},
    "鲜榨": {"category": "safe", "type": "工艺标识", "desc": "新鲜压榨"},
    "有机": {"category": "safe", "type": "认证标识", "desc": "有机认证产品"},
    "零添加": {"category": "safe", "type": "产品标识", "desc": "无额外添加剂"},
}


def lookup_additive(name: str) -> dict | None:
    """Look up an ingredient name in the knowledge base.

    Returns dict with category, type, desc or None if not found.
    Supports partial matching (e.g., "橙汁(NFC)" matches "NFC").
    """
    name_lower = name.lower()

    # Exact match first
    if name in ADDITIVE_DATABASE:
        return ADDITIVE_DATABASE[name]

    # Partial match — check if any known additive name is contained in the ingredient
    for additive_name, info in ADDITIVE_DATABASE.items():
        if additive_name.lower() in name_lower:
            return info

    return None


def auto_seed_rules(session) -> int:
    """Seed IngredientRule table from ADDITIVE_DATABASE if empty.

    Returns count of rules added.
    """
    from src.models import IngredientRule

    existing = session.query(IngredientRule).count()
    if existing > 0:
        return 0

    category_map = {"safe": "whitelist", "caution": "warning", "avoid": "blacklist"}
    count = 0
    for name, info in ADDITIVE_DATABASE.items():
        rule_category = category_map.get(info["category"], "warning")
        # Only auto-seed caution and avoid items as rules
        if info["category"] in ("caution", "avoid"):
            session.add(IngredientRule(
                name=name,
                category=rule_category,
                description=f"[{info['type']}] {info['desc']}",
            ))
            count += 1

    session.commit()
    return count
