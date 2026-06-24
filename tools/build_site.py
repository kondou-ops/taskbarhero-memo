import json
import re
from datetime import date
from html import escape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

GRADE_ORDER = [
    "Common",
    "Uncommon",
    "Rare",
    "Legendary",
    "Immortal",
    "Arcana",
    "Beyond",
    "Celestial",
    "Divine",
    "Cosmic",
]

GRADE_JA = {
    "Common": "コモン",
    "Uncommon": "アンコモン",
    "Rare": "レア",
    "Legendary": "レジェンダリー",
    "Immortal": "イモータル",
    "Arcana": "アルカナ",
    "Beyond": "ビヨンド",
    "Celestial": "セレスティアル",
    "Divine": "ディバイン",
    "Cosmic": "コズミック",
}

RARITY_COLOR = {
    "Common": "#d7d7d7",
    "Uncommon": "#7ce937",
    "Rare": "#519fff",
    "Legendary": "#ebbb00",
    "Immortal": "#e8695a",
    "Arcana": "#fb86ff",
    "Beyond": "#ff0080",
    "Celestial": "#00f6ff",
    "Divine": "#f6e7a2",
    "Cosmic": "#fc00ff",
}

COLOR_TO_GRADE = {v.lower().lstrip("#"): k for k, v in RARITY_COLOR.items()}

GEAR_PREFIX = {
    300: ("剣", "weapon physical", "SWORD"),
    310: ("弓", "weapon physical", "BOW"),
    320: ("スタッフ", "weapon magic", "STAFF"),
    330: ("セプター", "weapon magic", "SCEPTER"),
    340: ("クロスボウ", "weapon physical", "CROSSBOW"),
    350: ("斧", "weapon physical", "AXE"),
    400: ("盾", "armor defense", "SHIELD"),
    410: ("矢", "weapon physical", "ARROW"),
    420: ("オーブ", "weapon magic", "ORB"),
    430: ("トーム", "weapon magic", "TOME"),
    440: ("ボルト", "weapon physical", "BOLT"),
    450: ("ハチェット", "weapon physical", "HATCHET"),
    500: ("ヘルメット", "armor defense", "HELMET"),
    510: ("アーマー", "armor defense", "ARMOR"),
    520: ("グローブ", "armor defense", "GLOVES"),
    530: ("ブーツ", "armor defense", "BOOTS"),
    600: ("アミュレット", "accessory universal", "AMULET"),
    610: ("イヤリング", "accessory universal", "EARING"),
    620: ("リング", "accessory universal", "RING"),
    630: ("ブレーサー", "accessory universal", "BRACER"),
}

SUB_WEAPON_PREFIXES = {400, 410, 420, 430, 440, 450}
BOOT_PREFIXES = {530}
ACCESSORY_PREFIXES = {600, 610, 620, 630}
CRAFTING_MATERIAL_PREFIXES = set(range(140, 150))
HIGH_KEEP_MATERIAL_BANDS = ("レベル 65", "レベル 80+")

GEAR_LEVEL_BY_INDEX = {
    1: 1,
    2: 5,
    3: 10,
    4: 15,
    5: 20,
    6: 25,
    7: 30,
    8: 35,
    9: 40,
    10: 45,
    11: 50,
    12: 55,
    13: 60,
    14: 65,
    15: 70,
    16: 75,
    17: 80,
    18: 85,
    19: 90,
    20: 95,
}

HERO_SLUGS = {
    101: "knight",
    201: "ranger",
    301: "sorcerer",
    401: "priest",
    501: "hunter",
    601: "slayer",
}

MATERIAL_TIER_BY_PREFIX = {
    **{110 + i: GRADE_ORDER[i] for i in range(10)},
    **{120 + i: GRADE_ORDER[i] for i in range(10)},
    **{130 + i: GRADE_ORDER[i] for i in range(10)},
    **{140 + i: GRADE_ORDER[i] for i in range(10)},
}

SOURCE_LINKS = [
    {
        "name": "公式ストア",
        "url": "https://store.steampowered.com/app/3678970/TBH_Task_Bar_Hero/",
        "note": "ゲーム概要、アイテム数、キューブ、取引対応、レアリティ体系の確認元。",
    },
    {
        "name": "市場価格",
        "url": "https://steamcommunity.com/market/search?appid=3678970",
        "note": "掲載品、出品数、円建て参考価格の取得元。価格は毎日自動更新。",
    },
    {
        "name": "Steamコミュニティガイド",
        "url": "https://steamcommunity.com/sharedfiles/filedetails/?id=3744134720",
        "note": "ステータス、ソケット、付与系の補助確認。コミュニティ情報なのでローカル表と照合して使用。",
    },
]

SOURCE_AUDIT = [
    {
        "source": "ゲーム内データ",
        "rank": "最優先",
        "checks": "日本語名、説明文、キャラクター名、スキル名。",
        "note": "ゲーム内ローカライズ表を抽出したローカルデータ。サイト内の名称はここを基準にする。",
    },
    {
        "source": "Steam公式ストア",
        "rank": "一次情報",
        "checks": "アイテム数、キューブ、取引対応、レアリティ、対応言語。",
        "note": "ゲーム仕様の大枠を確認。パッチで変わる細部はローカル表を優先。",
    },
    {
        "source": "市場価格データ",
        "rank": "現在値",
        "checks": "日本円の最低価格、中央値、取引量、出品数。",
        "note": "価格は変動するため売却直前に再確認。最高売注文は公開APIで安定取得できない。",
    },
    {
        "source": "Steamコミュニティガイド",
        "rank": "補助",
        "checks": "ソケット解放、ステータス系統、付与の考え方。",
        "note": "プレイヤー作成情報。Patch表記と投稿日を見て、断定しすぎない形で掲載。",
    },
]

MATERIAL_BANDS = [
    {
        "range": "レベル 1-10",
        "tier": "コモン / アンコモン",
        "crafting": [140001, 140002, 140003, 140004, 141001, 141002],
        "deco": [110001, 110002, 110003, 110004, 110005, 111001, 111002, 111003, 111004],
        "engraving": [120001, 120002, 120003, 121001, 121002, 121003, 121004],
        "inscription": [130001, 131001],
        "advice": "序盤クラフトと最初の付与用。木材/石/レザー系は多めに拾うが、倉庫を圧迫したら一定数だけ残す。",
    },
    {
        "range": "レベル 15-30",
        "tier": "レア / レジェンダリー",
        "crafting": [142001, 142002, 143001, 143002],
        "deco": [112001, 112002, 112003, 112004, 112005, 113001, 113002, 113003, 113004],
        "engraving": [122001, 122002, 122003, 122004, 123001, 123002, 123003, 123004],
        "inscription": [132001, 133001],
        "advice": "ビルドが固まり始める帯。物理/属性/速度に合う装飾素材は残し、合わない余剰だけ売却候補。",
    },
    {
        "range": "レベル 40-50",
        "tier": "イモータル / アルカナ",
        "crafting": [144001, 144002, 145001, 145002],
        "deco": [114001, 114002, 114003, 114004, 115001, 115002, 115003, 115004],
        "engraving": [124001, 124002, 124003, 124004, 125001, 125002, 125003, 125004],
        "inscription": [134001, 135001],
        "advice": "合成・付与の失敗コストが重くなる帯。市場価格を見て、安い素材だけ実験に回す。",
    },
    {
        "range": "レベル 65",
        "tier": "ビヨンド / セレスティアル",
        "crafting": [146001, 146002, 147001, 147002],
        "deco": [116001, 116002, 116003, 116004, 117001, 117002],
        "engraving": [126001, 126002, 126003, 126004, 127001, 127002],
        "inscription": [136001, 137001],
        "advice": "高難度用の主力素材。セレスティアル合成はキューブレベル50条件があるため、売る前にキューブ進行も確認。",
    },
    {
        "range": "レベル 80+",
        "tier": "ディバイン / コズミック",
        "crafting": [148001, 148002, 149001, 149002],
        "deco": [118001, 118002, 119001, 119002],
        "engraving": [128001, 128002, 129001, 129002],
        "inscription": [138001, 139001],
        "advice": "最終帯。コズミックは合成不可なので、素材・装備ともに売却前の確認を強める。",
    },
]

TIER_TABLE = [
    {
        "tier": "残す",
        "label": "原則残す",
        "target": "ソウルストーン、ディバイン/コズミック素材、刻印巻物、主力ビルドの高等級装備、市場価格が高い素材",
        "reason": "ボス挑戦、最終付与、上位クラフト、取引価値のどれかに直結する。",
    },
    {
        "tier": "必要数",
        "label": "必要数を残す",
        "target": "装飾/彫刻素材、レベル40以上のクラフト素材、同等級合成に使う装備",
        "reason": "欲しいステータスの素材は消費が早い。合成は同等級装備9個が基本。",
    },
    {
        "tier": "余剰売却",
        "label": "余剰だけ売却可",
        "target": "序盤クラフト素材、ビルド外の中級素材、マーケットで安い重複品",
        "reason": "序盤素材は必要数を超えやすい。価格が安いものは倉庫圧迫を避ける。",
    },
    {
        "tier": "処分候補",
        "label": "売却/錬金候補",
        "target": "低等級の重複装備、ビルドに合わない付与なし装備、価格が低く在庫の多い素材",
        "reason": "使う予定がなければゴールド化や市場売却でよい。ただし装飾/彫刻/碑文済み装備は取引不可。",
    },
]

BUILD_TABLE = [
    {
        "name": "物理/攻速",
        "classes": "剣・弓・クロスボウ・斧・ハチェット・矢・ボルト",
        "keep": "物理ダメージ%、攻撃速度%、攻撃力%、クリティカル、投射物/近接/範囲強化",
        "sell": "魔法属性だけに寄った素材や、使わない武器種の低等級重複",
    },
    {
        "name": "属性/魔法",
        "classes": "スタッフ・セプター・オーブ・トーム",
        "keep": "火/冷気/雷/混沌ダメージ%、詠唱速度、クールダウン短縮、召喚/範囲強化",
        "sell": "物理専用ステータスだけの低等級素材。耐久不足時は防御素材を優先して残す。",
    },
    {
        "name": "耐久/放置安定",
        "classes": "盾・ヘルメット・アーマー・グローブ・ブーツ・アクセサリー",
        "keep": "最大体力、耐性、ダメージ軽減、ダメージ吸収、ライフ吸収、ヒット時体力回復",
        "sell": "火力が十分で、同じ耐久素材が過剰な場合だけ処分。",
    },
]

HERO_BUILD_NOTES = {
    101: {
        "role": "前衛 / 盾",
        "gear": "剣・盾・防具",
        "keep": "物理ダメージ%、攻撃力%、最大体力、ダメージ軽減、耐性",
        "sell": "魔法属性だけに寄った素材や、使わない遠距離武器の低等級重複。",
    },
    201: {
        "role": "遠距離",
        "gear": "弓・矢・攻撃速度系アクセ",
        "keep": "弓・矢の高等級品、エメラルド系、アメジスト系、翡翠石、スパイダーシルク、フェニックスの灰、タイタンマロウ、ヴォイドの精髄。",
        "sell": "詠唱速度や魔法属性だけの素材。防御不足なら耐久素材は残す。",
    },
    301: {
        "role": "範囲魔法",
        "gear": "スタッフ・オーブ・ブーツ",
        "keep": "火/冷気/雷、詠唱速度、範囲、クールダウン短縮、魔法火力系",
        "sell": "物理専用素材や近接武器の低等級重複。サブ武器/ブーツの特殊効果は売却前に確認。",
    },
    401: {
        "role": "ボス専用 / 支援",
        "gear": "セプター・トーム・耐久アクセ",
        "keep": "回復/支援向き、詠唱速度、最大体力、耐性、雷/範囲",
        "sell": "火力だけの余剰素材。支援運用なら耐久と詠唱系を優先。",
    },
    501: {
        "role": "罠 / クロスボウ",
        "gear": "クロスボウ・ボルト",
        "keep": "投射物、攻撃速度%、火/冷気/雷、罠系、クリティカル",
        "sell": "剣/盾専用の低等級重複。属性ボルト候補は残す。",
    },
    601: {
        "role": "近接火力",
        "gear": "斧・ハチェット・耐久装備",
        "keep": "物理ダメージ%、攻撃速度%、近接/範囲、ライフ吸収、最大体力",
        "sell": "遠距離/魔法専用素材。高難度用の耐久素材は売りすぎない。",
    },
}

