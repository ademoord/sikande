"""Dashboard spending stats for Current Month vs All Time views."""
from datetime import datetime

from sqlalchemy import extract, func

from archive_models import ArchiveItem
from archive_query import archive_stats, monthly_totals, top_recurring
from config import db
from models import Item

VALID_RANGES = ('month', 'all')


def parse_range(value):
    return value if value in VALID_RANGES else 'month'


def _month_filters(model):
    now = datetime.now()
    return (
        extract('month', model.itemTimestamp) == now.month,
        extract('year', model.itemTimestamp) == now.year,
    )


def _build_category_stats(cat_rows, totalout, category_mapping, category_colors):
    stats = []
    for cat, cnt, total in cat_rows:
        total = int(total or 0)
        key = cat or 'legacy'
        stats.append({
            'key': key,
            'name': category_mapping.get(key, key if key != 'legacy' else 'Legacy'),
            'color': category_colors.get(key, '#8a8170' if key == 'legacy' else '#c9a227'),
            'count': cnt,
            'total': total,
            'pct': round(total / totalout * 100) if totalout else 0,
        })
    stats.sort(key=lambda c: c['total'], reverse=True)
    return stats


def _spending_from_live(month_only, category_mapping, category_colors):
    filters = list(_month_filters(Item)) if month_only else []

    totalout = int(db.session.query(func.coalesce(func.sum(Item.itemPrice), 0)).filter(*filters).scalar() or 0)
    item_count = db.session.query(func.count(Item.itemID)).filter(*filters).scalar() or 0
    avg_item = round(totalout / item_count) if item_count else 0

    cat_rows = db.session.query(
        Item.category,
        func.count(Item.itemID),
        func.coalesce(func.sum(Item.itemPrice), 0),
    ).filter(*filters).group_by(Item.category).all()
    category_stats = _build_category_stats(cat_rows, totalout, category_mapping, category_colors)

    freq_row = db.session.query(
        Item.itemName,
        func.count(Item.itemID),
        func.coalesce(func.sum(Item.itemPrice), 0),
    ).filter(*filters).group_by(Item.itemName).order_by(func.count(Item.itemID).desc()).first()
    top_item = None
    if freq_row:
        top_item = {'name': freq_row[0], 'count': freq_row[1], 'total': int(freq_row[2] or 0)}

    hi = db.session.query(Item).filter(*filters).order_by(Item.itemPrice.desc()).first()
    highest_item = None
    if hi:
        highest_item = {
            'name': hi.itemName,
            'price': hi.itemPrice,
            'category': category_mapping.get(hi.category, hi.category),
        }

    top_cat_rp = category_stats[0] if category_stats else None
    top_cat_count = max(category_stats, key=lambda c: c['count']) if category_stats else None

    return {
        'totalout': totalout,
        'item_count': item_count,
        'avg_item': avg_item,
        'category_stats': category_stats,
        'top_cat_rp': top_cat_rp,
        'top_cat_count': top_cat_count,
        'top_item': top_item,
        'highest_item': highest_item,
    }


def _spending_from_archive(category_mapping, category_colors):
    totalout = int(db.session.query(func.coalesce(func.sum(ArchiveItem.itemPrice), 0)).scalar() or 0)
    item_count = ArchiveItem.query.count()
    avg_item = round(totalout / item_count) if item_count else 0

    cat_rows = db.session.query(
        func.coalesce(ArchiveItem.category, 'legacy'),
        func.count(ArchiveItem.id),
        func.coalesce(func.sum(ArchiveItem.itemPrice), 0),
    ).group_by('category').order_by(func.sum(ArchiveItem.itemPrice).desc()).all()
    category_stats = _build_category_stats(cat_rows, totalout, category_mapping, category_colors)

    freq_row = db.session.query(
        ArchiveItem.canonical_name,
        func.count(ArchiveItem.id),
        func.coalesce(func.sum(ArchiveItem.itemPrice), 0),
    ).group_by(ArchiveItem.canonical_name).order_by(func.count(ArchiveItem.id).desc()).first()
    top_item = None
    if freq_row:
        top_item = {'name': freq_row[0], 'count': freq_row[1], 'total': int(freq_row[2] or 0)}

    hi = ArchiveItem.query.order_by(ArchiveItem.itemPrice.desc()).first()
    highest_item = None
    if hi:
        key = hi.category or 'legacy'
        highest_item = {
            'name': hi.itemName,
            'price': hi.itemPrice,
            'category': category_mapping.get(key, key if key != 'legacy' else 'Legacy'),
        }

    top_cat_rp = category_stats[0] if category_stats else None
    top_cat_count = max(category_stats, key=lambda c: c['count']) if category_stats else None
    hist = archive_stats()

    return {
        'totalout': totalout,
        'item_count': item_count,
        'avg_item': avg_item,
        'category_stats': category_stats,
        'top_cat_rp': top_cat_rp,
        'top_cat_count': top_cat_count,
        'top_item': top_item,
        'highest_item': highest_item,
        'archive_from': hist['first_ts'] if hist else None,
        'archive_to': hist['last_ts'] if hist else None,
        'hist_top': top_recurring(5),
        'monthly_chart': monthly_totals(limit_months=24),
    }


def get_spending_context(range_mode, category_mapping, category_colors):
    """Build spending block for dashboard (stats + chart flags)."""
    if range_mode == 'month':
        ctx = _spending_from_live(True, category_mapping, category_colors)
        ctx.update({
            'range': 'month',
            'range_label': 'Current Month',
            'show_monthly_chart': False,
            'data_source': 'live',
        })
        return ctx

    if archive_stats():
        ctx = _spending_from_archive(category_mapping, category_colors)
        ctx.update({
            'range': 'all',
            'range_label': 'All Time',
            'show_monthly_chart': True,
            'data_source': 'archive',
        })
        return ctx

    ctx = _spending_from_live(False, category_mapping, category_colors)
    ctx.update({
        'range': 'all',
        'range_label': 'All Time',
        'show_monthly_chart': False,
        'data_source': 'live',
        'archive_note': 'Rebuild the archive in Settings for full historical data.',
    })
    return ctx


def chart_doughnut_data(range_mode):
    """Category counts for the spending doughnut chart."""
    if range_mode == 'month':
        filters = list(_month_filters(Item))
        rows = db.session.query(
            Item.category, func.count(Item.itemID)
        ).filter(*filters).group_by(Item.category).all()
        return {'categories': [r[0] for r in rows], 'counts': [r[1] for r in rows]}

    if archive_stats():
        rows = db.session.query(
            func.coalesce(ArchiveItem.category, 'legacy'),
            func.count(ArchiveItem.id),
        ).group_by('category').all()
        return {'categories': [r[0] for r in rows], 'counts': [r[1] for r in rows]}

    rows = db.session.query(
        Item.category, func.count(Item.itemID)
    ).group_by(Item.category).all()
    return {'categories': [r[0] for r in rows], 'counts': [r[1] for r in rows]}


def chart_monthly_totals(range_mode):
    if range_mode != 'all' or not archive_stats():
        return {'labels': [], 'totals': [], 'counts': []}
    rows = monthly_totals(limit_months=24)
    return {
        'labels': [r['month'] for r in rows],
        'totals': [r['total'] for r in rows],
        'counts': [r['count'] for r in rows],
    }
