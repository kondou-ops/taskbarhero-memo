import json
import re
from datetime import date
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

MATERIAL_TIER_BY_PREFIX = {
    **{110 + i: GRADE_ORDER[i] for i in range(10)},
    **{120 + i: GRADE_ORDER[i] for i in range(10)},
    **{130 + i: GRADE_ORDER[i] for i in range(10)},
    **{140 + i: GRADE_ORDER[i] for i in range(10)},
}

SOURCE_LINKS = [
    {
        "name": "Steam公式ストア",
        "url": "https://store.steampowered.com/app/3678970/TBH_Task_Bar_Hero/",
        "note": "500+ items、Cube System、Steam Market対応、レアリティ体系の確認",
    },
    {
        "name": "Steam Community Market",
        "url": "https://steamcommunity.com/market/search?appid=3678970",
        "note": "マーケット掲載品、出品数、参考価格の確認",
    },
    {
        "name": "Steamコミュニティガイド",
        "url": "https://steamcommunity.com/sharedfiles/filedetails/?id=3744134720",
        "note": "ダメージ計算、ソケット解放、装飾/彫刻/刻印のステータス傾向の補助確認",
    },
    {
        "name": "公式X",
        "url": "https://x.com/TesseractStd",
        "note": "Steam公式ページからリンクされている開発元X。ログインなしでは投稿本文を安定取得できないため、サイト本文はSteam/ローカルデータを主情報にした。",
    },
]

MATERIAL_BANDS = [
    {
        "range": "Lv 1-10",
        "tier": "Common / Uncommon",
        "crafting": [140001, 140002, 140003, 140004, 141001, 141002],
        "deco": [110001, 110002, 110003, 110004, 110005, 111001, 111002, 111003, 111004],
        "engraving": [120001, 120002, 120003, 121001, 121002, 121003, 121004],
        "inscription": [130001, 131001],
        "advice": "序盤クラフトと最初の付与用。木材/石/レザー系は多めに拾うが、倉庫を圧迫したら一定数だけ残す。",
    },
    {
        "range": "Lv 15-30",
        "tier": "Rare / Legendary",
        "crafting": [142001, 142002, 143001, 143002],
        "deco": [112001, 112002, 112003, 112004, 112005, 113001, 113002, 113003, 113004],
        "engraving": [122001, 122002, 122003, 122004, 123001, 123002, 123003, 123004],
        "inscription": [132001, 133001],
        "advice": "ビルドが固まり始める帯。物理/属性/速度に合う装飾素材は残し、合わない余剰だけ売却候補。",
    },
    {
        "range": "Lv 40-50",
        "tier": "Immortal / Arcana",
        "crafting": [144001, 144002, 145001, 145002],
        "deco": [114001, 114002, 114003, 114004, 115001, 115002, 115003, 115004],
        "engraving": [124001, 124002, 124003, 124004, 125001, 125002, 125003, 125004],
        "inscription": [134001, 135001],
        "advice": "合成・付与の失敗コストが重くなる帯。市場価格を見て、安い素材だけ実験に回す。",
    },
    {
        "range": "Lv 65",
        "tier": "Beyond / Celestial",
        "crafting": [146001, 146002, 147001, 147002],
        "deco": [116001, 116002, 116003, 116004, 117001, 117002],
        "engraving": [126001, 126002, 126003, 126004, 127001, 127002],
        "inscription": [136001, 137001],
        "advice": "高難度用の主力素材。Celestial合成はキューブLv50条件があるため、売る前にキューブ進行も確認。",
    },
    {
        "range": "Lv 80+",
        "tier": "Divine / Cosmic",
        "crafting": [148001, 148002, 149001, 149002],
        "deco": [118001, 118002, 119001, 119002],
        "engraving": [128001, 128002, 129001, 129002],
        "inscription": [138001, 139001],
        "advice": "最終帯。Cosmicは合成不可なので、素材・装備ともに売却前の確認を強める。",
    },
]

