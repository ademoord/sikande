#
#     file: seed.py
#     desc: Populate the local SQLite database with placeholder data from
#           the CSV files in ./data so the app is runnable without access
#           to the production MySQL database.
#
#           This only does anything when running locally (no ~/config.txt).
#           In production it is a no-op, so the real MySQL data is never touched.
#
import os
import csv
from datetime import datetime

from config import app, db
from models import Item, Debt, User

DATA_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data')

DATE_FORMATS = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d")


def _parse_dt(value):
    value = (value or "").strip()
    if not value:
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def _read_csv(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return []
    with open(path, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def seed():
    """Create tables and load placeholder data if the database is empty."""
    with app.app_context():
        db.create_all()

        if Item.query.first() is None:
            for row in _read_csv('items.csv'):
                db.session.add(Item(
                    itemName=row['itemName'],
                    itemPrice=int(row['itemPrice']),
                    itemTimestamp=_parse_dt(row['itemTimestamp']),
                    category=row['category'],
                ))

        if Debt.query.first() is None:
            for row in _read_csv('debts.csv'):
                db.session.add(Debt(
                    debtName=row['debtName'],
                    debtTotal=int(row['debtTotal']),
                    debtCreditor=row['debtCreditor'],
                    debtReceived=_parse_dt(row['debtReceived']),
                    debtDeadline=_parse_dt(row['debtDeadline']),
                ))

        if User.query.first() is None:
            for row in _read_csv('users.csv'):
                db.session.add(User(
                    username=row['username'],
                    password=row['password'],
                ))

        db.session.commit()


def seed_if_local():
    """Seed only when running in local development mode."""
    if app.config.get('LOCAL_DEV'):
        seed()


if __name__ == '__main__':
    seed()
    print('Local SQLite database seeded with placeholder data.')
