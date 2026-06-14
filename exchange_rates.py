"""Live IDR exchange rates with in-memory cache (no API key required)."""
import json
import time
from urllib.error import URLError
from urllib.request import Request, urlopen

CACHE_TTL = 600  # 10 minutes

_cache = {}


def _fetch_open_er_api(currency_code):
    url = 'https://open.er-api.com/v6/latest/{}'.format(currency_code)
    req = Request(url, headers={'User-Agent': 'Sikande/1.0'})
    with urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode())
    if data.get('result') != 'success':
        raise ValueError(data.get('error-type', 'api error'))
    return float(data['rates']['IDR']), data.get('time_last_update_utc')


def _fetch_frankfurter(currency_code):
    url = 'https://api.frankfurter.app/latest?from={}&to=IDR'.format(currency_code)
    req = Request(url, headers={'User-Agent': 'Sikande/1.0'})
    with urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode())
    return float(data['rates']['IDR']), data.get('date')


def get_idr_rate(currency_code):
    """Return (rate, meta). rate is IDR per 1 unit of currency_code."""
    code = (currency_code or '').strip().upper()
    if not code:
        return None, {'error': 'empty'}
    if code == 'IDR':
        return 1.0, {'source': 'fixed', 'date': None, 'fetched_at': time.time(), 'currency': code}

    now = time.time()
    cached = _cache.get(code)
    if cached and (now - cached['fetched_at']) < CACHE_TTL:
        return cached['rate'], cached

    rate = None
    date = None
    source = None
    last_error = None

    for fetcher, src in ((_fetch_open_er_api, 'open.er-api.com'), (_fetch_frankfurter, 'frankfurter')):
        try:
            rate, date = fetcher(code)
            source = src
            break
        except (URLError, ValueError, KeyError, TypeError) as exc:
            last_error = str(exc)
            continue

    if rate is not None:
        meta = {
            'rate': rate,
            'fetched_at': now,
            'date': date,
            'source': source,
            'currency': code,
        }
        _cache[code] = meta
        return rate, meta

    if cached:
        stale = dict(cached)
        stale['stale'] = True
        return cached['rate'], stale

    return None, {'error': last_error or 'unavailable', 'currency': code}


def resolve_currency_price(currency_code, fallback=None):
    """IDR per unit for holdings; falls back to stored price when API is down."""
    rate, meta = get_idr_rate(currency_code)
    if rate is not None:
        return rate, meta
    fb = float(fallback or 0)
    return fb, {'error': True, 'fallback': True, 'currency': (currency_code or '').upper()}
