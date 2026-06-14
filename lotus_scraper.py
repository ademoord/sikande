"""Scrape Lotus Archi gold buyback price from lotusarchi.com/pricing."""
import re
from html import unescape
from urllib.error import URLError
from urllib.request import Request, urlopen

LOTUS_PRICING_URL = 'https://lotusarchi.com/pricing'
USER_AGENT = 'Mozilla/5.0 (compatible; Sikande/1.0)'


def _parse_idr_amount(raw):
    digits = re.sub(r'[^\d]', '', raw or '')
    if not digits:
        return None
    return float(digits)


def _extract_gold_h4(html):
    """Return h4 text from the HARGA EMAS section when present."""
    section = re.search(
        r'class="section[^"]*text-harga-emas[^"]*"[^>]*>(.*?)</section>',
        html,
        re.I | re.S,
    )
    if section:
        h4 = re.search(r'<h4[^>]*>(.*?)</h4>', section.group(1), re.I | re.S)
        if h4:
            return unescape(re.sub(r'\s+', ' ', h4.group(1))).strip()
    h4 = re.search(
        r'<h4[^>]*>[^<]*Buyback Price[^<]*</h4>',
        html,
        re.I | re.S,
    )
    if h4:
        inner = re.search(r'<h4[^>]*>(.*?)</h4>', h4.group(0), re.I | re.S)
        if inner:
            return unescape(re.sub(r'\s+', ' ', inner.group(1))).strip()
    return None


def fetch_lotus_buyback_price():
    """Return (buyback_price_per_gram_idr, info_dict). Raises on failure."""
    req = Request(
        LOTUS_PRICING_URL,
        headers={'User-Agent': USER_AGENT, 'Accept': 'text/html'},
    )
    with urlopen(req, timeout=12) as resp:
        html = resp.read().decode('utf-8', errors='replace')

    h4_text = _extract_gold_h4(html)
    search_text = h4_text or html

    buyback = re.search(r'Buyback Price\s*:\s*Rp\s*([\d.]+)', search_text, re.I)
    if not buyback:
        raise ValueError('Lotus buyback price not found on pricing page')

    price = _parse_idr_amount(buyback.group(1))
    if not price or price <= 0:
        raise ValueError('Lotus buyback price is invalid')

    recorded = None
    if h4_text:
        date_match = re.match(r'^([^|]+?)\s*\|\|', h4_text)
        if date_match:
            recorded = date_match.group(1).strip()

    return price, {
        'date': recorded,
        'source': 'lotusarchi.com',
        'display_name': 'Lotus Archi',
        'price_type': 'buyback',
        'cached': False,
    }