HERO_AFFIX_TARGETS = {
    "knight": {
        "weapon": ["物理ダメージ", "攻撃力", "攻撃速度", "クリティカル", "近接ダメージ", "範囲ダメージ"],
        "armor": ["最大体力", "防御力", "耐性", "ダメージ軽減", "ダメージ吸収", "ブロック率"],
        "accessory": ["攻撃力", "攻撃速度", "ライフ吸収", "ヒット時体力回復", "移動速度"],
    },
    "ranger": {
        "weapon": ["物理ダメージ", "攻撃速度", "攻撃力", "クリティカル", "投射物ダメージ", "範囲ダメージ"],
        "armor": ["最大体力", "防御力", "耐性", "ダメージ軽減", "ダメージ吸収", "回避率"],
        "accessory": ["移動速度", "攻撃速度", "攻撃力", "クリティカル", "クールダウン短縮", "効果範囲"],
    },
    "sorcerer": {
        "weapon": ["火ダメージ", "冷気ダメージ", "雷ダメージ", "混沌ダメージ", "詠唱速度", "召喚ダメージ", "効果範囲"],
        "armor": ["最大体力", "耐性", "防御力", "ダメージ軽減", "ダメージ吸収", "クールダウン短縮"],
        "accessory": ["詠唱速度", "クールダウン短縮", "効果範囲", "最大体力", "召喚ダメージ"],
    },
    "priest": {
        "weapon": ["詠唱速度", "クールダウン短縮", "攻撃力", "雷ダメージ", "火ダメージ"],
        "armor": ["最大体力", "耐性", "防御力", "ダメージ軽減", "ダメージ吸収"],
        "accessory": ["詠唱速度", "クールダウン短縮", "最大体力", "秒間体力回復", "ヒット時体力回復"],
    },
    "hunter": {
        "weapon": ["物理ダメージ", "攻撃速度", "攻撃力", "クリティカル", "投射物ダメージ", "効果範囲"],
        "armor": ["最大体力", "防御力", "耐性", "ダメージ軽減", "ダメージ吸収", "回避率"],
        "accessory": ["移動速度", "攻撃速度", "攻撃力", "クリティカル", "クールダウン短縮", "効果範囲"],
    },
    "slayer": {
        "weapon": ["物理ダメージ", "攻撃速度", "攻撃力", "クリティカル", "近接ダメージ", "範囲ダメージ", "ライフ吸収"],
        "armor": ["最大体力", "防御力", "耐性", "ダメージ軽減", "ダメージ吸収", "回避率"],
        "accessory": ["移動速度", "攻撃速度", "攻撃力", "クリティカル", "ライフ吸収", "ヒット時体力回復"],
    },
}

SOCKET_TABLE = [
    {"grade": "Rare", "deco": 1, "engraving": 0, "inscription": 0},
    {"grade": "Legendary", "deco": 2, "engraving": 0, "inscription": 0},
    {"grade": "Immortal", "deco": 2, "engraving": 1, "inscription": 0},
    {"grade": "Arcana", "deco": 2, "engraving": 1, "inscription": 1},
    {"grade": "Beyond", "deco": 2, "engraving": 2, "inscription": 1},
    {"grade": "Celestial", "deco": 2, "engraving": 2, "inscription": 2},
    {"grade": "Divine", "deco": 2, "engraving": 2, "inscription": 2},
    {"grade": "Cosmic", "deco": 2, "engraving": 2, "inscription": 2},
]


def read_json(path: str, encoding: str = "utf-8"):
    return json.loads((ROOT / path).read_text(encoding=encoding))


def read_optional_json(path: str, fallback):
    target = ROOT / path
    if not target.exists():
        return fallback
    return json.loads(target.read_text(encoding="utf-8-sig"))


def item_id_from_key(key: str) -> int | None:
    match = re.search(r"_(\d+)$", key)
    return int(match.group(1)) if match else None


def icon_for(iid: int) -> str:
    prefix = iid // 1000
    if prefix in GEAR_PREFIX:
        icon = f"icons/{GEAR_PREFIX[prefix][2]}_{iid}.png"
    else:
        icon = f"icons/Item_{iid}.png"
    return icon if (ROOT / icon).exists() else "icons/Item_100001.png"


