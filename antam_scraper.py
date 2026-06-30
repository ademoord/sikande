"""Scrape Antam buyback price per gram from muamalahemas.com (HF Gold)."""
import re
from html import unescape
from urllib.request import Request, urlopen

ANTAM_HOME_URL = 'https://muamalahemas.com/'
USER_AGENT = 'Mozilla/5.0 (compatible; Sikande/1.0)'


def _parse_idr_amount(raw):
    digits = re.sub(r'[^\d]', '', raw or '')
    if not digits:
        return None
    return float(digits)


def _extract_buyback_h3(html):
    """Return (price_match, h3_text) for the buyback per gram headline."""
    shortcode = re.search(
        r'class="elementor-shortcode"[^>]*>.*?<h3[^>]*>(.*?)</h3>',
        html,
        re.I | re.S,
    )
    candidates = []
    if shortcode:
        candidates.append(unescape(re.sub(r'\s+', ' ', shortcode.group(1))).strip())

    for h3 in re.finditer(r'<h3[^>]*>(.*?)</h3>', html, re.I | re.S):
        text = unescape(re.sub(r'\s+', ' ', h3.group(1))).strip()
        if text not in candidates:
            candidates.append(text)

    for text in candidates:
        match = re.search(r'Rp\.?\s*([\d.,]+)\s*/\s*gram', text, re.I)
        if match:
            return match, text
    return None, None


def _extract_updated_at(html):
    match = re.search(
        r'Terakhir Diperbarui\s+([^<]+)',
        html,
        re.I,
    )
    if match:
        return unescape(match.group(1)).strip()
    return None


def fetch_antam_buyback_price():
    """Return (buyback_price_per_gram_idr, info_dict). Raises on failure."""
    req = Request(
        ANTAM_HOME_URL,
        headers={'User-Agent': USER_AGENT, 'Accept': 'text/html'},
    )
    with urlopen(req, timeout=12) as resp:
        html = resp.read().decode('utf-8', errors='replace')

    buyback, h3_text = _extract_buyback_h3(html)
    if not buyback:
        raise ValueError('Antam buyback price not found on muamalahemas.com')

    price = _parse_idr_amount(buyback.group(1))
    if not price or price <= 0:
        raise ValueError('Antam buyback price is invalid')

    return price, {
        'date': _extract_updated_at(html),
        'source': 'muamalahemas.com',
        'display_name': 'HF Gold (Muamalah Emas)',
        'price_type': 'buyback',
        'cached': False,
        'headline': h3_text,
    }
