"""Parse mysqldump item rows and ingest into the archive SQLite database."""
import hashlib
import os
import re
from datetime import datetime

from archive_normalize import keyword_category_hint, normalize_name, resolve_canonical_name
from archive_paths import list_sql_dumps
from archive_models import ArchiveItem, IngestRun, ItemAlias
from config import app, db

ITEM_INSERT_RE = re.compile(
    r"INSERT\s+INTO\s+`item`\s+VALUES\s+(.*?);",
    re.IGNORECASE | re.DOTALL,
)


def make_fingerprint(name, price, timestamp):
    normalized = normalize_name(name)
    if isinstance(timestamp, datetime):
        ts_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
    else:
        ts_str = str(timestamp)
    payload = '{}|{}|{}'.format(normalized, int(price), ts_str)
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


def _parse_string(blob, i):
    if i >= len(blob) or blob[i] != "'":
        raise ValueError('expected string at {}'.format(i))
    i += 1
    chars = []
    while i < len(blob):
        ch = blob[i]
        if ch == '\\':
            i += 1
            if i < len(blob):
                chars.append(blob[i])
                i += 1
            continue
        if ch == "'":
            return ''.join(chars), i + 1
        chars.append(ch)
        i += 1
    raise ValueError('unterminated string')


def _parse_tuple(blob, i):
    fields = []
    while i < len(blob):
        ch = blob[i]
        if ch == ')':
            return fields, i + 1
        if ch in ', \n\r\t':
            i += 1
            continue
        if ch == "'":
            value, i = _parse_string(blob, i)
            fields.append(value)
            continue
        if blob[i:i + 4].upper() == 'NULL':
            fields.append(None)
            i += 4
            continue
        j = i
        while j < len(blob) and blob[j] not in ',)':
            j += 1
        token = blob[i:j].strip()
        fields.append(int(token) if token.lstrip('-').isdigit() else token)
        i = j
    raise ValueError('unclosed tuple at {}'.format(i))


def _parse_values_blob(blob):
    rows = []
    i = 0
    n = len(blob)
    while i < n:
        if blob[i] == '(':
            row, i = _parse_tuple(blob, i + 1)
            rows.append(row)
        else:
            i += 1
    return rows


def parse_item_rows_from_sql(sql_text):
    """Return list of dicts from all INSERT INTO `item` statements in a dump."""
    parsed = []
    for match in ITEM_INSERT_RE.finditer(sql_text):
        for row in _parse_values_blob(match.group(1)):
            if len(row) == 4:
                orig_id, name, price, ts_raw = row
                category = None
            elif len(row) == 5:
                orig_id, name, price, ts_raw, category = row
            else:
                continue
            if name is None or price is None or ts_raw is None:
                continue
            if isinstance(ts_raw, datetime):
                ts = ts_raw
            else:
                ts = datetime.strptime(str(ts_raw), '%Y-%m-%d %H:%M:%S')
            parsed.append({
                'orig_item_id': int(orig_id) if orig_id is not None else None,
                'itemName': str(name).strip()[:64],
                'itemPrice': int(price),
                'itemTimestamp': ts,
                'category': (str(category).strip() if category else None),
            })
    return parsed


def _load_alias_map():
    alias_map = {}
    for alias in ItemAlias.query.all():
        alias_map[alias.normalized_raw] = alias.canonical_name
    return alias_map


def _row_to_archive_item(row, source_file, alias_map):
    category = row['category'] or keyword_category_hint(row['itemName'])
    normalized = normalize_name(row['itemName'])
    canonical = resolve_canonical_name(row['itemName'], alias_map)
    fingerprint = make_fingerprint(row['itemName'], row['itemPrice'], row['itemTimestamp'])
    return ArchiveItem(
        orig_item_id=row['orig_item_id'],
        itemName=row['itemName'],
        itemPrice=row['itemPrice'],
        itemTimestamp=row['itemTimestamp'],
        category=category,
        normalized_name=normalized,
        canonical_name=canonical,
        fingerprint=fingerprint,
        source_file=os.path.basename(source_file),
    )


def refresh_canonical_names():
    """Recompute canonical_name on all archive rows after alias changes."""
    alias_map = _load_alias_map()
    updated = 0
    for item in ArchiveItem.query.all():
        canonical = resolve_canonical_name(item.itemName, alias_map)
        if item.canonical_name != canonical:
            item.canonical_name = canonical
            updated += 1
    if updated:
        db.session.commit()
    return updated


def ingest_sql_file(path, alias_map, seen_fingerprints):
    inserted = 0
    skipped = 0
    with open(path, 'r', encoding='utf-8', errors='replace') as handle:
        sql_text = handle.read()
    for row in parse_item_rows_from_sql(sql_text):
        fp = make_fingerprint(row['itemName'], row['itemPrice'], row['itemTimestamp'])
        if fp in seen_fingerprints:
            skipped += 1
            continue
        seen_fingerprints.add(fp)
        db.session.add(_row_to_archive_item(row, path, alias_map))
        inserted += 1
    return inserted, skipped


def ingest_live_items(alias_map, seen_fingerprints):
    """Append current live Item rows not already in the archive."""
    from models import Item

    inserted = 0
    skipped = 0
    for live in Item.query.all():
        row = {
            'orig_item_id': live.itemID,
            'itemName': live.itemName,
            'itemPrice': live.itemPrice,
            'itemTimestamp': live.itemTimestamp,
            'category': live.category,
        }
        fp = make_fingerprint(row['itemName'], row['itemPrice'], row['itemTimestamp'])
        if fp in seen_fingerprints:
            skipped += 1
            continue
        seen_fingerprints.add(fp)
        db.session.add(_row_to_archive_item(row, 'live_mysql', alias_map))
        inserted += 1
    return inserted, skipped


def run_ingest(include_live=True, rebuild=False):
    """
    Ingest all SQL dumps (chronological) into archive DB.
    rebuild=True clears archive items first (aliases preserved).
    """
    run = IngestRun(started_at=datetime.utcnow(), status='running')
    db.session.add(run)
    db.session.commit()

    try:
        if rebuild:
            ArchiveItem.query.delete()
            db.session.commit()

        alias_map = _load_alias_map()
        seen = {row[0] for row in db.session.query(ArchiveItem.fingerprint).all()}
        total_inserted = 0
        total_skipped = 0
        files = list_sql_dumps(app.config)

        for path in files:
            ins, skp = ingest_sql_file(path, alias_map, seen)
            total_inserted += ins
            total_skipped += skp

        if include_live:
            ins, skp = ingest_live_items(alias_map, seen)
            total_inserted += ins
            total_skipped += skp

        run.files_processed = len(files)
        run.rows_inserted = total_inserted
        run.rows_skipped = total_skipped
        run.finished_at = datetime.utcnow()
        run.status = 'ok'
        run.message = 'Processed {} dump file(s).'.format(len(files))
        db.session.commit()
        return run
    except Exception as exc:
        db.session.rollback()
        run.status = 'error'
        run.finished_at = datetime.utcnow()
        run.message = str(exc)
        db.session.add(run)
        db.session.commit()
        raise


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        result = run_ingest(rebuild=True)
        print(result.status, result.rows_inserted, 'inserted', result.rows_skipped, 'skipped')
