#
#     file: flask_app.py
#     author: andromeda
#     desc: the main app
#
import datetime
import helpers
from flask import render_template, request, redirect, url_for, flash
from flask_login import UserMixin, login_user, logout_user, login_required, current_user
from config import app, db, login_manager

# START OF MODELS CREATION
# Item model
class Item(db.Model):
    itemID = db.Column(db.Integer, primary_key=True)
    itemName = db.Column(db.String(64), index=True, unique=False)
    itemPrice = db.Column(db.Integer, index=True)
    itemTimestamp = db.Column(db.DateTime, index=True)

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
# START OF VIEW AND CONTROLLER SECTION

# Create a global var for the needs of time adjustment
dtCurrent = helpers.gmt7now(datetime.datetime.utcnow)
dtDay = dtCurrent.day
dtMon = dtCurrent.month

# User loader view
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Dashboard view
@app.route('/dashboard')
def dashboard():
    title = "Dashboard"
    return render_template('dashboard.html',
                            title=title)

# Index view
@app.route('/')
def index():
    if current_user.is_authenticated:
        # User is authenticated, show dashboard contents
        # Modify this part according to your dashboard content
        return redirect(url_for('dashboard'))
    else:
        # User is not authenticated, redirect to the login view
        return redirect(url_for('login'))

# Input view
@app.route('/input')
@login_required
def input():
    title = "Input"
    return render_template('input.html',
                            title=title)

# Login view
@app.route('/login', methods=['GET', 'POST'])
def login():
    title = "Login"
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('input'))
        else:
            flash('Invalid username or password.', 'error')
    return render_template('login.html',
                            title=title)

# Logout view
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))

# Reports view
@app.route('/reports', methods=['GET', 'POST'])
@login_required
def reports():
    title = "Reports"
    try:
        if request.method == 'POST':
            # Process the POST request and save the data
            qs = Item(
                itemName=request.form["item"],
                itemPrice=request.form["harga"],
                itemTimestamp=helpers.gmt7now(datetime.datetime.utcnow)
            )
            db.session.rollback()
            db.session.add(qs)
            db.session.commit()
            flash('Item was successfully added')
        # Retrieve data and render the template
        items = Item.query.all()
        totalout = helpers.dbsumint(Item.itemPrice)
        return render_template('reports.html', title=title, item=items, dt=dtCurrent, curDay=dtDay, curMon=dtMon,
                               totalout=totalout)
    except Exception as e:
        return redirect(url_for('input'))  # Redirect to the "input" route if 500 Internal Server Error

# Delete item view
@app.route('/item/del/<int:itemID>', methods=['GET', 'POST'])
@login_required
def delete_item(itemID):
    try:
        item = Item.query.get(itemID)
        if item:
            db.session.delete(item)
            db.session.commit()
    except Exception as e:
        return redirect(url_for('input'))  # Redirect to the "input" route if 500 Internal Server Error
    return redirect(url_for('input'))  # Redirect to the "input" route after deletion

# Debts view
@app.route('/debts', methods=['GET', 'POST'])
def debts():
    title = "Debts"
    if request.method == 'POST':
        qs = Debt(debtName=request.form["debtname"],                       #
                debtTotal=request.form["debttotal"],                       #
                debtCreditor=request.form["debtcredit"],                   # insert the data to db
                debtReceived=helpers.gmt7now(datetime.datetime.utcnow),            #
                debtDeadline=request.form["debtdeadline"]                  #
                )
        db.session.rollback()
        db.session.add(qs)
        db.session.commit()
        flash('Debt was successfully added')

    debtList = Debt.query.all()
    totaldebt = helpers.dbsumint(Debt.debtTotal)
    return render_template('debts.html',
                            title=title,
                            debt=debtList,
                            dt=dtCurrent,
                            totaldebt=totaldebt)

# Plans view
@app.route('/plans', methods=['GET', 'POST'])
def plans():
    title = "Plans"
    return render_template('plans.html',
                            title=title)

# END OF VIEW AND CONTROLLER SECTION
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------



