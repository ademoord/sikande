"""Live gold bar prices from Logam Mulia API (per brand, IDR per gram)."""
import json
import time
from urllib.error import URLError
from urllib.request import Request, urlopen

from lotus_scraper import fetch_lotus_buyback_price

# Sikande brand -> Logam Mulia API source slug (Lotus uses lotus_scraper.py)
GOLD_BRAND_SOURCES = {
    'HRTA': 'emasku',
    'Antam': 'logammulia',
    'BullionKey': 'sampoernagold',
}

# Prefer standard bullion rows when a source lists multiple product lines.
PREFERRED_GOLD_TYPES = ('Emas Batangan',)

CACHE_TTL = 600  # 10 minutes

_cache = {}


def _get_base_url():
    try:
        from config import app
        return (app.config.get('GOLD_API_BASE_URL') or 'https://logam-mulia-api.iamutaki.workers.dev').rstrip('/')
    except Exception:
        import os
        return os.environ.get('GOLD_API_BASE_URL', 'https://logam-mulia-api.iamutaki.workers.dev').rstrip('/')


def _effective_price(row):
    """Prefer buyback (what you'd receive) when set; else retail sell price."""
    buyback = float(row.get('buybackPrice') or 0)
    if buyback > 0:
        return buyback, 'buyback'
    sell = float(row.get('sellPrice') or 0)
    return sell, 'sell'


def _pick_gold_row(rows, weight):
    """Pick the best row for a target weight, preferring standard bullion types."""
    candidates = [r for r in rows if float(r.get('weight') or 0) == weight]
    if not candidates:
        return None
    for material_type in PREFERRED_GOLD_TYPES:
        match = [r for r in candidates if (r.get('materialType') or '') == material_type]
        if match:
            return match[0]
    return candidates[0]


def _price_per_gram(items):
    """Derive price per gram from API rows (buyback when available)."""
    gold_rows = [
        row for row in items
        if (row.get('material') or '').lower() == 'gold'
        and (row.get('weightUnit') or '').lower().startswith('gr')
        and (row.get('sellPrice') is not None or float(row.get('buybackPrice') or 0) > 0)
    ]
    if not gold_rows:
        return None, None, None

    row = _pick_gold_row(gold_rows, 1)
    if row:
        price, price_type = _effective_price(row)
        return price, row.get('recordedDate'), price_type

    # Fallback: smallest-weight standard row, then smallest overall.
    standard = [
        r for r in gold_rows
        if (r.get('materialType') or '') in PREFERRED_GOLD_TYPES
    ] or gold_rows
    row = min(standard, key=lambda r: float(r.get('weight') or 999))
    weight = float(row.get('weight') or 0)
    if weight <= 0:
        return None, None, None
    total, price_type = _effective_price(row)
    return total / weight, row.get('recordedDate'), price_type


def _fetch_brand_prices(brand):
    if brand == 'Lotus':
        price, info = fetch_lotus_buyback_price()
        return price, info

    source = GOLD_BRAND_SOURCES.get(brand)
    if not source:
        return None, {'error': 'unsupported brand', 'brand': brand}

    url = '{}/api/prices/{}'.format(_get_base_url(), source)
    req = Request(url, headers={'User-Agent': 'Sikande/1.0', 'Accept': 'application/json'})
    with urlopen(req, timeout=12) as resp:
        payload = json.loads(resp.read().decode())

    if not payload.get('success'):
        raise ValueError(payload.get('error') or 'api error')

    price, recorded, price_type = _price_per_gram(payload.get('data') or [])
    if price is None:
        raise ValueError('no gold price rows')

    return price, {
        'date': recorded or payload.get('timestamp'),
        'source': source,
        'cached': payload.get('cached'),
        'display_name': payload.get('source') or source,
        'price_type': price_type,
    }


def get_gold_price(brand):
    """Return (price_per_gram_idr, meta) for a supported gold brand."""
    brand = (brand or '').strip()
    if not brand or brand == 'Other':
        return None, {'error': 'unsupported', 'brand': brand}

    now = time.time()
    cached = _cache.get(brand)
    if cached and (now - cached['fetched_at']) < CACHE_TTL:
        return cached['rate'], cached

    try:
        price, info = _fetch_brand_prices(brand)
        meta = {
            'rate': price,
            'fetched_at': now,
            'date': info.get('date'),
            'source': info.get('source'),
            'brand': brand,
            'unit': 'gr',
            'cached': info.get('cached'),
            'price_type': info.get('price_type'),
        }
        _cache[brand] = meta
        return price, meta
    except (URLError, ValueError, KeyError, TypeError) as exc:
        if cached:
            stale = dict(cached)
            stale['stale'] = True
            return cached['rate'], stale
        return None, {'error': str(exc), 'brand': brand}


def resolve_gold_price(brand, fallback=None):
    """IDR per gram for holdings; falls back to stored price when API is down."""
    price, meta = get_gold_price(brand)
    if price is not None:
        return price, meta
    fb = float(fallback or 0)
    return fb, {'error': True, 'fallback': True, 'brand': brand}
