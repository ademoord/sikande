"""Resolve paths for SQL dump sources and the archive SQLite database."""
import os
import re

_BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Indonesian + English month tokens in dump filenames (sikandeFeb23.sql, sikandeMei23.sql, …)
_MONTH_TOKENS = {
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'mei': 5,
    'jun': 6, 'jul': 7, 'agu': 8, 'agt': 8, 'aug': 8,
    'sep': 9, 'oct': 10, 'okt': 10, 'nov': 11, 'dec': 12, 'des': 12,
}


def is_local_dev(app_config):
    return bool(app_config.get('LOCAL_DEV'))


def sql_dumps_dir(app_config):
    """Directory containing sikande*.sql backup files."""
    if is_local_dev(app_config):
        path = os.path.join(_BASE_DIR, 'data', 'sql_samples')
    else:
        path = os.path.join(os.path.dirname(_BASE_DIR), 'Data')
    return path


def archive_db_path(app_config):
    """SQLite file used for the read-only historical archive."""
    if is_local_dev(app_config):
        data_dir = os.path.join(_BASE_DIR, 'data')
        os.makedirs(data_dir, exist_ok=True)
        return os.path.join(data_dir, 'archive.sqlite3')
    data_dir = os.path.join(os.path.dirname(_BASE_DIR), 'Data')
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, 'archive.sqlite3')


def dump_sort_key(filename):
    """
    Sort dump files chronologically from filename, e.g. sikandeFeb23.sql -> (2023, 2).
    Combined dumps like sikandeDes23danJan24.sql use the earliest month found.
    """
    stem = os.path.splitext(os.path.basename(filename))[0]
    stem = stem.replace('sikande', '', 1)
    matches = re.findall(r'([a-zA-Z]{3})(\d{2})', stem)
    if not matches:
        return (9999, 99, filename)
    keys = []
    for month_token, yy in matches:
        month = _MONTH_TOKENS.get(month_token.lower())
        if month is None:
            continue
        year = 2000 + int(yy)
        keys.append((year, month))
    if not keys:
        return (9999, 99, filename)
    year, month = min(keys)
    return (year, month, filename)


def list_sql_dumps(app_config):
    dump_dir = sql_dumps_dir(app_config)
    if not os.path.isdir(dump_dir):
        return []
    files = [
        os.path.join(dump_dir, name)
        for name in os.listdir(dump_dir)
        if name.lower().endswith('.sql') and name.lower().startswith('sikande')
    ]
    return sorted(files, key=dump_sort_key)
