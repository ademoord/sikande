"""SQLAlchemy models stored in the archive SQLite bind."""
from datetime import datetime

from config import db


class ArchiveItem(db.Model):
    __bind_key__ = 'archive'
    __tablename__ = 'archive_item'

    id = db.Column(db.Integer, primary_key=True)
    orig_item_id = db.Column(db.Integer, index=True)
    itemName = db.Column(db.String(64), index=True, nullable=False)
    itemPrice = db.Column(db.Integer, index=True, nullable=False)
    itemTimestamp = db.Column(db.DateTime, index=True, nullable=False)
    category = db.Column(db.String(20), index=True)
    normalized_name = db.Column(db.String(64), index=True)
    canonical_name = db.Column(db.String(64), index=True)
    fingerprint = db.Column(db.String(64), unique=True, index=True, nullable=False)
    source_file = db.Column(db.String(128))
    ingested_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<ArchiveItem {} {}>'.format(self.itemName, self.itemTimestamp)


class ItemAlias(db.Model):
    __bind_key__ = 'archive'
    __tablename__ = 'item_alias'

    id = db.Column(db.Integer, primary_key=True)
    raw_name = db.Column(db.String(64), index=True, nullable=False)
    normalized_raw = db.Column(db.String(64), unique=True, index=True, nullable=False)
    canonical_name = db.Column(db.String(64), index=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<ItemAlias {} -> {}>'.format(self.raw_name, self.canonical_name)


class IngestRun(db.Model):
    __bind_key__ = 'archive'
    __tablename__ = 'ingest_run'

    id = db.Column(db.Integer, primary_key=True)
    started_at = db.Column(db.DateTime, nullable=False)
    finished_at = db.Column(db.DateTime)
    files_processed = db.Column(db.Integer, default=0)
    rows_inserted = db.Column(db.Integer, default=0)
    rows_skipped = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='running')
    message = db.Column(db.Text)

    def __repr__(self):
        return '<IngestRun {} {}>'.format(self.id, self.status)