TIER_TABLE = [
    {
        "tier": "S",
        "label": "原則残す",
        "target": "Soulstone、Divine/Cosmic素材、刻印巻物、主力ビルドの高等級装備、市場価格が高い素材",
        "reason": "ボス挑戦、最終付与、上位クラフト、取引価値のどれかに直結する。",
    },
    {
        "tier": "A",
        "label": "必要数を残す",
        "target": "装飾/彫刻素材、Lv40以上のクラフト素材、同等級合成に使う装備",
        "reason": "欲しいステータスの素材は消費が早い。合成は同等級装備9個が基本。",
    },
    {
        "tier": "B",
        "label": "余剰だけ売却可",
        "target": "序盤クラフト素材、ビルド外の中級素材、マーケットで安い重複品",
        "reason": "序盤素材は必要数を超えやすい。価格が安いものは倉庫圧迫を避ける。",
    },
    {
        "tier": "C",
        "label": "売却/錬金候補",
        "target": "低等級の重複装備、ビルドに合わない付与なし装備、価格が低く在庫の多い素材",
        "reason": "使う予定がなければゴールド化や市場売却でよい。ただし装飾/彫刻/碑文済み装備は取引不可。",
    },
]

BUILD_TABLE = [
    {
        "name": "物理/攻速",
        "classes": "剣・弓・クロスボウ・斧・ハチェット・矢・ボルト",
        "keep": "Physical Damage%、Attack Speed%、Attack Damage%、Crit、Increase Projectile/Melee/Area",
        "sell": "魔法属性だけに寄った素材や、使わない武器種の低等級重複",
    },
    {
        "name": "属性/魔法",
        "classes": "スタッフ・セプター・オーブ・トーム",
        "keep": "Fire/Cold/Lightning/Chaos Damage%、Cast Speed、Cooldown、Increase Summon/Area",
        "sell": "物理専用ステータスだけの低等級素材。耐久不足時は防御素材を優先して残す。",
    },
    {
        "name": "耐久/放置安定",
        "classes": "盾・ヘルメット・アーマー・グローブ・ブーツ・アクセサリー",
        "keep": "Max HP、Resistance、Damage Reduction、Damage Absorption、Life Leech、HP per Hit",
        "sell": "火力が十分で、同じ耐久素材が過剰な場合だけ処分。",
    },
]

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
        image = f"images/{entry['name']}.png"
        unique[key] = {
            "name": entry["name"],
            "base": base,
            "id": base_id,
            "type": desc.get("type", ""),
            "grade": market_grade(entry, base_id),
            "price": entry.get("sell_price_text") or entry.get("sale_price_text") or "-",
            "priceValue": price_number(entry.get("sell_price_text") or entry.get("sale_price_text") or ""),
            "listings": entry.get("sell_listings", 0),
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


def related_band(iid: int) -> str:
    for band in MATERIAL_BANDS:
        all_ids = band["crafting"] + band["deco"] + band["engraving"] + band["inscription"]
        if iid in all_ids:
            return f'{band["range"]} / {band["tier"]}'
    if 300000 <= iid <= 639999:
        level = GEAR_LEVEL_BY_INDEX.get(iid % 1000)
        if level:
            if level <= 10:
                return "Lv 1-10"
            if level <= 30:
                return "Lv 15-30"
            if level <= 50:
                return "Lv 40-50"
            if level <= 65:
                return "Lv 65"
            return "Lv 80+"
    return ""


def uses_for(iid: int, category: str, gear_kind: str | None, grade: str | None) -> list[str]:
    prefix = iid // 1000
    if 110 <= prefix <= 119:
        return ["キューブの装飾で使用", "装飾スロット付き装備 x1 + 装飾素材 x1", "素材に応じたランダムステータスを付与"]
    if 120 <= prefix <= 129:
        return ["キューブの彫刻で使用", "彫刻スロット付き装備 x1 + 彫刻素材 x1", "装備種類に応じた候補からランダム付与"]
    if 130 <= prefix <= 139:
        return ["キューブの刻印で使用", "刻印スロット付き装備 x1 + 刻印素材 x1", "Increase系など強い最終火力ステータスの候補"]
    if 140 <= prefix <= 149:
        return ["キューブの製作で使用", "製作したい装備種類を選んで必要素材として投入", "同レベル帯の装備更新に備えて必要数を確保"]
    if prefix == 160:
        return ["キューブの祈願で使用", "記念コインを捧げてランダムアイテムを獲得", "イベント/記念品なので価格確認後に使う"]
    if prefix == 190:
        return ["Actボス召喚に必要", "失敗時は消費されず、勝利時に消費される仕様としてコミュニティ情報あり", "難易度進行用に優先して残す"]
    if gear_kind:
        level = GEAR_LEVEL_BY_INDEX.get(iid % 1000)
        return [
            f"{gear_kind}として装備",
            "同じ等級の装備9個でキューブ合成に使える",
            "装飾/彫刻/碑文が付いていなければSteam交易船の候補",
            f"目安装備Lv: {level if level else '-'}",
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
    if max_price >= 10:
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
        return f'市場掲載あり: {best["price"]} / 出品 {best["listings"]}。価格が動くので売却直前に確認。'
    if 300 <= prefix <= 639:
        return "ビルド外でも同等級9個合成に使える。低等級・重複・付与なしなら売却/錬金候補。"
    if "余剰" in action:
        return "必要数を決め、超えた分だけ売却/錬金候補。"
    return "用途がある素材。次の装備更新や付与予定がない余剰だけ処分。"


def build_items() -> tuple[list[dict], list[dict]]:
    rows = read_json("ItemTable.json")
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
        action = action_for(iid, category, grade, markets)
        tags = stat_tags(row["en"], category, class_name)
        if level:
            tags.insert(0, f"Lv {level}")

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
                "market": markets,
                "marketCount": len(markets),
            }
        )
    return items, market