def grade_from_id(iid: int) -> str | None:
    return MATERIAL_TIER_BY_PREFIX.get(iid // 1000)


def price_number(price: str) -> float:
    if not price:
        return 0.0
    cleaned = re.sub(r"[^0-9.]", "", price)
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def strip_market_base(name: str) -> str:
    return re.sub(
        r" \((Common|Uncommon|Rare|Legendary|Immortal|Arcana|Beyond|Celestial|Divine|Cosmic)\) [A-Z]$",
        "",
        name,
    )


def market_grade(entry: dict, base_id: int | None) -> str | None:
    match = re.search(r"\((Common|Uncommon|Rare|Legendary|Immortal|Arcana|Beyond|Celestial|Divine|Cosmic)\)", entry["name"])
    if match:
        return match.group(1)
    color = entry["asset_description"].get("name_color", "").lower()
    if color in COLOR_TO_GRADE:
        return COLOR_TO_GRADE[color]
    if base_id:
        return grade_from_id(base_id)
    return None


def translate_market_type(text: str) -> str:
    mapping = {
        "Decoration Material": "装飾素材",
        "Engraving Material": "彫刻素材",
        "Crafting Material": "クラフト素材",
        "Inscription Material": "刻印素材",
        "Soulstone": "ソウルストーン",
        "Sword": "剣",
        "Bow": "弓",
        "Staff": "スタッフ",
        "Scepter": "セプター",
        "Crossbow": "クロスボウ",
        "Axe": "斧",
        "Shield": "盾",
        "Arrow": "矢",
        "Orb": "オーブ",
        "Tome": "トーム",
        "Bolt": "ボルト",
        "Hatchet": "ハチェット",
        "Helmet": "ヘルメット",
        "Armor": "アーマー",
        "Gloves": "グローブ",
        "Boots": "ブーツ",
        "Amulet": "アミュレット",
        "Earring": "イヤリング",
        "Ring": "リング",
        "Bracer": "ブレーサー",
        "Earing": "イヤリング",
    }
    match = re.match(r"(.+?) - Lv\.? ?(\d+)", text or "")
    if match:
        kind = mapping.get(match.group(1), match.group(1))
        return f"{kind} - レベル {match.group(2)}"
    return mapping.get(text, text)


def build_market(name_to_id: dict[str, int]) -> tuple[list[dict], dict[int, list[dict]]]:
    raw = read_json("market-items.json", "utf-8-sig")
    unique: dict[str, dict] = {}
    for entry in raw:
        key = entry["name"]
        if key in unique:
            continue
        desc = entry["asset_description"]
        base = strip_market_base(entry["name"])
        base_id = name_to_id.get(base)
        image = entry.get("image_path") or f"images/{entry['name']}.png"
        lowest = (
            entry.get("lowest_price_text_jpy")
            or entry.get("lowest_price")
            or entry.get("sell_price_text")
            or entry.get("sale_price_text")
            or "-"
        )
        median = entry.get("median_price_text_jpy") or entry.get("median_price") or "-"
        highest = entry.get("highest_price_text_jpy") or "未取得"
        unique[key] = {
            "name": entry["name"],
            "base": base,
            "id": base_id,
            "type": translate_market_type(desc.get("type", "")),
            "grade": market_grade(entry, base_id),
            "price": lowest,
            "medianPrice": median,
            "highestPrice": highest,
            "highestNote": entry.get("highest_note", "").replace("Steamの公開API", "公開データ").replace("公開API", "公開データ"),
            "priceValue": price_number(lowest),
            "listings": entry.get("sell_listings", 0),
            "volume": entry.get("volume") or "-",
            "priceUpdatedAt": entry.get("price_fetched_at", ""),
            "color": desc.get("name_color", ""),
            "image": image if (ROOT / image).exists() else "",
        }
    market = sorted(unique.values(), key=lambda x: (-x["priceValue"], x["name"]))
    by_id: dict[int, list[dict]] = {}
    for entry in market:
        if entry["id"]:
            by_id.setdefault(entry["id"], []).append(entry)
    return market, by_id


def material_category(iid: int) -> tuple[str, str]:
    prefix = iid // 1000
    if 110 <= prefix <= 119:
        return "装飾素材", "material decoration"
    if 120 <= prefix <= 129:
        return "彫刻素材", "material engraving"
    if 130 <= prefix <= 139:
        return "刻印素材", "material inscription"
    if 140 <= prefix <= 149:
        return "クラフト素材", "material crafting"
    if prefix == 160:
        return "記念コイン", "material offering"
    if prefix == 190:
        return "ソウルストーン", "material soulstone"
    return "素材", "material"


def stat_tags(en: str, category: str, class_name: str) -> list[str]:
    text = en.lower()
    tags: list[str] = []
    if any(word in text for word in ["amethyst", "emerald", "opal", "diamond", "lazuli", "jade", "fang", "silk", "claw", "venom", "ash", "dice"]):
        tags.append("物理/攻撃速度")
    if any(word in text for word in ["ruby", "sapphire", "topaz", "arcane", "starlight", "void", "chaos", "crystal", "blood", "thunder", "fire", "cold", "lightning"]):
        tags.append("魔法/属性")
    if any(word in text for word in ["pearl", "coral", "turquoise", "garnet", "bone", "scale", "marrow", "leather", "stone"]):
        tags.append("防御/耐久")
    if "physical" in class_name:
        tags.append("物理/攻撃速度")
    if "magic" in class_name:
        tags.append("魔法/属性")
    if "defense" in class_name:
        tags.append("防御/耐久")
    if "accessory" in class_name:
        tags.append("汎用")
    if "soulstone" in class_name:
        tags.append("ボス素材")
    if "crafting" in class_name:
        tags.append("クラフト")
    if "inscription" in class_name:
        tags.append("刻印")
    if "decoration" in class_name or "engraving" in class_name:
        tags.append("付与")
    return list(dict.fromkeys(tags))


def effect_tags(effect_text: str) -> list[str]:
    text = effect_text.lower()
    tags: list[str] = []
    if any(word in text for word in ["physical", "attack speed", "crit", "projectile", "melee", "attack damage"]):
        tags.append("物理/攻撃速度")
    if any(word in text for word in ["fire", "cold", "lightning", "chaos", "cast speed", "cooldown", "summon", "area of effect"]):
        tags.append("魔法/属性")
    if any(word in text for word in ["resistance", "max hp", "armor", "dodge", "block", "damage reduction", "absorption", "life leech", "hp regen"]):
        tags.append("防御/耐久")
    return tags


def recommended_for(en: str, category: str, effect_text: str, specials: list[dict]) -> list[str]:
    text = f"{en} {category} {effect_text} {' '.join(s.get('Effect', '') for s in specials)}".lower()
    rec: list[str] = []
    if any(word in text for word in ["bow", "arrow", "physical", "attack speed", "crit", "projectile", "skewer", "arrow rain"]):
        rec.append("レンジャー")
    if any(word in text for word in ["staff", "orb", "fire", "cold", "lightning", "cast speed", "cooldown", "hydra", "ice orb", "snowstorm"]):
        rec.append("ソーサラー")
    if any(word in text for word in ["crossbow", "bolt", "trap", "turret", "explosive"]):
        rec.append("ハンター")
    if any(word in text for word in ["axe", "hatchet", "melee", "life leech", "missing hp", "axe spin"]):
        rec.append("スレイヤー")
    if any(word in text for word in ["scepter", "tome", "heal", "wrath of heaven", "resistance", "max hp"]):
        rec.append("プリースト")
    return list(dict.fromkeys(rec))


def translate_unique_effect(effect: str) -> str:
    replacements = [
        ("Equipped skill projectile +1", "装備スキルの投射物 +1"),
        ("Equipped skill multistrike +1", "装備スキルの連続攻撃 +1"),
        ("Equipped skill -1 basic attack to trigger", "装備スキルの発動に必要な基本攻撃 -1"),
        ("Equipped skill CD reduced", "装備スキルのクールダウン短縮"),
        ("Equipped skill element changes", "装備スキルの属性変更"),
        ("Hydra attack speed +200%", "ヒドラ攻撃速度 +200%"),
        ("Lightning skills shock on hit", "ライトニング命中時に感電"),
        ("Ice Orb 30% freeze chilled enemies", "アイスオーブが冷却中の敵を30%で凍結"),
        ("Snowstorm +100% dmg vs frozen", "スノーストームが凍結中の敵へ+100%ダメージ"),
        ("Wrath of Heaven: attacks also heal allies", "天上の怒り中の攻撃で味方も回復"),
        ("Crossbow Turret max +1", "クロスボウタレット最大数 +1"),
        ("Max Crossbow Turrets +1", "クロスボウタレット最大数 +1"),
        ("Crossbow Turret CD -50%", "クロスボウタレットのクールダウン -50%"),
        ("Explosive Bolt dmg & CD -50%", "エクスプロージョンボルトのダメージとクールダウン -50%"),
        ("Explosive Bolt kill → Charge Trap CD -1s", "エクスプロージョンボルトで倒すとチャージトラップのクールダウン -1秒"),
        ("Crit basic atk → Arrow Rain CD -0.5s", "基本攻撃のクリティカルで矢の雨のクールダウン -0.5秒"),
        ("Skewer Shot +2x dmg to bleeding", "スキュワーショットが出血中の敵へ2倍ダメージ"),
        ("Kill w/ Shield Charge → resets CD", "シールドチャージで倒すとクールダウンリセット"),
        ("Attack Speed +1% per 1% missing HP", "失った体力 1%ごとに攻撃速度 +1%"),
        ("Axe Spin → fire dmg, bleed → ignite", "アックススピンが火属性化、出血が点火化"),
        ("Axe Spin bleed chance → 50%", "アックススピンの出血確率が50%"),
        ("Walk between waves at fastest party member's speed", "ウェーブ間の移動速度がパーティ最速メンバー基準"),
        ("Walk between waves at slowest party member's speed", "ウェーブ間の移動速度がパーティ最遅メンバー基準"),
    ]
    for en, ja in replacements:
        if effect == en:
            return ja
    return effect


STAT_REPLACEMENTS = [
    ("All Elemental Resistance", "全属性耐性"),
    ("Cooldown Reduction", "クールダウン短縮"),
    ("Damage Absorption", "ダメージ吸収"),
    ("Damage Reduction", "ダメージ軽減"),
    ("Area of Effect", "効果範囲"),
    ("Projectile Count", "投射物数"),
    ("Basic Attack Count", "基本攻撃回数"),
    ("Cold Resistance", "冷気耐性"),
    ("Fire Resistance", "火耐性"),
    ("Lightning Resistance", "雷耐性"),
    ("Chaos Resistance", "混沌耐性"),
    ("Physical Resistance", "物理耐性"),
    ("Physical Damage", "物理ダメージ"),
    ("Attack Damage", "攻撃力"),
    ("Attack Speed", "攻撃速度"),
    ("Cast Speed", "詠唱速度"),
    ("Crit Chance", "クリティカル率"),
    ("Crit Damage", "クリティカルダメージ"),
    ("Cold Damage", "冷気ダメージ"),
    ("Fire Damage", "火ダメージ"),
    ("Lightning Damage", "雷ダメージ"),
    ("Chaos Damage", "混沌ダメージ"),
    ("Projectile Damage", "投射物ダメージ"),
    ("Melee Damage", "近接ダメージ"),
    ("Area Damage", "範囲ダメージ"),
    ("Summon Damage", "召喚ダメージ"),
    ("Movement Speed", "移動速度"),
    ("Block Chance", "ブロック率"),
    ("Dodge Chance", "回避率"),
    ("Life Leech", "ライフ吸収"),
    ("HP Regen/sec", "秒間体力回復"),
    ("HP per Hit", "ヒット時体力回復"),
    ("Max HP", "最大体力"),
    ("Armor", "防御力"),
    ("Multistrike", "連続攻撃"),
    ("Resistance", "耐性"),
    ("Damage", "ダメージ"),
]


SLOT_JA = {
    "Sword": "剣",
    "Bow": "弓",
    "Staff": "スタッフ",
    "Scepter": "セプター",
    "Crossbow": "クロスボウ",
    "Axe": "斧",
    "Shield": "盾",
    "Arrow": "矢",
    "Orb": "オーブ",
    "Tome": "トーム",
    "Bolt": "ボルト",
    "Hatchet": "ハチェット",
    "Helmet": "ヘルメット",
    "Armor": "アーマー",
    "Gloves": "グローブ",
    "Boots": "ブーツ",
    "Amulet": "アミュレット",
    "Earring": "イヤリング",
    "Ring": "リング",
    "Bracer": "ブレーサー",
}


def translate_stat_text(text: str) -> str:
    translated = text or ""
    for en, ja in STAT_REPLACEMENTS:
        translated = translated.replace(en, ja)
    return translated


def localize_visible_text(text: str) -> str:
    translated = translate_stat_text(text)
    replacements = [
        ("AoE", "範囲攻撃"),
        ("CD", "クールダウン"),
        ("HP", "体力"),
    ]
    for en, ja in replacements:
        translated = translated.replace(en, ja)
    return translated


def build_guide_effects() -> tuple[dict, dict[str, dict], dict[str, list[dict]]]:
    guide = read_optional_json(
        "guide-effects.json",
        {"source": "", "socketUnlocks": [], "decorations": [], "engravings": [], "uniqueMods": {}},
    )
    effect_by_name: dict[str, dict] = {}
    for row in guide.get("decorations", []):
        row["WeaponJa"] = translate_stat_text(row.get("Weapon", ""))
        row["ArmorJa"] = translate_stat_text(row.get("Armor", ""))
        row["AccessoryJa"] = translate_stat_text(row.get("Accessory", ""))
        effect_by_name[row["Gem"]] = {
            "kind": "装飾",
            "grade": row.get("Grade", ""),
            "weapon": row.get("Weapon", ""),
            "armor": row.get("Armor", ""),
            "accessory": row.get("Accessory", ""),
            "weaponJa": row.get("WeaponJa", ""),
            "armorJa": row.get("ArmorJa", ""),
            "accessoryJa": row.get("AccessoryJa", ""),
        }
    for row in guide.get("engravings", []):
        row["WeaponJa"] = translate_stat_text(row.get("Weapon", ""))
        row["ArmorJa"] = translate_stat_text(row.get("Armor", ""))
        row["AccessoryJa"] = translate_stat_text(row.get("Accessory", ""))
        effect_by_name[row["Engraving"]] = {
            "kind": "彫刻",
            "grade": row.get("Grade", ""),
            "weapon": row.get("Weapon", ""),
            "armor": row.get("Armor", ""),
            "accessory": row.get("Accessory", ""),
            "weaponJa": row.get("WeaponJa", ""),
            "armorJa": row.get("ArmorJa", ""),
            "accessoryJa": row.get("AccessoryJa", ""),
        }

    unique_by_item: dict[str, list[dict]] = {}
    class_ja = {
        "knight": "ナイト",
        "universal": "共通",
        "ranger": "レンジャー",
        "sorcerer": "ソーサラー",
        "priest": "プリースト",
        "hunter": "ハンター",
        "slayer": "スレイヤー",
    }
    for class_key, rows in guide.get("uniqueMods", {}).items():
        for row in rows:
            row.setdefault("EffectJa", translate_unique_effect(row.get("Effect", "")))
            item = row.get("Item", "")
            base = re.sub(r" \(.+\)$", "", item)
            slot_match = re.search(r"\((.+)\)$", item)
            entry = {
                "class": class_ja.get(class_key, class_key),
                "classKey": class_key,
                "item": item,
                "base": base,
                "slot": slot_match.group(1) if slot_match else "",
                "slotJa": SLOT_JA.get(slot_match.group(1), slot_match.group(1)) if slot_match else "",
                "level": row.get("Lv", ""),
                "grade": row.get("Grade", ""),
                "effect": row.get("Effect", ""),
                "effectJa": row.get("EffectJa", row.get("Effect", "")),
            }
            unique_by_item.setdefault(base, []).append(entry)
    return guide, effect_by_name, unique_by_item


def effect_summary(effect: dict | None) -> str:
    if not effect:
        return ""
    return " / ".join(
        part
        for part in [
            f'武器: {effect.get("weaponJa") or effect.get("weapon", "")}',
            f'防具: {effect.get("armorJa") or effect.get("armor", "")}',
            f'アクセ: {effect.get("accessoryJa") or effect.get("accessory", "")}',
        ]
        if part.strip() not in {"武器:", "防具:", "アクセ:"}
    )


def related_band(iid: int) -> str:
    for band in MATERIAL_BANDS:
        all_ids = band["crafting"] + band["deco"] + band["engraving"] + band["inscription"]
        if iid in all_ids:
            return f'{band["range"]} / {band["tier"]}'
    if 300000 <= iid <= 639999:
        level = GEAR_LEVEL_BY_INDEX.get(iid % 1000)
        if level:
            if level <= 10:
                return "レベル 1-10"
            if level <= 30:
                return "レベル 15-30"
            if level <= 50:
                return "レベル 40-50"
            if level <= 65:
                return "レベル 65"
            return "レベル 80+"
    return ""


def uses_for(iid: int, category: str, gear_kind: str | None, grade: str | None) -> list[str]:
    prefix = iid // 1000
    if 110 <= prefix <= 119:
        return ["キューブの装飾で使用", "装飾スロット付き装備1個 + 装飾素材1個", "素材に応じたランダムステータスを付与"]
    if 120 <= prefix <= 129:
        return ["キューブの彫刻で使用", "彫刻スロット付き装備1個 + 彫刻素材1個", "装備種類に応じた候補からランダム付与"]
    if 130 <= prefix <= 139:
        return ["キューブの刻印で使用", "刻印スロット付き装備1個 + 刻印素材1個", "増加系など強い最終火力ステータスの候補"]
    if 140 <= prefix <= 149:
        return ["キューブの製作で使用", "製作したい装備種類を選んで必要素材として投入", "同レベル帯の装備更新に備えて必要数を確保"]
    if prefix == 160:
        return ["キューブの祈願で使用", "記念コインを捧げてランダムアイテムを獲得", "イベント/記念品なので価格確認後に使う"]
    if prefix == 190:
        return ["ボス召喚に必要", "失敗時は消費されず、勝利時に消費される仕様としてコミュニティ情報あり", "難易度進行用に優先して残す"]
    if gear_kind:
        level = GEAR_LEVEL_BY_INDEX.get(iid % 1000)
        return [
            f"{gear_kind}として装備",
            "同じ等級の装備9個でキューブ合成に使える",
            "装飾/彫刻/碑文が付いていなければ取引船の候補",
            f"目安装備レベル: {level if level else '-'}",
        ]
    return ["用途未分類。売却前にゲーム内ツールチップを確認"]


def action_for(iid: int, category: str, grade: str | None, markets: list[dict]) -> str:
    prefix = iid // 1000
    max_price = max([m["priceValue"] for m in markets], default=0.0)
    if prefix == 190:
        return "必ず残す"
    if prefix == 160:
        return "祈願用"
    if grade in {"Celestial", "Divine", "Cosmic"}:
        return "残す"
    if max_price >= 500:
        return "価格確認"
    if 300 <= prefix <= 639:
        return "ビルド/合成"
    if grade in {"Common", "Uncommon"}:
        return "余剰売却可"
    return "必要数を残す"


def sell_advice(iid: int, action: str, markets: list[dict]) -> str:
    prefix = iid // 1000
    if prefix == 190:
        return "ソウルストーンは進行に直結するため、売る場合は現在の難易度分を残してから。"
    if markets:
        best = max(markets, key=lambda x: x["priceValue"])
        median = f' / 中央 {best["medianPrice"]}' if best.get("medianPrice") and best["medianPrice"] != "-" else ""
        return f'市場掲載あり: 最低 {best["price"]}{median} / 出品 {best["listings"]}。価格が動くので売却直前に確認。'
    if 300 <= prefix <= 639:
        return "ビルド外でも同等級9個合成に使える。低等級・重複・付与なしなら売却/錬金候補。"
    if "余剰" in action:
        return "必要数を決め、超えた分だけ売却/錬金候補。"
    return "用途がある素材。次の装備更新や付与予定がない余剰だけ処分。"


def build_heroes() -> list[dict]:
    rows = read_json("StringTable.json")
    names: dict[int, dict] = {}
    descriptions: dict[int, dict] = {}
    skills: dict[int, list[dict]] = {}

    for row in rows:
        key = row["key"]
        if key.startswith("HeroName_"):
            hero_id = item_id_from_key(key)
            if hero_id:
                names[hero_id] = {"ja": row["ja"], "en": row["en"]}
        elif key.startswith("Description_Hero"):
            match = re.search(r"Hero(\d+)$", key)
            if match:
                descriptions[int(match.group(1))] = {"ja": row["ja"], "en": row["en"]}
        elif key.startswith("SkillName_"):
            skill_id = item_id_from_key(key)
            if skill_id:
                hero_group = skill_id // 10000
                skills.setdefault(hero_group, []).append({"id": skill_id, "ja": row["ja"], "en": row["en"]})

    heroes = []
    for hero_id in sorted(names):
        note = HERO_BUILD_NOTES.get(hero_id, {})
        slug = HERO_SLUGS.get(hero_id, str(hero_id))
        heroes.append(
            {
                "id": hero_id,
                "slug": slug,
                "page": f"characters/{slug}.html",
                "ja": names[hero_id]["ja"],
                "en": names[hero_id]["en"],
                "desc": localize_visible_text(descriptions.get(hero_id, {}).get("ja", "")),
                "role": note.get("role", ""),
                "gear": localize_visible_text(note.get("gear", "")),
                "keep": localize_visible_text(note.get("keep", "")),
                "sell": localize_visible_text(note.get("sell", "")),
                "skills": sorted(skills.get(hero_id // 100, []), key=lambda x: x["id"]),
            }
        )
    return heroes


def build_items() -> tuple[list[dict], list[dict]]:
    rows = read_json("ItemTable.json")
    _guide, effect_by_name, unique_by_item = build_guide_effects()
    names: dict[int, dict] = {}
    descriptions: dict[int, dict] = {}
    for row in rows:
        iid = item_id_from_key(row["key"])
        if not iid:
            continue
        if row["key"].startswith("ItemName_"):
            names[iid] = {"id": iid, "ja": row["ja"], "en": row["en"]}
        elif row["key"].startswith("ItemDescription_"):
            descriptions[iid] = {"ja": row["ja"], "en": row["en"]}

    name_to_id = {row["en"]: iid for iid, row in names.items()}
    market, market_by_id = build_market(name_to_id)

    items = []
    for iid, row in sorted(names.items()):
        prefix = iid // 1000
        grade = grade_from_id(iid)
        level = None
        gear_kind = None
        if prefix in GEAR_PREFIX:
            gear_kind, class_name, _icon_prefix = GEAR_PREFIX[prefix]
            level = GEAR_LEVEL_BY_INDEX.get(iid % 1000)
            category = gear_kind
            class_name = f"gear {class_name}"
        else:
            category, class_name = material_category(iid)

        markets = market_by_id.get(iid, [])
        effect = effect_by_name.get(row["en"])
        specials = unique_by_item.get(row["en"], [])
        effect_text = effect_summary(effect)
        action = action_for(iid, category, grade, markets)
        tags = stat_tags(row["en"], category, class_name)
        tags.extend(effect_tags(effect_text))
        if level:
            tags.insert(0, f"レベル {level}")
        if specials:
            tags.append("特殊効果")
        recommended = recommended_for(row["en"], category, effect_text, specials)

        items.append(
            {
                "id": iid,
                "ja": row["ja"],
                "en": row["en"],
                "desc": descriptions.get(iid, {}).get("ja", ""),
                "category": category,
                "class": class_name,
                "grade": grade,
                "level": level,
                "tierBand": related_band(iid),
                "action": action,
                "uses": uses_for(iid, category, gear_kind, grade),
                "sellAdvice": sell_advice(iid, action, markets),
                "icon": icon_for(iid),
                "tags": list(dict.fromkeys(tags)),
                "effect": effect,
                "effectText": effect_text,
                "specials": specials,
                "specialCount": len(specials),
                "recommended": recommended,
                "market": markets,
                "marketCount": len(markets),
            }
        )
    return items, market


def css() -> str:
    return r"""
:root{--bg:#151017;--bg2:#261a13;--paper:#f8f0df;--paper2:#fffaf0;--ink:#241a14;--muted:#76695c;--line:#d5c3a4;--line-dark:#4a3425;--gold:#e3b35c;--gold2:#8c6127;--teal:#1f9b8c;--green:#2f8f5b;--blue:#3267ba;--red:#b4483f;--chip:#efe1c5;--shadow:0 20px 50px rgba(16,11,8,.28)}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;font-family:Inter,"Noto Sans JP",Meiryo,system-ui,-apple-system,sans-serif;background:linear-gradient(180deg,#151017 0,#261a13 420px,#f0e5cf 421px);color:var(--ink);line-height:1.5;overflow-x:hidden}a{color:#6d4312;text-decoration:none}a:hover{text-decoration:underline}
header{position:sticky;top:0;z-index:18;color:#fff;padding:16px 20px 14px;border-bottom:3px solid var(--gold);background:linear-gradient(135deg,rgba(23,17,28,.98) 0%,rgba(50,32,22,.98) 55%,rgba(16,43,40,.98) 100%);box-shadow:0 8px 24px rgba(20,12,8,.24);backdrop-filter:blur(10px)}header .wrap,main{max-width:1240px;margin:0 auto;width:100%}h1{margin:0 0 6px;font-size:clamp(20px,2.4vw,32px);letter-spacing:0;overflow-wrap:anywhere;line-break:anywhere}.compact-title{display:none}h2{margin:32px 0 12px;font-size:20px;letter-spacing:0;scroll-margin-top:122px}h3{margin:0 0 8px;font-size:15px}p,li,td,th{overflow-wrap:anywhere;word-break:break-word;line-break:anywhere}p{margin:0}.sub{color:#eadfc6;font-size:13px;max-width:940px;overflow-wrap:anywhere;line-break:anywhere}.nav{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}.nav a{color:#fff;border:1px solid rgba(227,179,92,.5);background:rgba(0,0,0,.16);padding:6px 10px;border-radius:6px;font-size:13px}
main{padding:18px 20px 46px}.section-note{color:var(--muted);font-size:13px;margin:-6px 0 12px}.grid4,.grid3,.hero-grid,.source-list,.audit-grid{display:grid;gap:12px}.grid4{grid-template-columns:repeat(4,minmax(0,1fr))}.grid3{grid-template-columns:repeat(3,minmax(0,1fr))}.hero-grid{grid-template-columns:repeat(3,minmax(0,1fr))}.source-list,.audit-grid{grid-template-columns:repeat(2,minmax(0,1fr))}
.panel,.status-card,.hero-card{min-width:0;background:var(--paper2);border:1px solid var(--line);border-radius:8px;padding:14px;box-shadow:0 2px 0 rgba(126,82,28,.08)}a.hero-card{display:block;color:var(--ink);text-decoration:none}.hero-card:hover,.hero-card:focus{outline:2px solid var(--teal);outline-offset:2px}.status-card{background:#21181f;color:#fff;border-color:#5b3a23}.status-card b{display:block;color:var(--gold);font-size:22px;line-height:1.1}.status-card span{display:block;color:#d9c7a9;font-size:12px;margin-top:4px}.panel.keep,.hero-card.keep{border-left:5px solid var(--green)}.panel.synth,.hero-card.synth{border-left:5px solid var(--blue)}.panel.sell{border-left:5px solid var(--gold2)}.panel.warn{border-left:5px solid var(--red)}.small{color:var(--muted);font-size:13px}.rank{display:inline-flex;margin-bottom:8px;padding:2px 7px;border:1px solid var(--line);border-radius:999px;background:var(--chip);font-size:11px;color:#5c4328}ul{padding-left:18px;margin:8px 0 0}li{margin:3px 0}
.toolbar{position:sticky;top:88px;z-index:5;background:rgba(248,240,223,.98);border:1px solid var(--line);border-radius:8px 8px 0 0;padding:10px;display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:0}input[type=search],select{border:1px solid var(--line);border-radius:6px;padding:10px 12px;font-size:14px;background:#fffdf6;color:var(--ink)}input[type=search]{flex:1 1 270px}select{flex:0 1 160px}button{border:1px solid var(--line);background:#fff8e8;color:var(--ink);border-radius:6px;padding:9px 11px;font-size:13px;cursor:pointer}button.active{background:#261a13;color:#fff;border-color:#261a13}.count{color:var(--muted);font-size:13px;margin-left:auto}.item-workbench{border:1px solid var(--line);border-radius:8px;background:#f0dfc1;margin-top:16px}.item-scroll{max-height:min(72vh,860px);overflow:auto;overscroll-behavior:contain;padding:10px}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(232px,1fr));gap:10px}.card{--rarity:#9b8053;min-width:0;background:#fffaf0;border:1px solid var(--line);border-left:4px solid var(--rarity);border-radius:8px;padding:10px;display:block;text-align:left;width:100%;min-height:122px}.card:hover,.card:focus{outline:2px solid var(--teal);outline-offset:1px}.card-top{display:grid;grid-template-columns:52px minmax(0,1fr);gap:10px;align-items:center}.card img,.dialog-head img,td img,.mini-item img{object-fit:contain;image-rendering:pixelated}.card img{width:52px;height:52px;background:#eadbc0;border:1px solid #d1ba92;border-radius:6px}.name{display:block;font-weight:800;font-size:14px;overflow-wrap:anywhere}.en{display:block;color:var(--muted);font-size:12px;overflow-wrap:anywhere}.card-note{display:block;margin-top:7px;color:#614b35;font-size:12px;min-height:18px;overflow-wrap:anywhere}.chips{display:flex;flex-wrap:wrap;gap:4px;margin-top:7px}.chip{display:inline-flex;align-items:center;border-radius:999px;background:var(--chip);color:#4b3924;padding:2px 7px;font-size:11px;line-height:18px;white-space:nowrap}.chip.keep{background:#dff1e4;color:#1f643d}.chip.synth{background:#e2eafe;color:#244f9d}.chip.sell{background:#f8e6b8;color:#68470b}.chip.warn{background:#f8d9d5;color:#8b2d25}.market{color:#68470b;background:#f8e6b8}.special{background:#ead8ff;color:#5c2f84}.rarity{width:10px;height:10px;border-radius:50%;display:inline-block;margin-right:5px;border:1px solid rgba(0,0,0,.25)}
table{width:100%;border-collapse:separate;border-spacing:0;background:#fffaf0;border:1px solid var(--line);border-radius:8px;overflow:hidden}th,td{padding:9px 10px;border-bottom:1px solid var(--line);text-align:left;font-size:13px;vertical-align:top}th{background:#ead8b7;color:#4c3928}tr:last-child td{border-bottom:0}td img{width:34px;height:34px;vertical-align:middle;margin-right:8px}.table-wrap{overflow:auto;margin-top:10px}.scroll-table{max-height:430px;overflow:auto;overscroll-behavior:contain;border:1px solid var(--line);border-radius:8px;background:#fffaf0}.market-scroll{max-height:min(70vh,780px)}.scroll-table table{border:0;border-radius:0}.scroll-table thead th{position:sticky;top:0;z-index:2}.table-item{display:grid;grid-template-columns:38px minmax(0,1fr);gap:8px;align-items:center;min-width:180px}.table-item img{width:34px;height:34px;margin:0;background:#eadbc0;border:1px solid #d1ba92;border-radius:6px;object-fit:contain;image-rendering:pixelated}.effect-cell{font-weight:700;color:#3f2b1a}.effect-cell .en{margin-top:2px}.mini-items{display:flex;flex-wrap:wrap;gap:5px}.mini-item{display:inline-flex;align-items:center;gap:4px;border:1px solid var(--line);border-radius:999px;padding:2px 7px;background:#fffaf0;font-size:12px;white-space:nowrap}.mini-item img{width:22px;height:22px;margin:0}.keep-icon-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(52px,1fr));gap:9px;max-height:min(64vh,620px);overflow:auto;overscroll-behavior:contain;border:1px solid var(--line);border-radius:8px;background:#fffaf0;padding:12px}.keep-icon{display:grid;place-items:center;aspect-ratio:1;border:1px solid var(--line);border-radius:8px;background:#f2e4c8}.keep-icon img{width:42px;height:42px;object-fit:contain;image-rendering:pixelated}.socket-lane{display:grid;grid-template-columns:repeat(8,minmax(120px,1fr));gap:10px;overflow:auto;overscroll-behavior-x:contain;padding-bottom:4px}.socket-card{background:#fffaf0;border:1px solid var(--line);border-radius:8px;padding:12px;min-width:120px}.socket-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin-top:8px}.socket-stats span{background:var(--chip);border-radius:6px;padding:5px 6px;text-align:center;font-size:12px}.material-bands{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:12px}.material-band{background:#fffaf0;border:1px solid var(--line);border-radius:8px;padding:14px}.material-band h3{display:flex;justify-content:space-between;gap:8px;align-items:center}.material-row{margin-top:10px}.material-row b{display:block;margin-bottom:5px;color:#4c3928;font-size:12px}
.hero-card .skill-line{display:flex;flex-wrap:wrap;gap:4px;margin-top:8px}.hero-card .loadout{color:#5b4229;font-size:13px;margin-bottom:8px}.price-note{display:grid;grid-template-columns:1fr auto;gap:10px;align-items:center;background:#21181f;color:#f2e3c6;border:1px solid #5b3a23;border-radius:8px;padding:12px 14px;margin:8px 0 12px}.price-note strong{color:var(--gold)}.price-note span{font-size:12px;color:#d5c0a0}
.modal{position:fixed;inset:0;display:none;align-items:center;justify-content:center;padding:18px;background:rgba(19,12,8,.64);z-index:20}.modal.open{display:flex}.dialog{width:min(820px,100%);max-height:90vh;overflow:auto;background:#fffaf0;border-radius:8px;box-shadow:var(--shadow);border:1px solid var(--line-dark)}.dialog-head{display:grid;grid-template-columns:72px 1fr auto;gap:12px;align-items:center;padding:16px;border-bottom:1px solid var(--line);background:#f2dfbd}.dialog-head img{width:72px;height:72px;background:#eadbc0;border:1px solid #d1ba92;border-radius:8px}.dialog-body{padding:16px}.detail-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}.close{font-size:20px;line-height:1;width:36px;height:36px;padding:0}footer{margin-top:28px;color:var(--muted);font-size:12px;text-align:center}
@media(max-width:980px){.grid4,.grid3,.hero-grid,.source-list,.audit-grid{grid-template-columns:1fr 1fr}.detail-grid{grid-template-columns:1fr}}@media(max-width:640px){body{background:linear-gradient(180deg,#151017 0,#261a13 520px,#f0e5cf 521px)}header{padding:12px 16px}header .wrap{width:calc(100vw - 32px);max-width:calc(100vw - 32px);min-width:0;margin:0}.nav{display:grid;width:calc(100vw - 32px);grid-template-columns:repeat(3,minmax(0,1fr));gap:7px}.nav a{min-width:0;text-align:center;font-size:12px;padding:6px 7px;white-space:nowrap}main{width:100vw;max-width:100vw;min-width:0;margin:0;padding:14px 16px 36px;overflow-x:hidden}.wide-title{display:none}.compact-title{display:inline}.grid4,.grid3,.hero-grid,.source-list,.audit-grid{width:calc(100vw - 32px);max-width:calc(100vw - 32px);grid-template-columns:minmax(0,1fr)}.panel,.status-card,.hero-card,.item-workbench,.price-note,.table-wrap,.scroll-table,.material-band{max-width:calc(100vw - 32px);min-width:0}.toolbar{position:static}.cards{grid-template-columns:minmax(0,1fr)}input[type=search],select{width:100%;flex:1 1 100%}.count{width:100%;margin-left:0}.price-note{grid-template-columns:1fr}.item-scroll{max-height:68vh}.dialog-head{grid-template-columns:56px 1fr auto}.dialog-head img{width:56px;height:56px}h1,.sub,p,li{word-break:break-all;line-break:anywhere}}
"""


def html_template(data: dict) -> str:
    data_json = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    template = """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TBH 素材・装備メモ</title>
<style>__CSS__</style>
</head>
<body>
<header>
  <div class="wrap">
    <h1><span class="wide-title">TBH 素材・装備メモ</span><span class="compact-title">TBH 素材・装備メモ</span></h1>
    <p class="sub">更新: __TODAY__ / 価格は日本円。ゲーム内データと市場情報を分けて整理。</p>
    <nav class="nav">
      <a href="#heroes">キャラクター</a><a href="keep-materials.html">残す素材</a><a href="#stats">数値表</a><a href="#specials">特殊装備</a><a href="#items">アイテム</a><a href="#market">価格</a>
    </nav>
  </div>
</header>
<main>
  <section id="rules" class="grid4">
    <div class="panel keep"><h3>残す</h3><p>進行素材・高等級・主力付与・高値品。</p></div>
    <div class="panel synth"><h3>合成</h3><p>同等級装備9個。コズミックは合成不可。</p></div>
    <div class="panel sell"><h3>売却</h3><p>低級余剰、ビルド外重複、安値の付与なし装備。</p></div>
    <div class="panel warn"><h3>注意</h3><p>付与済み装備は取引不可。素材は戻らない。</p></div>
  </section>

  <h2 id="heroes">キャラクター別メモ</h2>
  <p class="section-note">キャラクターごとに装備、残す素材、特殊装備を分けています。</p>
  <section class="hero-grid" id="heroCards"></section>

  <h2 id="tiers">クラフト/売却判断表</h2>
  <section class="grid4" id="tierCards"></section>

  <h2>ビルド別に残すステータス</h2>
  <section class="grid3" id="buildCards"></section>

  <h2 id="stats">数値付きステータス表</h2>
  <p class="section-note">装飾/彫刻素材を装備スロットへ入れた時の数値。コミュニティガイド由来のため、パッチ差分がある場合はゲーム内表示を優先。</p>
  <div class="toolbar">
    <select id="effectKindFilter" aria-label="効果種類">
      <option value="all">装飾 + 彫刻</option>
      <option value="decorations">装飾だけ</option>
      <option value="engravings">彫刻だけ</option>
    </select>
    <input id="effectQ" type="search" placeholder="物理ダメージ / 攻撃速度 / 火ダメージ / 詠唱速度 など">
    <span class="count" id="effectCount"></span>
  </div>
  <div class="scroll-table"><table id="effectTable"><thead><tr><th>素材</th><th>種類</th><th>等級</th><th>武器/サブ武器</th><th>防具/ブーツ</th><th>アクセ</th></tr></thead><tbody></tbody></table></div>

  <h2 id="specials">特殊装備まとめ</h2>
  <p class="section-note">一定レア度以上で出るユニーク効果。ソーサラーはスタッフ/オーブ/ヘルメット中心、ブーツは共通特殊効果も確認。</p>
  <div class="toolbar">
    <select id="specialClassFilter" aria-label="特殊装備クラス">
      <option value="all">全クラス</option>
      <option value="ranger">レンジャー</option>
      <option value="sorcerer">ソーサラー</option>
      <option value="priest">プリースト</option>
      <option value="hunter">ハンター</option>
      <option value="slayer">スレイヤー</option>
      <option value="knight">ナイト</option>
      <option value="universal">共通</option>
    </select>
    <input id="specialQ" type="search" placeholder="オーブ / ブーツ / ヒドラ / 投射物 など">
    <span class="count" id="specialCount"></span>
  </div>
  <div class="scroll-table"><table id="specialTable"><thead><tr><th>クラス</th><th>装備</th><th>レベル</th><th>必要等級</th><th>効果</th></tr></thead><tbody></tbody></table></div>

  <h2>ソケット解放目安</h2>
  <p class="section-note">コミュニティガイドを補助情報として使った目安です。パッチ差分があるため、ゲーム内表示を優先してください。</p>
  <section class="socket-lane" id="socketCards"></section>

  <h2 id="materials">素材とレベル帯</h2>
  <p class="section-note">保持判断用の整理表です。個別要求数は静的ローカライズ表だけでは確定できないため、ゲーム内レシピ確認を前提にしています。</p>
  <section class="material-bands" id="materialBands"></section>

  <h2 id="items">素材・装備一覧</h2>
  <p class="section-note">この枠だけ独立スクロールします。ページ全体を動かしたい時は枠の外でスクロール。</p>
  <section class="item-workbench">
    <div class="toolbar">
      <input id="q" type="search" placeholder="日本語名・英語名・用途・数値・特殊効果で検索">
      <select id="categoryFilter" aria-label="分類">
        <option value="all">分類: すべて</option>
        <option value="material">素材すべて</option>
        <option value="crafting">クラフト素材</option>
        <option value="decoration">装飾素材</option>
        <option value="engraving">彫刻素材</option>
        <option value="inscription">刻印素材</option>
        <option value="weapon">武器</option>
        <option value="armor">防具</option>
        <option value="accessory">アクセ</option>
        <option value="special">特殊効果あり</option>
        <option value="marketed">市場あり</option>
      </select>
      <select id="buildFilter" aria-label="ビルド">
        <option value="all">ビルド: すべて</option>
        <option value="ranger">レンジャー向け</option>
        <option value="sorcerer">ソーサラー向け</option>
        <option value="priest">プリースト向け</option>
        <option value="hunter">ハンター向け</option>
        <option value="slayer">スレイヤー向け</option>
        <option value="physical">物理/速度</option>
        <option value="magic">魔法/属性</option>
        <option value="defense">防御/耐久</option>
      </select>
      <select id="gradeFilter" aria-label="等級">
        <option value="all">等級: すべて</option>
      </select>
      <select id="actionFilter" aria-label="判断">
        <option value="all">判断: すべて</option>
        <option value="keep">残す</option>
        <option value="synth">合成/ビルド</option>
        <option value="sell">売却候補</option>
        <option value="warn">価格/注意</option>
      </select>
      <button id="resetFilters" type="button">解除</button>
      <span class="count" id="count"></span>
    </div>
    <section class="cards item-scroll" id="cards"></section>
  </section>

  <h2 id="market">市場価格</h2>
  <div class="price-note"><div><strong>日本円で定期更新</strong><br><span>最低価格・中央値・取引量を取得。現在の最高売注文は安定取得できないため、サイト上では未取得と表示します。</span></div><span id="marketUpdated"></span></div>
  <div class="scroll-table market-scroll"><table id="marketTable"><thead><tr><th>アイテム</th><th>分類</th><th>等級</th><th>最低価格</th><th>中央値</th><th>最高値</th><th>量/出品</th></tr></thead><tbody></tbody></table></div>

  <footer>データ: ゲーム内データ / 市場価格 / コミュニティガイド</footer>
</main>

<div class="modal" id="modal" aria-hidden="true">
  <div class="dialog" role="dialog" aria-modal="true" aria-labelledby="modalTitle">
    <div class="dialog-head">
      <img id="modalIcon" alt="">
      <div>
        <div class="name" id="modalTitle"></div>
        <div class="en" id="modalSub"></div>
        <div class="chips" id="modalChips"></div>
      </div>
      <button class="close" id="modalClose" aria-label="閉じる">×</button>
    </div>
    <div class="dialog-body" id="modalBody"></div>
  </div>
</div>

<script>
const DATA=__DATA_JSON__;
const ITEMS=DATA.items, MARKET=DATA.market, HEROES=DATA.heroes, GUIDE=DATA.guideEffects;
const MATERIAL_BANDS=DATA.materialBands, TIER_TABLE=DATA.tierTable, BUILD_TABLE=DATA.buildTable, SOCKET_TABLE=DATA.socketTable;
const rarityColor=DATA.rarityColor, gradeJa=DATA.gradeJa, gradeOrder=DATA.gradeOrder;
const filters={category:'all',build:'all',grade:'all',action:'all'};
const cards=document.getElementById('cards'),count=document.getElementById('count'),q=document.getElementById('q');
const categoryFilter=document.getElementById('categoryFilter'),buildFilter=document.getElementById('buildFilter'),gradeFilter=document.getElementById('gradeFilter'),actionFilter=document.getElementById('actionFilter');
const modal=document.getElementById('modal'), modalClose=document.getElementById('modalClose');
const itemByEn=new Map(ITEMS.map(it=>[it.en,it]));
function esc(s){return String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}
function actionClass(a){if(a.includes('必ず')||a.includes('残'))return 'keep';if(a.includes('合成')||a.includes('ビルド'))return 'synth';if(a.includes('価格')||a.includes('祈願'))return 'warn';return 'sell';}
function gradeChip(g){return g?`<span class="chip"><span class="rarity" style="background:${rarityColor[g]||'#ddd'}"></span>${esc(gradeJa[g]||g)}</span>`:'';}
function itemForName(name){return itemByEn.get(String(name||'').replace(/ \\(.+\\)$/,''));}
function tableItem(it,fallback){return `<span class="table-item">${it?.icon?`<img src="${esc(it.icon)}" alt="">`:''}<span><strong>${esc(it?.ja||fallback||'-')}</strong></span></span>`;}
function effectCell(ja,en){return `<div class="effect-cell">${esc(ja||en||'-')}</div>`;}
function categoryMatch(it){const c=filters.category;if(c==='all')return true;if(c==='marketed')return it.marketCount>0;if(c==='special')return it.specialCount>0;if(c==='weapon')return it.class.includes('gear weapon');if(c==='armor')return it.class.includes('armor');if(c==='accessory')return it.class.includes('accessory');return it.class.includes(c);}
function buildMatch(it){const b=filters.build;if(b==='all')return true;const rec=(it.recommended||[]).join(' ');if(b==='ranger')return rec.includes('レンジャー');if(b==='sorcerer')return rec.includes('ソーサラー');if(b==='priest')return rec.includes('プリースト');if(b==='hunter')return rec.includes('ハンター');if(b==='slayer')return rec.includes('スレイヤー');if(b==='physical')return it.tags.includes('物理/攻撃速度');if(b==='magic')return it.tags.includes('魔法/属性');if(b==='defense')return it.tags.includes('防御/耐久');return true;}
function passFilter(it){return categoryMatch(it)&&buildMatch(it)&&(filters.grade==='all'||it.grade===filters.grade)&&(filters.action==='all'||actionClass(it.action)===filters.action);}
function searchable(it){return [it.ja,it.en,it.category,it.action,it.grade,gradeJa[it.grade],it.sellAdvice,it.tierBand,it.desc,it.effectText,(it.recommended||[]).join(' '),...(it.tags||[]),...(it.uses||[]),...(it.specials||[]).map(s=>`${s.class} ${s.item} ${s.effect} ${s.grade} ${s.level}`)].join(' ').toLowerCase();}
function renderMiniItems(ids){return `<div class="mini-items">${ids.map(id=>{const it=ITEMS.find(x=>x.id===id);return it?`<span class="mini-item"><img src="${esc(it.icon)}" alt="">${esc(it.ja)}</span>`:'';}).join('')}</div>`;}
function renderHeroCards(){document.getElementById('heroCards').innerHTML=HEROES.map((h,i)=>`<a class="hero-card ${i%3===0?'keep':i%3===1?'synth':'warn'}" href="${esc(h.page)}"><span class="rank">${esc(h.role)}</span><h3>${esc(h.ja)}</h3><p class="loadout">${esc(h.gear)}</p><p class="small">${esc(h.desc)}</p><div class="skill-line">${h.skills.map(s=>`<span class="chip">${esc(s.ja)}</span>`).join('')}</div><ul><li>残す: ${esc(h.keep)}</li><li>売却候補: ${esc(h.sell)}</li></ul><p class="small" style="margin-top:10px">個別ページを見る</p></a>`).join('');}
function decisionClass(t){if(t.tier.includes('残す'))return 'keep';if(t.tier.includes('必要'))return 'synth';if(t.tier.includes('余剰'))return 'sell';return 'warn';}
function renderTierCards(){document.getElementById('tierCards').innerHTML=TIER_TABLE.map(t=>`<div class="panel ${decisionClass(t)}"><span class="rank">${esc(t.tier)}</span><h3>${esc(t.label)}</h3><p>${esc(t.target)}</p><p class="small" style="margin-top:8px">${esc(t.reason)}</p></div>`).join('');}
function renderBuildCards(){document.getElementById('buildCards').innerHTML=BUILD_TABLE.map(b=>`<div class="panel"><h3>${esc(b.name)}</h3><p class="small">${esc(b.classes)}</p><ul><li>残す: ${esc(b.keep)}</li><li>売却候補: ${esc(b.sell)}</li></ul></div>`).join('');}
function renderSocketTable(){document.getElementById('socketCards').innerHTML=SOCKET_TABLE.map(r=>`<article class="socket-card">${gradeChip(r.grade)}<div class="socket-stats"><span>装飾<br><b>${r.deco}</b></span><span>彫刻<br><b>${r.engraving||0}</b></span><span>刻印<br><b>${r.inscription||0}</b></span></div></article>`).join('');}
function renderMaterialTable(){document.getElementById('materialBands').innerHTML=MATERIAL_BANDS.map(b=>`<article class="material-band"><h3>${esc(b.range)} <span class="rank">${esc(b.tier)}</span></h3><div class="material-row"><b>クラフト素材</b>${renderMiniItems(b.crafting)}</div><div class="material-row"><b>装飾</b>${renderMiniItems(b.deco)}</div><div class="material-row"><b>彫刻</b>${renderMiniItems(b.engraving)}</div><div class="material-row"><b>刻印</b>${renderMiniItems(b.inscription)}</div><p class="small" style="margin-top:10px">${esc(b.advice)}</p></article>`).join('');}
function effectRows(){return [...(GUIDE.decorations||[]).map(r=>{const it=itemForName(r.Gem);return {kind:'装飾',name:r.Gem,item:it,grade:r.Grade,weapon:r.Weapon,armor:r.Armor,accessory:r.Accessory,weaponJa:r.WeaponJa||r.Weapon,armorJa:r.ArmorJa||r.Armor,accessoryJa:r.AccessoryJa||r.Accessory};}),...(GUIDE.engravings||[]).map(r=>{const it=itemForName(r.Engraving);return {kind:'彫刻',name:r.Engraving,item:it,grade:r.Grade,weapon:r.Weapon,armor:r.Armor,accessory:r.Accessory,weaponJa:r.WeaponJa||r.Weapon,armorJa:r.ArmorJa||r.Armor,accessoryJa:r.AccessoryJa||r.Accessory};})];}
function specialRows(){return Object.entries(GUIDE.uniqueMods||{}).flatMap(([classKey,rows])=>rows.map(r=>{const it=itemForName(r.Item);return {classKey,className:({knight:'ナイト',universal:'共通',ranger:'レンジャー',sorcerer:'ソーサラー',priest:'プリースト',hunter:'ハンター',slayer:'スレイヤー'}[classKey]||classKey),itemData:it,...r};}));}
function renderEffectTable(){const kind=document.getElementById('effectKindFilter').value;const term=document.getElementById('effectQ').value.trim().toLowerCase();const rows=effectRows().filter(r=>kind==='all'||(kind==='decorations'?r.kind==='装飾':r.kind==='彫刻')).filter(r=>!term||[r.item?.ja,r.name,r.kind,r.grade,r.weapon,r.armor,r.accessory,r.weaponJa,r.armorJa,r.accessoryJa].join(' ').toLowerCase().includes(term));document.querySelector('#effectTable tbody').innerHTML=rows.map(r=>`<tr><td>${tableItem(r.item,r.name)}</td><td>${esc(r.kind)}</td><td>${gradeChip(r.grade)||esc(r.grade)}</td><td>${effectCell(r.weaponJa,r.weapon)}</td><td>${effectCell(r.armorJa,r.armor)}</td><td>${effectCell(r.accessoryJa,r.accessory)}</td></tr>`).join('');document.getElementById('effectCount').textContent=`${rows.length}件`;}
function renderSpecialTable(){const cls=document.getElementById('specialClassFilter').value;const term=document.getElementById('specialQ').value.trim().toLowerCase();const rows=specialRows().filter(r=>cls==='all'||r.classKey===cls).filter(r=>!term||[r.className,r.itemData?.ja,r.Item,r.Lv,r.Grade,r.Effect,r.EffectJa].join(' ').toLowerCase().includes(term));document.querySelector('#specialTable tbody').innerHTML=rows.map(r=>`<tr><td>${esc(r.className)}</td><td>${tableItem(r.itemData,r.Item)}</td><td>${esc(r.Lv)}</td><td>${gradeChip(r.Grade)||esc(r.Grade)}</td><td>${effectCell(r.EffectJa||r.Effect,r.Effect)}</td></tr>`).join('');document.getElementById('specialCount').textContent=`${rows.length}件`;}
function setupGradeFilter(){gradeOrder.forEach(g=>{const opt=document.createElement('option');opt.value=g;opt.textContent=`等級: ${gradeJa[g]||g}`;gradeFilter.appendChild(opt);});}
function renderCards(){const term=q.value.trim().toLowerCase();const list=ITEMS.filter(it=>passFilter(it)).filter(it=>!term||searchable(it).includes(term));cards.innerHTML=list.map(it=>{const market=it.market.slice(0,2).map(m=>`<span class="chip market"><span class="rarity" style="background:#${esc(m.color||'ddd')}"></span>${esc(m.price)}</span>`).join('');const rec=(it.recommended||[]).slice(0,2).map(r=>`<span class="chip">${esc(r)}</span>`).join('');const special=it.specialCount?`<span class="chip special">特殊${it.specialCount}</span>`:'';const note=it.effectText||it.specials?.[0]?.effectJa||it.tierBand||it.uses[0]||it.sellAdvice;return `<button class="card" data-id="${it.id}" style="--rarity:${rarityColor[it.grade]||'#a8894c'}"><span class="card-top"><img src="${esc(it.icon)}" alt="${esc(it.ja)}" loading="lazy"><span><span class="name">${esc(it.ja)}</span></span></span><span class="chips"><span class="chip ${actionClass(it.action)}">${esc(it.action)}</span><span class="chip">${esc(it.category)}</span>${gradeChip(it.grade)}${rec}${special}${it.tags.slice(0,2).map(t=>`<span class="chip">${esc(t)}</span>`).join('')}${market}</span><span class="card-note">${esc(note)}</span></button>`;}).join('');count.textContent=`${list.length} / ${ITEMS.length}件`;}
function displayDate(s){return String(s||'').replace('T',' ').replace('Z','');}
function renderMarket(){document.getElementById('marketUpdated').textContent=DATA.marketUpdatedAt?`最終取得: ${displayDate(DATA.marketUpdatedAt)}`:'価格取得日: 未記録';document.querySelector('#marketTable tbody').innerHTML=MARKET.map(m=>{const it=ITEMS.find(x=>x.id===m.id);return `<tr><td><span class="table-item">${m.image?`<img src="${esc(m.image)}" alt="">`:it?.icon?`<img src="${esc(it.icon)}" alt="">`:''}<span><strong>${esc(it?.ja||m.base)}</strong></span></span></td><td>${esc(m.type)}</td><td>${gradeChip(m.grade)||'-'}</td><td>${esc(m.price)}</td><td>${esc(m.medianPrice||'-')}</td><td title="${esc(m.highestNote||'公開API未取得')}">${esc(m.highestPrice||'未取得')}</td><td>${esc(m.volume||'-')} / ${esc(m.listings)}</td></tr>`}).join('');}
function openDetail(id){const it=ITEMS.find(x=>x.id===Number(id));if(!it)return;document.getElementById('modalIcon').src=it.icon;document.getElementById('modalIcon').alt=it.ja;document.getElementById('modalTitle').textContent=it.ja;document.getElementById('modalSub').textContent=`${it.category}${it.level?' / レベル '+it.level:''}`;document.getElementById('modalChips').innerHTML=`<span class="chip ${actionClass(it.action)}">${esc(it.action)}</span>${gradeChip(it.grade)}${(it.recommended||[]).map(t=>`<span class="chip">${esc(t)}</span>`).join('')}${it.specialCount?`<span class="chip special">特殊${it.specialCount}</span>`:''}${it.tags.map(t=>`<span class="chip">${esc(t)}</span>`).join('')}`;const effectHtml=it.effect?`<div class="panel" style="margin-top:12px"><h3>${esc(it.effect.kind)}の数値</h3><table><thead><tr><th>武器/サブ</th><th>防具/ブーツ</th><th>アクセ</th></tr></thead><tbody><tr><td>${effectCell(it.effect.weaponJa,it.effect.weapon)}</td><td>${effectCell(it.effect.armorJa,it.effect.armor)}</td><td>${effectCell(it.effect.accessoryJa,it.effect.accessory)}</td></tr></tbody></table></div>`:'';const specialHtml=it.specials?.length?`<div class="panel" style="margin-top:12px"><h3>特殊効果</h3><table><thead><tr><th>対象</th><th>レベル</th><th>必要等級</th><th>効果</th></tr></thead><tbody>${it.specials.map(s=>`<tr><td>${esc(s.class)} / ${esc(s.slotJa||s.slot)}</td><td>${esc(s.level)}</td><td>${gradeChip(s.grade)||esc(s.grade)}</td><td>${effectCell(s.effectJa||s.effect,s.effect)}</td></tr>`).join('')}</tbody></table></div>`:'';const marketHtml=it.market.length?`<div class="table-wrap"><table><thead><tr><th>市場名</th><th>最低</th><th>中央値</th><th>最高</th><th>量/出品</th></tr></thead><tbody>${it.market.map(m=>`<tr><td>${esc(it.ja)}</td><td>${esc(m.price)}</td><td>${esc(m.medianPrice||'-')}</td><td title="${esc(m.highestNote||'公開API未取得')}">${esc(m.highestPrice||'未取得')}</td><td>${esc(m.volume||'-')} / ${esc(m.listings)}</td></tr>`).join('')}</tbody></table></div>`:'<p class="small">現在の取得データでは市場掲載なし。</p>';document.getElementById('modalBody').innerHTML=`<div class="detail-grid"><div class="panel"><h3>用途</h3><ul>${it.uses.map(u=>`<li>${esc(u)}</li>`).join('')}</ul></div><div class="panel"><h3>売却判断</h3><p>${esc(it.sellAdvice)}</p><p class="small" style="margin-top:8px">関連帯: ${esc(it.tierBand||'-')}</p></div></div>${effectHtml}${specialHtml}${it.desc?`<div class="panel" style="margin-top:12px"><h3>ゲーム内説明</h3><p>${esc(it.desc)}</p></div>`:''}<div class="panel" style="margin-top:12px"><h3>市場価格</h3>${marketHtml}</div>`;modal.classList.add('open');modal.setAttribute('aria-hidden','false');modalClose.focus();}
cards.addEventListener('click',e=>{const btn=e.target.closest('.card');if(btn)openDetail(btn.dataset.id);});
[categoryFilter,buildFilter,gradeFilter,actionFilter].forEach(el=>el.addEventListener('change',()=>{filters.category=categoryFilter.value;filters.build=buildFilter.value;filters.grade=gradeFilter.value;filters.action=actionFilter.value;renderCards();}));
document.getElementById('resetFilters').addEventListener('click',()=>{q.value='';categoryFilter.value=buildFilter.value=gradeFilter.value=actionFilter.value='all';filters.category=filters.build=filters.grade=filters.action='all';renderCards();});
q.addEventListener('input',renderCards);document.getElementById('effectKindFilter').addEventListener('change',renderEffectTable);document.getElementById('effectQ').addEventListener('input',renderEffectTable);document.getElementById('specialClassFilter').addEventListener('change',renderSpecialTable);document.getElementById('specialQ').addEventListener('input',renderSpecialTable);
modalClose.addEventListener('click',()=>{modal.classList.remove('open');modal.setAttribute('aria-hidden','true');});modal.addEventListener('click',e=>{if(e.target===modal)modalClose.click();});window.addEventListener('keydown',e=>{if(e.key==='Escape'&&modal.classList.contains('open'))modalClose.click();});
setupGradeFilter();renderHeroCards();renderTierCards();renderBuildCards();renderEffectTable();renderSpecialTable();renderSocketTable();renderMaterialTable();renderCards();renderMarket();
</script>
</body>
</html>
"""
    return (
        template.replace("__CSS__", css())
        .replace("__TODAY__", date.today().isoformat())
        .replace("__DATA_JSON__", data_json)
    )


def h(value) -> str:
    return escape(str(value or ""), quote=True)


def grade_chip_static(grade: str | None) -> str:
    if not grade:
        return ""
    color = RARITY_COLOR.get(grade, "#ddd")
    label = GRADE_JA.get(grade, grade)
    return f'<span class="chip"><span class="rarity" style="background:{h(color)}"></span>{h(label)}</span>'


def static_item_card(item: dict, prefix: str = "") -> str:
    chips = [
        f'<span class="chip {h(action_class_static(item["action"]))}">{h(item["action"])}</span>',
        f'<span class="chip">{h(item["category"])}</span>',
        grade_chip_static(item.get("grade")),
    ]
    chips.extend(f'<span class="chip">{h(tag)}</span>' for tag in item.get("tags", [])[:2])
    if item.get("market"):
        chips.append(f'<span class="chip market">{h(item["market"][0]["price"])}</span>')
    note = item.get("effectText") or (item.get("specials") or [{}])[0].get("effectJa") or item.get("tierBand") or item.get("sellAdvice")
    return f"""
<article class="card" style="--rarity:{h(RARITY_COLOR.get(item.get("grade"), "#a8894c"))}">
  <span class="card-top"><img src="{h(prefix + item["icon"])}" alt="{h(item["ja"])}" loading="lazy"><span><span class="name">{h(item["ja"])}</span></span></span>
  <span class="chips">{''.join(chips)}</span>
  <span class="card-note">{h(note)}</span>
</article>
"""


def action_class_static(action: str) -> str:
    if "必ず" in action or "残" in action:
        return "keep"
    if "合成" in action or "ビルド" in action:
        return "synth"
    if "価格" in action or "祈願" in action:
        return "warn"
    return "sell"


def hero_related_items(hero: dict, items: list[dict]) -> list[dict]:
    slug = hero["slug"]
    related = []
    for item in items:
        if hero["ja"] in item.get("recommended", []):
            related.append(item)
            continue
        if any(s.get("classKey") in {slug, "universal"} for s in item.get("specials", [])):
            related.append(item)
    return related


def hero_special_rows(hero: dict, items: list[dict]) -> list[tuple[dict, dict]]:
    slug = hero["slug"]
    rows: list[tuple[dict, dict]] = []
    for item in items:
        for special in item.get("specials", []):
            if special.get("classKey") in {slug, "universal"}:
                rows.append((item, special))
    return rows


AFFIX_SLOTS = [
    ("weapon", "武器/サブ武器", "weaponJa"),
    ("armor", "防具/ブーツ", "armorJa"),
    ("accessory", "アクセ", "accessoryJa"),
]


def matched_keywords(text: str, keywords: list[str]) -> list[str]:
    found = []
    for keyword in keywords:
        if keyword in text and keyword not in found:
            found.append(keyword)
    return found


def hero_affix_items(hero: dict, items: list[dict]) -> list[dict]:
    targets = HERO_AFFIX_TARGETS.get(hero["slug"], {})
    rows = []
    for item in items:
        effect = item.get("effect")
        if not effect or effect.get("kind") not in {"装飾", "彫刻"}:
            continue
        slot_matches = []
        for slot_key, slot_label, effect_key in AFFIX_SLOTS:
            text = effect.get(effect_key, "")
            keywords = matched_keywords(text, targets.get(slot_key, []))
            if keywords:
                slot_matches.append({"slot": slot_label, "keywords": keywords, "text": text})
        if slot_matches:
            rows.append({"item": item, "matches": slot_matches, "score": sum(len(m["keywords"]) for m in slot_matches)})
    return sorted(
        rows,
        key=lambda row: (
            GRADE_ORDER.index(row["item"].get("grade")) if row["item"].get("grade") in GRADE_ORDER else 99,
            0 if row["item"].get("effect", {}).get("kind") == "装飾" else 1,
            row["item"].get("ja", ""),
        ),
    )


def affix_reason(matches: list[dict]) -> str:
    parts = []
    for match in matches:
        keywords = "・".join(match["keywords"][:3])
        parts.append(f'{match["slot"]}: {keywords}')
    return " / ".join(parts)


def static_affix_rows(rows: list[dict]) -> str:
    if not rows:
        return '<tr><td colspan="7">該当する付与素材はまだ整理中です。</td></tr>'
    return "\n".join(
        f"""<tr>
  <td><span class="table-item"><img src="{h('../' + row['item']['icon'])}" alt="{h(row['item']['ja'])}"><span><strong>{h(row['item']['ja'])}</strong></span></span></td>
  <td>{h(row['item'].get('effect', {}).get('kind'))}</td>
  <td>{grade_chip_static(row['item'].get('grade'))}</td>
  <td>{h(affix_reason(row['matches']))}</td>
  <td><div class="effect-cell">{h(row['item'].get('effect', {}).get('weaponJa'))}</div></td>
  <td><div class="effect-cell">{h(row['item'].get('effect', {}).get('armorJa'))}</div></td>
  <td><div class="effect-cell">{h(row['item'].get('effect', {}).get('accessoryJa'))}</div></td>
</tr>"""
        for row in rows
    )


def static_affix_summary(rows: list[dict], limit: int = 14) -> str:
    chips = []
    seen = set()
    for row in rows:
        name = row["item"].get("ja", "")
        if not name or name in seen:
            continue
        seen.add(name)
        chips.append(f'<span class="chip">{h(name)}</span>')
        if len(chips) >= limit:
            break
    if not chips:
        return '<p class="small">残す付与素材はまだ整理中です。</p>'
    return f'<div class="chips keep-list">{"".join(chips)}</div>'


def level_value(item: dict) -> int | None:
    level = item.get("level")
    if isinstance(level, int):
        return level
    try:
        return int(level)
    except (TypeError, ValueError):
        return None


def row_level_text(item: dict) -> str:
    level = level_value(item)
    if level is not None:
        return f"レベル {level}"
    return item.get("tierBand") or "-"


def keep_price(item: dict) -> str:
    market = item.get("market") or []
    if market:
        return market[0].get("price") or "-"
    return "-"


def keep_use_text(item: dict) -> str:
    uses = item.get("uses") or []
    return " / ".join(uses[:2]) if uses else "-"


def keep_material_icon(item: dict) -> str:
    return f'<span class="keep-icon"><img src="{h(item["icon"])}" alt=""></span>'


def unique_items(items: list[dict]) -> list[dict]:
    seen = set()
    result = []
    for item in items:
        if item["id"] in seen:
            continue
        seen.add(item["id"])
        result.append(item)
    return result


def material_band_items(items_by_id: dict[int, dict], ranges: set[str], keys: tuple[str, ...]) -> list[dict]:
    result = []
    for band in MATERIAL_BANDS:
        if band["range"] not in ranges:
            continue
        for key in keys:
            result.extend(items_by_id[iid] for iid in band[key] if iid in items_by_id)
    return result


def keep_material_sections(items: list[dict]) -> list[dict]:
    items_by_id = {item["id"]: item for item in items}
    craft_items = sorted(
        [item for item in items if item["id"] // 1000 in CRAFTING_MATERIAL_PREFIXES],
        key=lambda item: item["id"],
    )
    low_items = material_band_items(items_by_id, {"レベル 1-10", "レベル 15-30"}, ("crafting",))
    high_items = material_band_items(
        items_by_id,
        {"レベル 65", "レベル 80+"},
        ("crafting", "deco", "engraving", "inscription"),
    )
    all_items = unique_items(craft_items + low_items + high_items)
    sections = [
        {
            "id": "all",
            "title": "残す素材",
            "note": "対象素材を全部まとめた一覧。表示はアイコンだけです。",
            "items": all_items,
        },
        {
            "id": "craft",
            "title": "作成用（全レベル）",
            "note": "キューブ作成用に残す素材。",
            "items": craft_items,
        },
        {
            "id": "low",
            "title": "レベル10〜20 作成素材",
            "note": "序盤の作成で残す素材。",
            "items": low_items,
        },
        {
            "id": "high",
            "title": "レベル65〜80+",
            "note": "高レベル帯で残す素材。",
            "items": high_items,
        },
    ]
    return sections


def keep_materials_page_template(data: dict) -> str:
    section_html = []
    for section in keep_material_sections(data["items"]):
        icons = "\n".join(keep_material_icon(item) for item in section["items"])
        if not icons:
            icons = '<p class="small">該当する素材はまだ整理中です。</p>'
        section_html.append(
            f"""
  <h2 id="{h(section['id'])}">{h(section['title'])}</h2>
  <p class="section-note">{h(section['note'])}</p>
  <section class="keep-icon-grid">{icons}</section>
"""
        )
    body = f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>残す素材一覧 - TBH 素材・装備メモ</title>
<style>{css()}</style>
</head>
<body>
<header>
  <div class="wrap">
    <h1>残す素材一覧</h1>
    <p class="sub">残す素材だけをアイコンでまとめた一覧。</p>
    <nav class="nav">
      <a href="index.html">一覧へ戻る</a><a href="#all">全部</a><a href="#craft">作成用</a><a href="#low">10〜20</a><a href="#high">65〜80+</a>
    </nav>
  </div>
</header>
<main>
  <section class="grid3">
    <div class="panel keep"><h3>全部</h3><p>残す対象をまとめて表示。</p></div>
    <div class="panel synth"><h3>作成用</h3><p>全レベル分を残す。</p></div>
    <div class="panel warn"><h3>高レベル</h3><p>65〜80+を残す。</p></div>
  </section>
  {''.join(section_html)}
  <footer>データ: ゲーム内データ / 市場価格 / コミュニティガイド</footer>
</main>
</body>
</html>
"""
    return body


def write_keep_materials_page(data: dict) -> None:
    (ROOT / "keep-materials.html").write_text(keep_materials_page_template(data), encoding="utf-8", newline="\n")


def character_page_template(data: dict, hero: dict) -> str:
    items = data["items"]
    related = hero_related_items(hero, items)
    specials = hero_special_rows(hero, items)
    affixes = hero_affix_items(hero, items)
    related_cards = "\n".join(static_item_card(item, "../") for item in related[:120])
    if not related_cards:
        related_cards = '<p class="small">関連アイテムはまだ整理中です。</p>'
    affix_rows = static_affix_rows(affixes[:90])
    affix_summary = static_affix_summary(affixes)
    special_rows = "\n".join(
        f"""<tr>
  <td><span class="table-item"><img src="{h('../' + item['icon'])}" alt="{h(item['ja'])}"><span><strong>{h(item['ja'])}</strong></span></span></td>
  <td>{h(special.get('level'))}</td>
  <td>{grade_chip_static(special.get('grade'))}</td>
  <td>{h(special.get('slotJa') or special.get('slot'))}</td>
  <td><div class="effect-cell">{h(special.get('effectJa') or special.get('effect'))}</div></td>
</tr>"""
        for item, special in specials
    )
    if not special_rows:
        special_rows = '<tr><td colspan="5">該当する特殊装備はまだ整理中です。</td></tr>'
    skills = "".join(f'<span class="chip">{h(skill["ja"])}</span>' for skill in hero.get("skills", []))
    body = f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{h(hero["ja"])} - TBH 素材・装備メモ</title>
<style>{css()}</style>
</head>
<body>
<header>
  <div class="wrap">
    <h1>{h(hero["ja"])} メモ</h1>
    <p class="sub">装備、残す素材、特殊装備をキャラクター別に整理。</p>
    <nav class="nav">
      <a href="../index.html">一覧へ戻る</a><a href="../keep-materials.html">残す素材</a><a href="#affixes">残す付与素材</a><a href="#specials">特殊装備</a>
    </nav>
  </div>
</header>
<main>
  <section class="detail-grid">
    <div class="panel keep">
      <span class="rank">{h(hero["role"])}</span>
      <h2>{h(hero["ja"])}</h2>
      <p>{h(hero["desc"])}</p>
      <p class="loadout" style="margin-top:10px">{h(hero["gear"])}</p>
      <div class="skill-line">{skills}</div>
    </div>
    <div class="panel synth">
      <h2>残すもの</h2>
      <p>{h(hero["keep"])}</p>
      {affix_summary}
      <h3 style="margin-top:14px">売却候補</h3>
      <p>{h(hero["sell"])}</p>
    </div>
  </section>

  <h2 id="items">関連アイテム</h2>
  <section class="cards">{related_cards}</section>

  <h2 id="affixes">残す付与素材</h2>
  <p class="small">装飾・彫刻素材を、付ける部位ごとの効果で整理。武器、防具、アクセのどこに付けると目的の数値が伸びるかを確認。</p>
  <div class="scroll-table"><table><thead><tr><th>素材</th><th>種類</th><th>等級</th><th>残す理由</th><th>武器/サブ武器</th><th>防具/ブーツ</th><th>アクセ</th></tr></thead><tbody>{affix_rows}</tbody></table></div>

  <h2 id="specials">特殊装備</h2>
  <div class="scroll-table"><table><thead><tr><th>装備</th><th>レベル</th><th>必要等級</th><th>部位</th><th>効果</th></tr></thead><tbody>{special_rows}</tbody></table></div>

  <footer>データ: ゲーム内データ / 市場価格 / コミュニティガイド</footer>
</main>
</body>
</html>
"""
    return body


def write_character_pages(data: dict) -> None:
    target = ROOT / "characters"
    target.mkdir(exist_ok=True)
    for hero in data["heroes"]:
        (target / f'{hero["slug"]}.html').write_text(character_page_template(data, hero), encoding="utf-8", newline="\n")


def main() -> None:
    items, market = build_items()
    guide_effects, _effect_by_name, _unique_by_item = build_guide_effects()
    market_updated_at = max([m["priceUpdatedAt"] for m in market if m.get("priceUpdatedAt")], default="")
    data = {
        "items": items,
        "market": market,
        "heroes": build_heroes(),
        "guideEffects": guide_effects,
        "materialBands": MATERIAL_BANDS,
        "tierTable": TIER_TABLE,
        "buildTable": BUILD_TABLE,
        "socketTable": SOCKET_TABLE,
        "marketUpdatedAt": market_updated_at,
        "rarityColor": RARITY_COLOR,
        "gradeJa": GRADE_JA,
        "gradeOrder": GRADE_ORDER,
    }
    (ROOT / "index.html").write_text(html_template(data), encoding="utf-8", newline="\n")
    write_keep_materials_page(data)
    write_character_pages(data)


if __name__ == "__main__":
    main()
