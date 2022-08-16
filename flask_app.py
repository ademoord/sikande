#
#     file: flask_app.py
#     author: andromeda
#     desc: the main app
#
import datetime, pytz
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate


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
# the timeConverter method
def gmt7now(dt_utc):
    dt_utc = datetime.datetime.utcnow()                                # utcnow class method
    dt_rep = dt_utc.replace(tzinfo=pytz.UTC)                           # replace method
    dt_gmt7 = dt_rep.astimezone(pytz.timezone("Asia/Jakarta"))         # astimezone method
    return dt_gmt7

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
    debtTimestamp = db.Column(db.DateTime, index=True)

    def __repr__(self):
        return '<Debt {}>'.format(self.itemName)


# END OF MODELS CREATION
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------



# START OF VIEW AND CONTROLLER SECTION
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
    title = "Finance Report"
    dtCurrent = gmt7now(datetime.datetime.utcnow)
    dtDay = dtCurrent.day
    dtMon = dtCurrent.month
    if request.method == 'POST':
        qs = Item(itemName=request.form["item"],                       #
                itemPrice=request.form["harga"],                       # insert the data to db
                itemTimestamp=gmt7now(datetime.datetime.utcnow)        #
                )
        db.session.rollback()
        db.session.add(qs)
        db.session.commit()
        items = Item.query.all()

        return render_template('reports.html',
                                title=title,
                                item=items,
                                curDay=dtDay,
                                curMon=dtMon
        )
    else:
        db.session.rollback()
        items = Item.query.all()

        return render_template('reports.html',
                                title=title,
                                item=items,
                                curDay=dtDay,
                                curMon=dtMon
        )


# Debts view
@app.route('/debts')
def debts():
    title = "Debts"
    return render_template('debts.html',
                            title=title
    )

# END OF VIEW AND CONTROLLER SECTION
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------