def css() -> str:
    return r"""
:root{--bg:#f4f6f8;--paper:#fff;--ink:#19202a;--muted:#667085;--line:#d7dde5;--green:#247a4b;--blue:#2764b5;--amber:#9a6500;--red:#b43b3b;--teal:#0f766e;--chip:#eef2f7;--shadow:0 18px 50px rgba(16,24,40,.18)}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;font-family:Inter,"Noto Sans JP",Meiryo,system-ui,-apple-system,sans-serif;background:var(--bg);color:var(--ink);line-height:1.55}a{color:#245da8;text-decoration:none}a:hover{text-decoration:underline}
header{background:#18202c;color:#fff;padding:22px 20px 18px;border-bottom:4px solid #2d8a76}header .wrap,main{max-width:1220px;margin:0 auto}h1{margin:0 0 8px;font-size:28px;letter-spacing:0}h2{margin:34px 0 14px;font-size:20px}h3{margin:0 0 8px;font-size:16px}p{margin:0}.sub{color:#cbd5e1;font-size:14px;max-width:900px}
main{padding:22px 20px 46px}.section-note{color:var(--muted);font-size:13px;margin:-6px 0 12px}.grid4,.stat-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}.grid3{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}.panel{background:var(--paper);border:1px solid var(--line);border-radius:8px;padding:14px}.panel.keep{border-left:5px solid var(--green)}.panel.synth{border-left:5px solid var(--blue)}.panel.sell{border-left:5px solid var(--amber)}.panel.warn{border-left:5px solid var(--red)}.small{color:var(--muted);font-size:13px}ul{padding-left:18px;margin:8px 0 0}li{margin:3px 0}
.nav{display:flex;gap:8px;flex-wrap:wrap;margin-top:14px}.nav a{color:#fff;border:1px solid rgba(255,255,255,.28);padding:6px 10px;border-radius:999px;font-size:13px}
.toolbar{position:sticky;top:0;z-index:5;background:rgba(244,246,248,.97);border:1px solid var(--line);border-radius:8px;padding:10px;display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:18px 0}input[type=search]{flex:1 1 270px;border:1px solid var(--line);border-radius:6px;padding:10px 12px;font-size:14px;background:#fff}button{border:1px solid var(--line);background:#fff;color:var(--ink);border-radius:6px;padding:9px 11px;font-size:13px;cursor:pointer}button.active{background:#18202c;color:#fff;border-color:#18202c}.count{color:var(--muted);font-size:13px;margin-left:auto}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(238px,1fr));gap:10px}.card{background:#fff;border:1px solid var(--line);border-radius:8px;padding:10px;display:grid;grid-template-columns:52px 1fr;gap:10px;min-height:104px;text-align:left;width:100%}.card:hover,.card:focus{outline:2px solid #2d8a76;outline-offset:1px}.card img{width:52px;height:52px;object-fit:contain;image-rendering:pixelated;background:#eef2f7;border:1px solid #d5deea;border-radius:6px}.name{font-weight:700;font-size:14px;overflow-wrap:anywhere}.en{color:var(--muted);font-size:12px;overflow-wrap:anywhere}.chips{display:flex;flex-wrap:wrap;gap:4px;margin-top:6px}.chip{display:inline-flex;align-items:center;border-radius:999px;background:var(--chip);color:#3f4a5a;padding:2px 7px;font-size:11px;line-height:18px}.chip.keep{background:#e6f4ec;color:#17643c}.chip.synth{background:#e8f0ff;color:#1d55a6}.chip.sell{background:#fff3d7;color:#7a4c00}.chip.warn{background:#ffe8e8;color:#9d2b2b}.market{color:#7a4c00;background:#fff3d7}.rarity{width:10px;height:10px;border-radius:50%;display:inline-block;margin-right:5px;border:1px solid rgba(0,0,0,.2)}
table{width:100%;border-collapse:collapse;background:#fff;border:1px solid var(--line);border-radius:8px;overflow:hidden}th,td{padding:9px 10px;border-bottom:1px solid var(--line);text-align:left;font-size:13px;vertical-align:top}th{background:#eef2f7;color:#3f4a5a}td img{width:34px;height:34px;object-fit:contain;image-rendering:pixelated;vertical-align:middle;margin-right:8px}.table-wrap{overflow:auto;margin-top:10px}.mini-items{display:flex;flex-wrap:wrap;gap:5px}.mini-item{display:inline-flex;align-items:center;gap:4px;border:1px solid var(--line);border-radius:999px;padding:2px 7px;background:#fff;font-size:12px;white-space:nowrap}.mini-item img{width:22px;height:22px;margin:0;object-fit:contain;image-rendering:pixelated}
.modal{position:fixed;inset:0;display:none;align-items:center;justify-content:center;padding:18px;background:rgba(15,23,42,.56);z-index:20}.modal.open{display:flex}.dialog{width:min(760px,100%);max-height:90vh;overflow:auto;background:#fff;border-radius:8px;box-shadow:var(--shadow);border:1px solid var(--line)}.dialog-head{display:grid;grid-template-columns:72px 1fr auto;gap:12px;align-items:center;padding:16px;border-bottom:1px solid var(--line)}.dialog-head img{width:72px;height:72px;object-fit:contain;image-rendering:pixelated;background:#eef2f7;border:1px solid #d5deea;border-radius:8px}.dialog-body{padding:16px}.detail-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}.close{font-size:20px;line-height:1;width:36px;height:36px;padding:0}.source-list{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}footer{margin-top:28px;color:var(--muted);font-size:12px}
@media(max-width:900px){.grid4,.stat-grid,.grid3,.source-list{grid-template-columns:1fr 1fr}.detail-grid{grid-template-columns:1fr}}@media(max-width:640px){header{padding:18px 14px}main{padding:16px 12px 36px}.grid4,.stat-grid,.grid3,.source-list{grid-template-columns:1fr}.toolbar{position:static}.cards{grid-template-columns:1fr}.count{width:100%;margin-left:0}.dialog-head{grid-template-columns:56px 1fr auto}.dialog-head img{width:56px;height:56px}}
"""


