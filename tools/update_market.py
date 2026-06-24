import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
APPID = 3678970
SEARCH_URL = "https://steamcommunity.com/market/search/render/"
PRICE_URL = "https://steamcommunity.com/market/priceoverview/"
IMAGE_URL = "https://community.steamstatic.com/economy/image/"
USER_AGENT = "Mozilla/5.0 (compatible; taskbarhero-memo-price-updater/1.0)"
HIGHEST_NOTE = "Steamの公開APIでは現在の最高売注文を安定取得できないため未取得"


def fetch_bytes(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json,*/*"})
    with urlopen(request, timeout=30) as response:
        return response.read()


def fetch_json(url: str) -> dict:
    return json.loads(fetch_bytes(url).decode("utf-8-sig"))


def steam_get_json(base_url: str, params: dict) -> dict:
    return fetch_json(f"{base_url}?{urlencode(params)}")


def safe_filename(name: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*]', "_", name).strip()
    return cleaned or "market-item"


def image_path_for(entry: dict) -> str:
    name = entry["name"]
    image_dir = ROOT / "images"
    image_dir.mkdir(exist_ok=True)

    exact = image_dir / f"{name}.png"
    if exact.exists():
        return f"images/{exact.name}"

    local = image_dir / f"{safe_filename(name)}.png"
    if local.exists():
        return f"images/{local.name}"

    icon_url = entry.get("asset_description", {}).get("icon_url", "")
    if not icon_url:
        return ""

    try:
        local.write_bytes(fetch_bytes(f"{IMAGE_URL}{icon_url}"))
        return f"images/{local.name}"
    except (OSError, URLError):
        return ""


def fetch_market_items() -> list[dict]:
    all_results: list[dict] = []
    seen: set[str] = set()
    start = 0
    count = 100
    total = None

    while True:
        page = steam_get_json(
            SEARCH_URL,
            {
                "appid": APPID,
                "norender": 1,
                "count": count,
                "start": start,
                "cc": "JP",
                "l": "japanese",
            },
        )
        if not page.get("success"):
            raise RuntimeError(f"Steam market search failed: {page}")

        total = int(page.get("total_count") or 0)
        results = page.get("results") or []
        if not results:
            break

        for result in results:
            name = result.get("name") or result.get("hash_name")
            if not name or name in seen:
                continue
            seen.add(name)
            all_results.append(result)

        start += len(results)
        if start >= total:
            break
        time.sleep(0.4)

    return all_results


def fetch_price_overview(hash_name: str, attempts: int = 2) -> dict:
    for attempt in range(attempts):
        try:
            data = steam_get_json(
                PRICE_URL,
                {
                    "appid": APPID,
                    "currency": 8,
                    "cc": "JP",
                    "l": "japanese",
                    "market_hash_name": hash_name,
                },
            )
        except (OSError, URLError, json.JSONDecodeError):
            data = {}
        if data.get("success"):
            return data
        time.sleep(0.8 + attempt * 1.0)
    return {}


def enrich(entry: dict, fetched_at: str) -> dict:
    desc = entry.get("asset_description", {})
    hash_name = desc.get("market_hash_name") or entry.get("hash_name") or entry.get("name")
    overview = fetch_price_overview(hash_name)

    enriched = dict(entry)
    enriched["hash_name"] = hash_name
    search_price = entry.get("sell_price_text") or entry.get("sale_price_text") or "-"
    if not str(search_price).startswith("¥"):
        search_price = "-"
    enriched["lowest_price_text_jpy"] = overview.get("lowest_price") or search_price
    enriched["median_price_text_jpy"] = overview.get("median_price") or "-"
    enriched["volume"] = overview.get("volume") or "-"
    enriched["price_currency"] = "JPY"
    enriched["price_fetched_at"] = fetched_at
    enriched["highest_price_text_jpy"] = None
    enriched["highest_note"] = HIGHEST_NOTE
    enriched["image_path"] = image_path_for(enriched)
    return enriched


def apply_overview(entry: dict, overview: dict) -> None:
    if not overview.get("success"):
        return
    if overview.get("lowest_price"):
        entry["lowest_price_text_jpy"] = overview["lowest_price"]
    if overview.get("median_price"):
        entry["median_price_text_jpy"] = overview["median_price"]
    if overview.get("volume"):
        entry["volume"] = overview["volume"]


def repair_missing_prices(entries: list[dict]) -> None:
    for _round in range(2):
        missing = [entry for entry in entries if entry.get("lowest_price_text_jpy") == "-"]
        if not missing:
            return
        time.sleep(12)
        for entry in missing:
            apply_overview(entry, fetch_price_overview(entry["hash_name"], attempts=1))
            time.sleep(1.5)


def main() -> None:
    fetched_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    items = fetch_market_items()
    enriched = []

    for index, entry in enumerate(items, start=1):
        enriched.append(enrich(entry, fetched_at))
        if index < len(items):
            time.sleep(1.0)

    repair_missing_prices(enriched)

    output = ROOT / "market-items.json"
    output.write_text(json.dumps(enriched, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    print(f"updated {len(enriched)} market items at {fetched_at}")


if __name__ == "__main__":
    main()
