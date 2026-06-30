"""Normalize item names and resolve canonical group labels for archive reporting."""
import re
import unicodedata

# Regex rules applied after basic normalization; first match wins.
PATTERN_RULES = [
    (re.compile(r'^kontrakan\b', re.I), 'Kontrakan'),
    (re.compile(r'^sedekah\b', re.I), 'Sedekah'),
    (re.compile(r'^infaq\b', re.I), 'Infaq'),
    (re.compile(r'^bensin\b', re.I), 'Bensin'),
    (re.compile(r'^token\b', re.I), 'Token'),
    (re.compile(r'^goride\b', re.I), 'Goride'),
    (re.compile(r'^gocar\b', re.I), 'Gocar'),
    (re.compile(r'^grabbike\b', re.I), 'Grabbike'),
    (re.compile(r'^indrive\b', re.I), 'Indrive'),
    (re.compile(r'^topup\b', re.I), 'Topup'),
    (re.compile(r'^naskun\b', re.I), 'Naskun'),
    (re.compile(r'^nasgor\b', re.I), 'Nasi Goreng'),
    (re.compile(r'^nasi goreng\b', re.I), 'Nasi Goreng'),
    (re.compile(r'^rencang\b', re.I), 'Rencang'),
    (re.compile(r'^padang\b', re.I), 'Padang'),
    (re.compile(r'^buah\b', re.I), 'Buah'),
    (re.compile(r'^kopi\b', re.I), 'Kopi'),
    (re.compile(r'^indomaret\b', re.I), 'Indomaret'),
]


def normalize_name(name):
    """Lowercase, trim, collapse whitespace, strip trailing punctuation."""
    if not name:
        return ''
    text = unicodedata.normalize('NFKC', str(name))
    text = text.strip().lower()
    text = text.replace("'", '').replace('"', '')
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[.,;:!?]+$', '', text)
    return text


def apply_pattern_rules(normalized_name):
    """Return a canonical label from pattern rules, or None."""
    if not normalized_name:
        return None
    for pattern, label in PATTERN_RULES:
        if pattern.search(normalized_name):
            return label
    return None


def resolve_canonical_name(raw_name, alias_map=None):
    """
    Resolve display/canonical name: explicit alias > pattern rule > title-cased raw name.
    alias_map: dict normalized_raw -> canonical
    """
    alias_map = alias_map or {}
    normalized = normalize_name(raw_name)
    if normalized in alias_map:
        return alias_map[normalized]
    ruled = apply_pattern_rules(normalized)
    if ruled:
        return ruled
    if not raw_name:
        return 'Unknown'
    return str(raw_name).strip()


def keyword_category_hint(name):
    """Optional category backfill for legacy rows without category."""
    normalized = normalize_name(name)
    if not normalized:
        return None
    if re.search(r'\b(sedekah|infaq|zakat|fidyah|kurban|qurban)\b', normalized):
        return 'charity'
    if re.search(r'\b(goride|gocar|grabbike|indrive|topup|token)\b', normalized):
        return 'urgent'
    if re.search(r'\b(jajan|kopi|tomoro|mako|es\b|matcha)\b', normalized):
        return 'fun'
    if re.search(r'\b(emas|tabungan|saving|rak pira|polytron)\b', normalized):
        return 'saving'
    if re.search(r'\b(cicilan|hutang|kontrakan)\b', normalized):
        return 'liabilities' if 'cicilan' in normalized or 'hutang' in normalized else 'needs'
    return None
