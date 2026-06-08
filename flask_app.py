#
#     file: flask_app.py
#     author: andromeda
#     desc: the main app
#
# import datetime
from datetime import datetime
import helpers
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from config import app, db, login_manager
from models import Item, Debt, User
import os
import subprocess

# When running locally (no production config.txt), build and seed a local
# SQLite database with placeholder data. This is a no-op in production.
if app.config.get('LOCAL_DEV'):
    from seed import seed_if_local
    seed_if_local()

# START OF VIEW AND CONTROLLER SECTION

# Create a global var for the needs of time adjustment
dtCurrent = helpers.gmt7now(datetime.utcnow)
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
    totalout = helpers.dbsumint(Item.itemPrice)
    item_count = Item.query.count()
    debt_count = Debt.query.count()
    total_debt = helpers.dbsumint(Debt.debtTotal)
    return render_template('dashboard.html',
                            title=title,
                            totalout=totalout,
                            item_count=item_count,
                            debt_count=debt_count,
                            total_debt=total_debt,
                            dt=dtCurrent)

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

    # Create a mapping of category values to their corresponding names
    category_mapping = {
        'needs': 'Kebutuhan Sehari-hari',
        'liabilities': 'Hutang',
        'saving': 'Tabungan',
        'charity': 'Kebaikan',
        'fun': 'Jajan & Hiburan',
        'urgent': 'Keperluan Darurat'
    }

    title = "Reports"
    try:
        if request.method == 'POST':
            # Process the POST request and save the data
            category = request.form["category"]
            item = request.form["item"]
            harga = request.form["harga"]

            print("CATEG",category)
            print("ITEM",item)
            print("HARG",harga)

            qs = Item(
                itemName=item,
                itemPrice=harga,
                itemTimestamp=helpers.gmt7now(datetime.utcnow()),
                category=category  # Add the selected category
            )

            db.session.rollback()
            db.session.add(qs)
            db.session.commit()
            flash('Item was successfully added')

        # Retrieve data and render the template
        items = Item.query.all()
        totalout = helpers.dbsumint(Item.itemPrice)
        return render_template('reports.html', title=title, item=items, dt=dtCurrent, curDay=dtDay, curMon=dtMon,
                               totalout=totalout, category_mapping=category_mapping)
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
                debtReceived=helpers.gmt7now(datetime.utcnow),            #
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

# Settings view
@app.route('/settings', methods=['GET', 'POST'])
def settings():
    title = "Settings"
    return render_template('settings.html',
                            title=title)

@app.route('/api/bar_chart_data')
def bar_chart_data():
    # Fetch current year and month
    now = datetime.now()
    current_month = now.month
    current_year = now.year

    # Query to get item data for the current month and year
    items = db.session.query(
        Item.category,
        db.func.count(Item.itemID).label('count')
    ).filter(
        db.func.extract('month', Item.itemTimestamp) == current_month,
        db.func.extract('year', Item.itemTimestamp) == current_year
    ).group_by(Item.category).all()

    # Prepare data for the chart
    labels = [item.category for item in items]
    values = [item.count for item in items]

    return jsonify({'labels': labels, 'values': values})

@app.route('/api/doughnut_chart_data')
@login_required
def doughnut_chart_data():
    data = db.session.query(
        Item.category, db.func.count(Item.category)
    ).group_by(Item.category).all()

    categories = [row[0] for row in data]
    counts = [row[1] for row in data]

    return {
        'categories': categories,
        'counts': counts
    }

# Route for backup
@app.route('/backup', methods=['POST'])
def backup():
    current_month_year = datetime.now().strftime("%b%y")  # Format like Aug24
    backup_file = f"sikande{current_month_year}.sql"

    # Construct the backup command
    command = [
        "mysqldump", "-u", "sikande", "-h", "sikande.mysql.pythonanywhere-services.com",
        "--set-gtid-purged=OFF", "--no-tablespaces", "--column-statistics=0",
        "'sikande$default'", f">{backup_file}"
    ]

    # Execute the backup command
    try:
        subprocess.run(" ".join(command), shell=True, check=True)
        return redirect(url_for('settings'))
    except subprocess.CalledProcessError as e:
        return f"Error during backup: {e}", 500

# Route for truncating 'item' table
@app.route('/truncate', methods=['POST'])
def truncate_item():
    try:
        db.session.execute('TRUNCATE TABLE item')
        db.session.commit()
        return redirect(url_for('settings'))
    except Exception as e:
        return f"Error truncating items: {e}", 500


# Local development entry point. In production the app is served via WSGI,
# so this block is ignored there.
if __name__ == '__main__':
    app.run(debug=True)

