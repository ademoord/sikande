from sqlalchemy import CheckConstraint
from flask_login import UserMixin
from config import db

# START OF MODELS CREATION
# Item model
class Item(db.Model):
    itemID = db.Column(db.Integer, primary_key=True)
    itemName = db.Column(db.String(64), index=True, unique=False)
    itemPrice = db.Column(db.Integer, index=True)
    itemTimestamp = db.Column(db.DateTime, index=True)
    category = db.Column(db.String(20), index=True)

    # Add a check constraint to enforce allowed values
    __table_args__ = (
        CheckConstraint(category.in_(['needs', 'liabilities', 'saving', 'charity', 'fun', 'urgent'])),
    )

    def __repr__(self):
        return '<Item {}>'.format(self.itemName)

# Debt model
class Debt(db.Model):
    debtID = db.Column(db.Integer, primary_key=True)
    debtName = db.Column(db.String(64), index=True, unique=False)
    debtTotal = db.Column(db.Integer, index=True)
    debtCreditor = db.Column(db.String(64), index=True, unique=False)
    debtReceived = db.Column(db.DateTime, index=True)
    debtDeadline = db.Column(db.DateTime, index=True)

    def __repr__(self):
        return '<Debt {}>'.format(self.debtName)

# User model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

    def __init__(self, username, password):
        self.username = username
        self.password = password


# END OF MODELS CREATION
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
