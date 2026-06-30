"""Query helpers for archive search, filter, and grouping."""
from datetime import datetime

from sqlalchemy import func, or_

from archive_models import ArchiveItem
from config import db

ALLOWED_GROUP_BY = ('none', 'month', 'category', 'name', 'canonical')
ALLOWED_SORT = ('date_desc', 'date_asc', 'price_desc', 'price_asc', 'name_asc')


def _apply_filters(query, q=None, date_from=None, date_to=None, category=None,
                   price_min=None, price_max=None):
    if q:
        like = '%{}%'.format(q.strip())
        query = query.filter(or_(
            ArchiveItem.itemName.ilike(like),
            ArchiveItem.canonical_name.ilike(like),
            ArchiveItem.normalized_name.ilike(like),
        ))
    if date_from:
        query = query.filter(ArchiveItem.itemTimestamp >= date_from)
    if date_to:
        end = datetime.combine(date_to.date() if isinstance(date_to, datetime) else date_to,
                               datetime.max.time())
        query = query.filter(ArchiveItem.itemTimestamp <= end)
    if category:
        if category == 'legacy':
            query = query.filter(or_(ArchiveItem.category.is_(None), ArchiveItem.category == ''))
        else:
            query = query.filter(ArchiveItem.category == category)
    if price_min is not None:
        query = query.filter(ArchiveItem.itemPrice >= price_min)
    if price_max is not None:
        query = query.filter(ArchiveItem.itemPrice <= price_max)
    return query


def _apply_sort(query, sort='date_desc'):
    if sort == 'date_asc':
        return query.order_by(ArchiveItem.itemTimestamp.asc(), ArchiveItem.id.asc())
    if sort == 'price_desc':
        return query.order_by(ArchiveItem.itemPrice.desc(), ArchiveItem.itemTimestamp.desc())
    if sort == 'price_asc':
        return query.order_by(ArchiveItem.itemPrice.asc(), ArchiveItem.itemTimestamp.asc())
    if sort == 'name_asc':
        return query.order_by(ArchiveItem.itemName.asc(), ArchiveItem.itemTimestamp.desc())
    return query.order_by(ArchiveItem.itemTimestamp.desc(), ArchiveItem.id.desc())


def _filtered_sum(q=None, date_from=None, date_to=None, category=None,
                  price_min=None, price_max=None):
    sum_query = db.session.query(func.coalesce(func.sum(ArchiveItem.itemPrice), 0))
    sum_query = _apply_filters(sum_query, q, date_from, date_to, category, price_min, price_max)
    return int(sum_query.scalar() or 0)


