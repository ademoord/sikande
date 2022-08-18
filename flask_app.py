#
#     file: flask_app.py
#     author: andromeda
#     desc: the main app
#
import datetime, pytz
from flask import Flask, render_template, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from functools import reduce
from operator import add


# START OF INIT AND CONFIG SECTION
# application init
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://sikande:financial2022@sikande.mysql.pythonanywhere-services.com/sikande$default'
app.config['SECRET_KEY'] = 'you-will-never-guess'

# assign the db object init
db = SQLAlchemy(app)
migrate = Migrate(app, db)
# END OF INIT AND CONFIG SECTION
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------



# START OF CUSTOM METHODS
# the time converter method
def gmt7now(dt_utc):
    dt_utc = datetime.datetime.utcnow()                                 # utcnow class method
    dt_rep = dt_utc.replace(tzinfo=pytz.UTC)                            # replace method
    dt_gmt7 = dt_rep.astimezone(pytz.timezone("Asia/Jakarta"))          # astimezone method
    return dt_gmt7

# the db integer sum method
def dbsumint(qr_int):
    db.session.rollback()                                               # rollback the object first
    total = db.session.query(qr_int)                                    # assign the integer column object by querying them
    sums = total.all()                                                  # joins them as a tuple
    joined = reduce(add, sums)                                          # joins them as a list
    result = sum(joined)                                                # sum that list and assign to a var
    return result


# END OF CUSTOM METHODS
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# START OF MODELS CREATION
# Item models
class Item(db.Model):
    itemID = db.Column(db.Integer, primary_key=True)
    itemName = db.Column(db.String(64), index=True, unique=False)
    itemPrice = db.Column(db.Integer, index=True)
    itemTimestamp = db.Column(db.DateTime, index=True)

    def __repr__(self):
        return '<Item {}>'.format(self.itemName)

# Debt models
class Debt(db.Model):
    debtID = db.Column(db.Integer, primary_key=True)
    debtName = db.Column(db.String(64), index=True, unique=False)
    debtTotal = db.Column(db.Integer, index=True)
    debtCreditor = db.Column(db.String(64), index=True, unique=False)
    debtReceived = db.Column(db.DateTime, index=True)
    debtDeadline = db.Column(db.DateTime, index=True)

    def __repr__(self):
        return '<Debt {}>'.format(self.debtName)


# END OF MODELS CREATION
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------



# START OF VIEW AND CONTROLLER SECTION


# Create a global var for the needs of time adjusting
dtCurrent = gmt7now(datetime.datetime.utcnow)
dtDay = dtCurrent.day
dtMon = dtCurrent.month


# Input view
@app.route('/')
def home():
    title = "Input"
    return render_template('index.html',
                            title=title
    )


# Reports view
@app.route('/reports', methods=['GET', 'POST'])
def reports():
    title = "Reports"
    if request.method == 'POST':
        qs = Item(itemName=request.form["item"],                       #
                itemPrice=request.form["harga"],                       # insert the data to db
                itemTimestamp=gmt7now(datetime.datetime.utcnow)        #
                )
        db.session.rollback()
        db.session.add(qs)
        db.session.commit()
        flash('Item was successfully added')
        items = Item.query.all()
        totalout = dbsumint(Item.itemPrice)

        return render_template('reports.html',
                                title=title,
                                item=items,
                                dt=dtCurrent,
                                curDay=dtDay,
                                curMon=dtMon,
                                totalout=totalout
        )
    else:
        db.session.rollback()
        items = Item.query.all()
        totalout = dbsumint(Item.itemPrice)

        return render_template('reports.html',
                                title=title,
                                item=items,
                                dt=dtCurrent,
                                curDay=dtDay,
                                curMon=dtMon,
                                totalout=totalout
        )


# Debts view
@app.route('/debts', methods=['GET', 'POST'])
def debts():
    title = "Debts"
    if request.method == 'POST':
        qs = Debt(debtName=request.form["debtname"],                       #
                debtTotal=request.form["debttotal"],                       #
                debtCreditor=request.form["debtcredit"],                   # insert the data to db
                debtReceived=gmt7now(datetime.datetime.utcnow),            #
                debtDeadline=request.form["debtdeadline"]                  #
                )
        db.session.rollback()
        db.session.add(qs)
        db.session.commit()
        flash('Debt was successfully added')

    debtList = Debt.query.all()
    totaldebt = dbsumint(Debt.debtTotal)
    return render_template('debts.html',
                            title=title,
                            debt=debtList,
                            dt=dtCurrent,
                            totaldebt=totaldebt
    )


# Plans view
@app.route('/plans', methods=['GET', 'POST'])
def plans():
    title = "Plans"
    return render_template('plans.html',
                            title=title
    )

# END OF VIEW AND CONTROLLER SECTION
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------



