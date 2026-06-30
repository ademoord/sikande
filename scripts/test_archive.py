#!/usr/bin/env python3
"""Rebuild the local archive from sample SQL dumps and run sanity checks."""
import os
import sys

# Allow imports from project root when run as scripts/test_archive.py
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from archive_paths import list_sql_dumps, sql_dumps_dir
from archive_query import archive_stats, query_grouped_rows, top_recurring
from archive_ingest import run_ingest
from config import app, db
import archive_models  # noqa: F401


def main():
    dump_dir = sql_dumps_dir(app.config)
    dumps = list_sql_dumps(app.config)

    print('=== Sikande archive test ===')
    print('Mode:       {}'.format('LOCAL_DEV' if app.config.get('LOCAL_DEV') else 'production'))
    print('SQL dir:    {}'.format(dump_dir))
    print('Dump files: {}'.format(len(dumps)))
    for path in dumps:
        print('  - {}'.format(os.path.basename(path)))

    if not dumps:
        print('\nERROR: No sikande*.sql files found.')
        print('Add sample dumps to data/sql_samples/ (local) or ../Data/ (production).')
        return 1

    with app.app_context():
        db.create_all()
        run = run_ingest(rebuild=True)
        stats = archive_stats()

        print('\n--- Ingest ---')
        print('Status:   {}'.format(run.status))
        print('Inserted: {}'.format(run.rows_inserted))
        print('Skipped:  {} (duplicates)'.format(run.rows_skipped))

        if not stats:
            print('\nERROR: Archive is empty after ingest.')
            return 1

        print('\n--- Archive stats ---')
        print('Records:   {}'.format(stats['total_rows']))
        print('Total Rp:  {:,.0f}'.format(stats['total_amount']))
        print('Date span: {} -> {}'.format(
            stats['first_ts'].strftime('%Y-%m-%d'),
            stats['last_ts'].strftime('%Y-%m-%d'),
        ))
        print('Raw names: {} | Canonical groups: {}'.format(
            stats['distinct_names'], stats['distinct_canonical'],
        ))

        nas = query_grouped_rows(group_by='canonical', q='nas', per_page=10)
        print('\n--- Sanity: search "nas" (canonical groups) ---')
        print('Matches: {}'.format(nas['total_rows']))
        for row in nas['rows']:
            print('  {}  {}x  Rp{:,.0f}'.format(row.label, row.count, row.total))

        top = top_recurring(5)
        print('\n--- Top recurring (canonical) ---')
        for row in top:
            print('  {}  {}x  Rp{:,.0f}'.format(row['name'], row['count'], row['total']))

    print('\nOK — open http://127.0.0.1:5000/archive after starting the app.')
    print('Login (local): admin / admin')
    return 0


if __name__ == '__main__':
    sys.exit(main())