def html_template(data: dict) -> str:
    data_json = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TBH: Task Bar Hero 素材・装備メモ</title>
<style>{css()}</style>
</head>
<body>
<header>
  <div class="wrap">
    <h1>TBH: Task Bar Hero 素材・装備メモ</h1>
    <p class="sub">更新: {date.today().isoformat()} / ゲーム内ローカライズ、抽出アイコン、Steam公式マーケット、公開コミュニティ情報から整理。素材を残すか、合成・付与・売却に使うかを画像付きで確認するためのメモです。</p>
    <nav class="nav">
      <a href="#rules">判断基準</a><a href="#tiers">ティア表</a><a href="#materials">素材/レベル帯</a><a href="#items">アイテム一覧</a><a href="#market">マーケット</a><a href="#sources">情報元</a>
    </nav>
  </div>
</header>
<main>
  <section id="rules" class="grid4">
    <div class="panel keep"><h3>残す</h3><p>ソウルストーン、刻印巻物、高等級素材、狙いステータスの装飾/彫刻素材。必要数を決めて超過分だけ処分。</p></div>
    <div class="panel synth"><h3>合成</h3><p>同じ等級の装備9個が基本。Immortal合成はキューブLv10、Celestial合成はキューブLv50、Cosmicは合成不可。</p></div>
    <div class="panel sell"><h3>売却/錬金</h3><p>低級素材の余剰、ビルド外の重複装備、市場価格が低い付与なし装備。売却前に価格と今後のクラフト予定を確認。</p></div>
    <div class="panel warn"><h3>注意</h3><p>装飾/彫刻/碑文済み装備は取引不可。キューブ除去は可能だが、使った素材は戻らない。</p></div>
  </section>

  <h2 id="tiers">クラフト/売却ティア表</h2>
  <p class="section-note">迷った時の保持優先度。価格は変動するので、S/A判定でも売る直前にマーケットを確認。</p>
  <section class="grid4" id="tierCards"></section>

  <h2>ビルド別に残すステータス</h2>
  <section class="grid3" id="buildCards"></section>

  <h2>ソケット解放目安</h2>
  <p class="section-note">公開コミュニティガイドとゲーム内文言を元にした目安。装飾/彫刻/刻印素材はスロットが空いている装備に使う。</p>
  <div class="table-wrap"><table id="socketTable"><thead><tr><th>等級</th><th>装飾</th><th>彫刻</th><th>刻印</th></tr></thead><tbody></tbody></table></div>

  <h2 id="materials">素材とレベル帯</h2>
  <p class="section-note">数量レシピではなく、保持判断用の整理表です。ローカルデータには「必要アイテムレベル: Lv.x以上」の文言はありますが、個別要求数は静的ファイルからは確定できませんでした。</p>
  <div class="table-wrap"><table id="materialTable"><thead><tr><th>帯</th><th>クラフト素材</th><th>装飾</th><th>彫刻</th><th>刻印</th><th>判断</th></tr></thead><tbody></tbody></table></div>

  <h2 id="items">素材・装備一覧</h2>
  <div class="toolbar">
    <input id="q" type="search" placeholder="日本語名・英語名・用途・ステータスで検索">
    <button class="filter active" data-filter="all">すべて</button>
    <button class="filter" data-filter="material">素材</button>
    <button class="filter" data-filter="crafting">クラフト</button>
    <button class="filter" data-filter="decoration">装飾</button>
    <button class="filter" data-filter="engraving">彫刻</button>
    <button class="filter" data-filter="inscription">刻印</button>
    <button class="filter" data-filter="gear weapon">武器</button>
    <button class="filter" data-filter="armor">防具</button>
    <button class="filter" data-filter="accessory">アクセ</button>
    <button class="filter" data-filter="marketed">市場あり</button>
    <button class="filter" data-filter="physical">物理/速度</button>
    <button class="filter" data-filter="magic">魔法</button>
    <span class="count" id="count"></span>
  </div>
  <section class="cards" id="cards"></section>

  <h2 id="market">Steamマーケット掲載アイテム</h2>
  <p class="section-note">取得時点の参考価格。公開ページでは自動更新しないため、売却直前はSteamマーケット側を確認。</p>
  <div class="table-wrap"><table id="marketTable"><thead><tr><th>アイテム</th><th>分類</th><th>等級</th><th>最安値</th><th>出品数</th></tr></thead><tbody></tbody></table></div>

  <h2 id="sources">情報元</h2>
  <section class="source-list" id="sourceList"></section>

  <footer>ローカルデータ: ItemTable/StringTable/sharedassets0。Xserverは使用していません。</footer>
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
const DATA={data_json};
const ITEMS=DATA.items, MARKET=DATA.market, MATERIAL_BANDS=DATA.materialBands, TIER_TABLE=DATA.tierTable, BUILD_TABLE=DATA.buildTable, SOCKET_TABLE=DATA.socketTable, SOURCES=DATA.sources;
const rarityColor=DATA.rarityColor, gradeJa=DATA.gradeJa;
let activeFilter='all';
const cards=document.getElementById('cards'),count=document.getElementById('count'),q=document.getElementById('q');
const modal=document.getElementById('modal'), modalClose=document.getElementById('modalClose');
function esc(s){{return String(s??'').replace(/[&<>"]/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}}[c]));}}
function actionClass(a){{if(a.includes('必ず')||a.includes('残'))return 'keep';if(a.includes('合成')||a.includes('ビルド'))return 'synth';if(a.includes('価格')||a.includes('祈願'))return 'warn';return 'sell';}}
function gradeChip(g){{return g?`<span class="chip"><span class="rarity" style="background:${{rarityColor[g]||'#ddd'}}"></span>${{esc(gradeJa[g]||g)}}</span>`:'';}}
function passFilter(it){{if(activeFilter==='all')return true;if(activeFilter==='marketed')return it.marketCount>0;if(activeFilter==='physical')return it.tags.includes('物理/攻撃速度');if(activeFilter==='magic')return it.tags.includes('魔法/属性');return it.class.includes(activeFilter);}}
function searchable(it){{return [it.ja,it.en,it.category,it.action,it.grade,gradeJa[it.grade],it.sellAdvice,it.tierBand,it.desc,...it.tags,...it.uses].join(' ').toLowerCase();}}
function renderMiniItems(ids){{return `<div class="mini-items">${{ids.map(id=>{{const it=ITEMS.find(x=>x.id===id);return it?`<span class="mini-item" title="${{esc(it.en)}}"><img src="${{esc(it.icon)}}" alt="">${{esc(it.ja)}}</span>`:'';}}).join('')}}</div>`;}}
function renderTierCards(){{document.getElementById('tierCards').innerHTML=TIER_TABLE.map(t=>`<div class="panel ${{t.tier==='S'?'keep':t.tier==='A'?'synth':t.tier==='B'?'sell':'warn'}}"><h3>${{esc(t.tier)}}: ${{esc(t.label)}}</h3><p>${{esc(t.target)}}</p><p class="small" style="margin-top:8px">${{esc(t.reason)}}</p></div>`).join('');}}
function renderBuildCards(){{document.getElementById('buildCards').innerHTML=BUILD_TABLE.map(b=>`<div class="panel"><h3>${{esc(b.name)}}</h3><p class="small">${{esc(b.classes)}}</p><ul><li>残す: ${{esc(b.keep)}}</li><li>売却候補: ${{esc(b.sell)}}</li></ul></div>`).join('');}}
function renderSocketTable(){{document.querySelector('#socketTable tbody').innerHTML=SOCKET_TABLE.map(r=>`<tr><td>${{gradeChip(r.grade)}}</td><td>${{r.deco}}</td><td>${{r.engraving||'-'}}</td><td>${{r.inscription||'-'}}</td></tr>`).join('');}}
function renderMaterialTable(){{document.querySelector('#materialTable tbody').innerHTML=MATERIAL_BANDS.map(b=>`<tr><td><strong>${{esc(b.range)}}</strong><div class="small">${{esc(b.tier)}}</div></td><td>${{renderMiniItems(b.crafting)}}</td><td>${{renderMiniItems(b.deco)}}</td><td>${{renderMiniItems(b.engraving)}}</td><td>${{renderMiniItems(b.inscription)}}</td><td>${{esc(b.advice)}}</td></tr>`).join('');}}
function renderCards(){{const term=q.value.trim().toLowerCase();const list=ITEMS.filter(it=>passFilter(it)).filter(it=>!term||searchable(it).includes(term));cards.innerHTML=list.map(it=>{{const market=it.market.slice(0,2).map(m=>`<span class="chip market"><span class="rarity" style="background:#${{esc(m.color||'ddd')}}"></span>${{esc(m.price)}}</span>`).join('');return `<button class="card" data-id="${{it.id}}"><img src="${{esc(it.icon)}}" alt="${{esc(it.ja)}}" loading="lazy"><span><span class="name">${{esc(it.ja)}}</span><span class="en">${{esc(it.en)}} / ID ${{it.id}}</span><span class="chips"><span class="chip ${{actionClass(it.action)}}">${{esc(it.action)}}</span><span class="chip">${{esc(it.category)}}</span>${{gradeChip(it.grade)}}${{it.tags.slice(0,4).map(t=>`<span class="chip">${{esc(t)}}</span>`).join('')}}${{market}}</span><span class="small" style="display:block;margin-top:6px">${{esc(it.uses[0]||it.sellAdvice)}}</span></span></button>`;}}).join('');count.textContent=`${{list.length}} / ${{ITEMS.length}}件`;}}
function renderMarket(){{document.querySelector('#marketTable tbody').innerHTML=MARKET.map(m=>`<tr><td>${{m.image?`<img src="${{esc(m.image)}}" alt="">`:''}}${{esc(m.name)}}<div class="en">${{esc(m.base)}}</div></td><td>${{esc(m.type)}}</td><td>${{gradeChip(m.grade)||'-'}}</td><td>${{esc(m.price)}}</td><td>${{esc(m.listings)}}</td></tr>`).join('');}}
function renderSources(){{document.getElementById('sourceList').innerHTML=SOURCES.map(s=>`<div class="panel"><h3><a href="${{esc(s.url)}}" target="_blank" rel="noreferrer">${{esc(s.name)}}</a></h3><p class="small">${{esc(s.note)}}</p></div>`).join('');}}
function openDetail(id){{const it=ITEMS.find(x=>x.id===Number(id));if(!it)return;document.getElementById('modalIcon').src=it.icon;document.getElementById('modalIcon').alt=it.ja;document.getElementById('modalTitle').textContent=it.ja;document.getElementById('modalSub').textContent=`${{it.en}} / ID ${{it.id}} / ${{it.category}}${{it.level?' / Lv '+it.level:''}}`;document.getElementById('modalChips').innerHTML=`<span class="chip ${{actionClass(it.action)}}">${{esc(it.action)}}</span>${{gradeChip(it.grade)}}${{it.tags.map(t=>`<span class="chip">${{esc(t)}}</span>`).join('')}}`;const marketHtml=it.market.length?`<div class="table-wrap"><table><thead><tr><th>市場名</th><th>価格</th><th>出品</th></tr></thead><tbody>${{it.market.map(m=>`<tr><td>${{esc(m.name)}}</td><td>${{esc(m.price)}}</td><td>${{esc(m.listings)}}</td></tr>`).join('')}}</tbody></table></div>`:'<p class="small">現在の取得データではマーケット掲載なし。</p>';document.getElementById('modalBody').innerHTML=`<div class="detail-grid"><div class="panel"><h3>用途</h3><ul>${{it.uses.map(u=>`<li>${{esc(u)}}</li>`).join('')}}</ul></div><div class="panel"><h3>売却判断</h3><p>${{esc(it.sellAdvice)}}</p><p class="small" style="margin-top:8px">関連帯: ${{esc(it.tierBand||'-')}}</p></div></div>${{it.desc?`<div class="panel" style="margin-top:12px"><h3>ゲーム内説明</h3><p>${{esc(it.desc)}}</p></div>`:''}}<div class="panel" style="margin-top:12px"><h3>マーケット</h3>${{marketHtml}}</div>`;modal.classList.add('open');modal.setAttribute('aria-hidden','false');modalClose.focus();}}
cards.addEventListener('click',e=>{{const btn=e.target.closest('.card');if(btn)openDetail(btn.dataset.id);}});
document.querySelectorAll('.filter').forEach(btn=>btn.addEventListener('click',()=>{{document.querySelectorAll('.filter').forEach(b=>b.classList.remove('active'));btn.classList.add('active');activeFilter=btn.dataset.filter;renderCards();}}));
q.addEventListener('input',renderCards);modalClose.addEventListener('click',()=>{{modal.classList.remove('open');modal.setAttribute('aria-hidden','true');}});modal.addEventListener('click',e=>{{if(e.target===modal)modalClose.click();}});window.addEventListener('keydown',e=>{{if(e.key==='Escape'&&modal.classList.contains('open'))modalClose.click();}});
renderTierCards();renderBuildCards();renderSocketTable();renderMaterialTable();renderCards();renderMarket();renderSources();
</script>
</body>
</html>
"""


def main() -> None:
    items, market = build_items()
    data = {
        "items": items,
        "market": market,
        "materialBands": MATERIAL_BANDS,
        "tierTable": TIER_TABLE,
        "buildTable": BUILD_TABLE,
        "socketTable": SOCKET_TABLE,
        "sources": SOURCE_LINKS,
        "rarityColor": RARITY_COLOR,
        "gradeJa": GRADE_JA,
    }
    (ROOT / "index.html").write_text(html_template(data), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
