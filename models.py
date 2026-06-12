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

# Plan model (savings goals)
class Plan(db.Model):
    planID = db.Column(db.Integer, primary_key=True)
    planName = db.Column(db.String(80), index=True)
    planType = db.Column(db.String(20), index=True)   # umrah, house, car, other
    targetAmount = db.Column(db.Float)
    savedAmount = db.Column(db.Float)
    targetDate = db.Column(db.DateTime, index=True)
    planTimestamp = db.Column(db.DateTime, index=True)  # created/start date

    def __repr__(self):
        return '<Plan {}>'.format(self.planName)

# Investment model
class Investment(db.Model):
    invID = db.Column(db.Integer, primary_key=True)
    invType = db.Column(db.String(20), index=True)   # gold, bitcoin, stock, currency
    asset = db.Column(db.String(40), index=True)     # Antam / HRTA / BTC / ETH / ticker / USD
    quantity = db.Column(db.Float)                    # grams (gold) or units (others)
    buyPrice = db.Column(db.Float)                    # purchase price per unit (Rp)
    currentPrice = db.Column(db.Float)               # latest market price per unit (Rp)
    invTimestamp = db.Column(db.DateTime, index=True)

    def __repr__(self):
        return '<Investment {} {}>'.format(self.invType, self.asset)

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