def query_detail_rows(q=None, date_from=None, date_to=None, category=None,
                      price_min=None, price_max=None, sort='date_desc',
                      page=1, per_page=50):
    query = ArchiveItem.query
    query = _apply_filters(query, q, date_from, date_to, category, price_min, price_max)
    query = _apply_sort(query, sort)
    total = query.count()
    rows = query.offset((page - 1) * per_page).limit(per_page).all()
    page_total = sum(r.itemPrice for r in rows)
    return {
        'mode': 'detail',
        'rows': rows,
        'total_rows': total,
        'page': page,
        'per_page': per_page,
        'pages': max(1, (total + per_page - 1) // per_page),
        'filtered_total': _filtered_sum(q, date_from, date_to, category, price_min, price_max),
        'page_total': page_total,
    }


def query_grouped_rows(group_by='month', q=None, date_from=None, date_to=None, category=None,
                       price_min=None, price_max=None, sort='date_desc',
                       page=1, per_page=50):
    if group_by not in ALLOWED_GROUP_BY or group_by == 'none':
        return query_detail_rows(q, date_from, date_to, category, price_min, price_max,
                                 sort, page, per_page)

    base = _apply_filters(ArchiveItem.query, q, date_from, date_to, category,
                          price_min, price_max)

    if group_by == 'month':
        label_expr = func.strftime('%Y-%m', ArchiveItem.itemTimestamp)
        group_expr = label_expr
    elif group_by == 'category':
        label_expr = func.coalesce(ArchiveItem.category, 'legacy')
        group_expr = label_expr
    elif group_by == 'name':
        label_expr = ArchiveItem.itemName
        group_expr = ArchiveItem.itemName
    else:  # canonical
        label_expr = ArchiveItem.canonical_name
        group_expr = ArchiveItem.canonical_name

    grouped = base.with_entities(
        label_expr.label('label'),
        func.count(ArchiveItem.id).label('count'),
        func.coalesce(func.sum(ArchiveItem.itemPrice), 0).label('total'),
        func.min(ArchiveItem.itemTimestamp).label('first_seen'),
        func.max(ArchiveItem.itemTimestamp).label('last_seen'),
    ).group_by(group_expr)

    if sort in ('price_desc', 'price_asc'):
        order_col = func.coalesce(func.sum(ArchiveItem.itemPrice), 0)
        grouped = grouped.order_by(order_col.desc() if sort == 'price_desc' else order_col.asc())
    elif sort == 'name_asc':
        grouped = grouped.order_by(label_expr.asc())
    else:
        grouped = grouped.order_by(func.max(ArchiveItem.itemTimestamp).desc())

    subq = grouped.subquery()
    total = db.session.query(func.count()).select_from(subq).scalar() or 0
    rows = grouped.offset((page - 1) * per_page).limit(per_page).all()

    return {
        'mode': 'grouped',
        'group_by': group_by,
        'rows': rows,
        'total_rows': total,
        'page': page,
        'per_page': per_page,
        'pages': max(1, (total + per_page - 1) // per_page),
        'filtered_total': _filtered_sum(q, date_from, date_to, category, price_min, price_max),
    }


def archive_stats():
    """Summary numbers for dashboard and archive header."""
    total_rows = ArchiveItem.query.count()
    if total_rows == 0:
        return None
    total_amount = db.session.query(func.coalesce(func.sum(ArchiveItem.itemPrice), 0)).scalar()
    first_ts = db.session.query(func.min(ArchiveItem.itemTimestamp)).scalar()
    last_ts = db.session.query(func.max(ArchiveItem.itemTimestamp)).scalar()
    distinct_names = db.session.query(func.count(func.distinct(ArchiveItem.itemName))).scalar()
    distinct_canonical = db.session.query(func.count(func.distinct(ArchiveItem.canonical_name))).scalar()
    return {
        'total_rows': total_rows,
        'total_amount': int(total_amount or 0),
        'first_ts': first_ts,
        'last_ts': last_ts,
        'distinct_names': distinct_names,
        'distinct_canonical': distinct_canonical,
    }


def monthly_totals(limit_months=24):
    rows = db.session.query(
        func.strftime('%Y-%m', ArchiveItem.itemTimestamp).label('month'),
        func.count(ArchiveItem.id).label('count'),
        func.coalesce(func.sum(ArchiveItem.itemPrice), 0).label('total'),
    ).group_by('month').order_by('month').all()
    if limit_months and len(rows) > limit_months:
        rows = rows[-limit_months:]
    return [{'month': r.month, 'count': r.count, 'total': int(r.total)} for r in rows]


def yoy_comparison():
    """Compare current calendar month total vs same month last year."""
    now = datetime.utcnow()
    cur = db.session.query(func.coalesce(func.sum(ArchiveItem.itemPrice), 0)).filter(
        func.strftime('%Y', ArchiveItem.itemTimestamp) == str(now.year),
        func.strftime('%m', ArchiveItem.itemTimestamp) == '{:02d}'.format(now.month),
    ).scalar()
    prev = db.session.query(func.coalesce(func.sum(ArchiveItem.itemPrice), 0)).filter(
        func.strftime('%Y', ArchiveItem.itemTimestamp) == str(now.year - 1),
        func.strftime('%m', ArchiveItem.itemTimestamp) == '{:02d}'.format(now.month),
    ).scalar()
    cur = int(cur or 0)
    prev = int(prev or 0)
    pct = round((cur - prev) / prev * 100, 1) if prev else None
    return {'current': cur, 'previous': prev, 'pct_change': pct, 'month': now.month, 'year': now.year}


def top_recurring(limit=10):
    rows = db.session.query(
        ArchiveItem.canonical_name.label('name'),
        func.count(ArchiveItem.id).label('count'),
        func.coalesce(func.sum(ArchiveItem.itemPrice), 0).label('total'),
    ).group_by(ArchiveItem.canonical_name).order_by(
        func.count(ArchiveItem.id).desc()
    ).limit(limit).all()
    return [{'name': r.name, 'count': r.count, 'total': int(r.total)} for r in rows]


def category_breakdown():
    rows = db.session.query(
        func.coalesce(ArchiveItem.category, 'legacy').label('category'),
        func.count(ArchiveItem.id).label('count'),
        func.coalesce(func.sum(ArchiveItem.itemPrice), 0).label('total'),
    ).group_by('category').order_by(func.sum(ArchiveItem.itemPrice).desc()).all()
    return [{'category': r.category, 'count': r.count, 'total': int(r.total)} for r in rows]


def fuzzy_name_suggestions(query_text, limit=8):
    """Suggest similar raw item names using difflib (for alias UI)."""
    import difflib
    q = (query_text or '').strip()
    if len(q) < 2:
        return []
    names = [
        row[0] for row in db.session.query(ArchiveItem.itemName).distinct().all()
    ]
    matches = difflib.get_close_matches(q, names, n=limit, cutoff=0.55)
    return matches


def distinct_raw_names(prefix='', limit=30):
    query = db.session.query(ArchiveItem.itemName).distinct()
    if prefix:
        query = query.filter(ArchiveItem.itemName.ilike('%{}%'.format(prefix.strip())))
    return [row[0] for row in query.order_by(ArchiveItem.itemName).limit(limit).all()]
