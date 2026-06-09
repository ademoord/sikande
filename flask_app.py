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
from models import Item, Debt, User, Investment
import os
import subprocess

# Ensure all tables exist in whichever database is configured. create_all only
# creates missing tables (it never alters/drops), so this safely adds new tables
# like `investment` on a production MySQL reload without a manual migration.
with app.app_context():
    db.create_all()

# When running locally (no production config.txt), build and seed a local
# SQLite database with placeholder data. This is a no-op in production.
if app.config.get('LOCAL_DEV'):
    from seed import seed_if_local
    seed_if_local()


@app.after_request
def set_security_headers(response):
    # In production, PythonAnywhere terminates TLS at its proxy and forwards the
    # request to the app with X-Forwarded-Proto: https. When the visitor is on
    # HTTPS, emit HSTS so browsers (especially mobile) auto-upgrade any future
    # http:// visit to https:// on their own. Never sent during local http dev,
    # so it can't force-https your localhost.
    if not app.config.get('LOCAL_DEV') and request.headers.get('X-Forwarded-Proto') == 'https':
        response.headers['Strict-Transport-Security'] = 'max-age=31536000'
    return response

# START OF VIEW AND CONTROLLER SECTION

# Create a global var for the needs of time adjustment
dtCurrent = helpers.gmt7now(datetime.utcnow)
dtDay = dtCurrent.day
dtMon = dtCurrent.month

# Shared category metadata (display names + chart/bar colors)
CATEGORY_MAPPING = {
    'needs': 'Kebutuhan Sehari-hari',
    'liabilities': 'Hutang',
    'saving': 'Tabungan',
    'charity': 'Kebaikan',
    'fun': 'Jajan & Hiburan',
    'urgent': 'Keperluan Darurat',
}

CATEGORY_COLORS = {
    'needs': 'forestgreen',
    'liabilities': 'mediumpurple',
    'saving': 'lightskyblue',
    'charity': 'mediumseagreen',
    'fun': 'lightsalmon',
    'urgent': 'indianred',
}

# Investment metadata
INVESTMENT_TYPES = {
    'gold': 'Gold',
    'bitcoin': 'Crypto',
    'stock': 'Stock',
    'currency': 'Currency',
}

GOLD_BRANDS = ['Antam', 'HRTA', 'BullionKey', 'Lotus', 'Other']
CRYPTO_COINS = ['BTC', 'ETH']
ALLOWED_INV_TYPES = tuple(INVESTMENT_TYPES.keys())

INVESTMENT_COLORS = {
    'gold': 'goldenrod',
    'bitcoin': 'darkorange',
    'stock': 'steelblue',
    'currency': 'mediumseagreen',
}


def _investment_form_asset(inv_type, form):
    """Resolve the asset/brand/symbol from the right sub-field for each type."""
    if inv_type == 'gold':
        return (form.get('asset_gold') or '').strip()
    if inv_type == 'bitcoin':
        return (form.get('asset_crypto') or '').strip()
    if inv_type == 'stock':
        return (form.get('asset_stock') or '').strip().upper()
    if inv_type == 'currency':
        return (form.get('asset_currency') or '').strip().upper()
    return ''

# User loader view
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Dashboard view
@app.route('/dashboard')
def dashboard():
    title = "Dashboard"
    db.session.rollback()

    totalout = helpers.dbsumint(Item.itemPrice)
    item_count = Item.query.count()
    debt_count = Debt.query.count()
    total_debt = helpers.dbsumint(Debt.debtTotal)
    avg_item = round(totalout / item_count) if item_count else 0

    # Totals + counts per category
    cat_rows = db.session.query(
        Item.category,
        db.func.count(Item.itemID),
        db.func.coalesce(db.func.sum(Item.itemPrice), 0)
    ).group_by(Item.category).all()

    category_stats = []
    for cat, cnt, total in cat_rows:
        total = int(total or 0)
        category_stats.append({
            'key': cat,
            'name': CATEGORY_MAPPING.get(cat, cat),
            'color': CATEGORY_COLORS.get(cat, '#c9a227'),
            'count': cnt,
            'total': total,
            'pct': round(total / totalout * 100) if totalout else 0,
        })
    category_stats.sort(key=lambda c: c['total'], reverse=True)

    # Which category holds the most Rp / most count
    top_cat_rp = category_stats[0] if category_stats else None
    top_cat_count = max(category_stats, key=lambda c: c['count']) if category_stats else None

    # Most frequently inputted item (by number of entries)
    freq_row = db.session.query(
        Item.itemName,
        db.func.count(Item.itemID),
        db.func.coalesce(db.func.sum(Item.itemPrice), 0)
    ).group_by(Item.itemName).order_by(db.func.count(Item.itemID).desc()).first()
    top_item = None
    if freq_row:
        top_item = {'name': freq_row[0], 'count': freq_row[1], 'total': int(freq_row[2] or 0)}

    # Single largest expense
    hi = Item.query.order_by(Item.itemPrice.desc()).first()
    highest_item = None
    if hi:
        highest_item = {
            'name': hi.itemName,
            'price': hi.itemPrice,
            'category': CATEGORY_MAPPING.get(hi.category, hi.category),
        }

    portfolio = compute_portfolio()

    return render_template('dashboard.html',
                            title=title,
                            totalout=totalout,
                            item_count=item_count,
                            debt_count=debt_count,
                            total_debt=total_debt,
                            avg_item=avg_item,
                            category_stats=category_stats,
                            top_cat_rp=top_cat_rp,
                            top_cat_count=top_cat_count,
                            top_item=top_item,
                            highest_item=highest_item,
                            portfolio=portfolio,
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

# Edit item view
# Uses the SQLAlchemy ORM, so it emits an UPDATE against whatever database
# config.py selected: SQLite locally, MySQL in production. Same code, both envs.
@app.route('/item/edit/<int:itemID>', methods=['POST'])
@login_required
def edit_item(itemID):
    allowed_categories = ('needs', 'liabilities', 'saving', 'charity', 'fun', 'urgent')
    try:
        item = Item.query.get(itemID)
        if item:
            item.itemName = request.form['item'].strip()
            item.itemPrice = int(request.form['harga'])
            category = request.form['category']
            if category in allowed_categories:
                item.category = category
            db.session.commit()
            flash('Item was successfully updated')
    except Exception as e:
        db.session.rollback()
        flash('Failed to update item.', 'error')
    return redirect(url_for('reports'))

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


def compute_portfolio():
    """Compute per-holding valuation, totals, and allocation by type."""
    investments = Investment.query.order_by(Investment.invTimestamp.desc()).all()

    holdings = []
    total_invested = 0.0
    total_value = 0.0
    alloc = {}  # by type: current value

    for inv in investments:
        qty = inv.quantity or 0
        invested = qty * (inv.buyPrice or 0)
        value = qty * (inv.currentPrice or 0)
        gain = value - invested
        gain_pct = (gain / invested * 100) if invested else 0

        total_invested += invested
        total_value += value
        alloc[inv.invType] = alloc.get(inv.invType, 0) + value

        holdings.append({
            'id': inv.invID,
            'type': inv.invType,
            'type_name': INVESTMENT_TYPES.get(inv.invType, inv.invType),
            'asset': inv.asset,
            'quantity': qty,
            'buyPrice': inv.buyPrice or 0,
            'currentPrice': inv.currentPrice or 0,
            'invested': invested,
            'value': value,
            'gain': gain,
            'gain_pct': gain_pct,
        })

    total_gain = total_value - total_invested
    total_gain_pct = (total_gain / total_invested * 100) if total_invested else 0

    # Best / worst performer by gain %
    best = max(holdings, key=lambda h: h['gain_pct']) if holdings else None

    # Allocation (by type) for the donut chart
    allocation = [
        {
            'type': t,
            'name': INVESTMENT_TYPES.get(t, t),
            'color': INVESTMENT_COLORS.get(t, '#c9a227'),
            'value': v,
            'pct': round(v / total_value * 100) if total_value else 0,
        }
        for t, v in alloc.items()
    ]
    allocation.sort(key=lambda a: a['value'], reverse=True)

    return {
        'holdings': holdings,
        'total_invested': total_invested,
        'total_value': total_value,
        'total_gain': total_gain,
        'total_gain_pct': total_gain_pct,
        'best': best,
        'allocation': allocation,
    }


# Invest view (list + add)
@app.route('/invest', methods=['GET', 'POST'])
@login_required
def invest():
    title = "Invest"
    if request.method == 'POST':
        try:
            inv_type = request.form['invtype']
            asset = _investment_form_asset(inv_type, request.form)
            if inv_type in ALLOWED_INV_TYPES and asset:
                qs = Investment(
                    invType=inv_type,
                    asset=asset,
                    quantity=float(request.form['quantity']),
                    buyPrice=float(request.form['buyprice']),
                    currentPrice=float(request.form['currentprice']),
                    invTimestamp=helpers.gmt7now(datetime.utcnow()),
                )
                db.session.rollback()
                db.session.add(qs)
                db.session.commit()
                flash('Investment was successfully added')
            else:
                flash('Please complete the investment form.', 'error')
        except Exception:
            db.session.rollback()
            flash('Failed to add investment.', 'error')
        return redirect(url_for('invest'))

    portfolio = compute_portfolio()
    return render_template('invest.html',
                            title=title,
                            portfolio=portfolio,
                            gold_brands=GOLD_BRANDS,
                            crypto_coins=CRYPTO_COINS,
                            dt=dtCurrent)


# Edit investment (ORM UPDATE -> SQLite locally, MySQL in production)
@app.route('/invest/edit/<int:invID>', methods=['POST'])
@login_required
def edit_investment(invID):
    try:
        inv = Investment.query.get(invID)
        if inv:
            inv.asset = request.form['asset'].strip()
            inv.quantity = float(request.form['quantity'])
            inv.buyPrice = float(request.form['buyprice'])
            inv.currentPrice = float(request.form['currentprice'])
            db.session.commit()
            flash('Investment was successfully updated')
    except Exception:
        db.session.rollback()
        flash('Failed to update investment.', 'error')
    return redirect(url_for('invest'))


# Delete investment
@app.route('/invest/del/<int:invID>', methods=['GET', 'POST'])
@login_required
def delete_investment(invID):
    try:
        inv = Investment.query.get(invID)
        if inv:
            db.session.delete(inv)
            db.session.commit()
    except Exception:
        db.session.rollback()
    return redirect(url_for('invest'))

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

@app.route('/api/investment_chart_data')
@login_required
def investment_chart_data():
    portfolio = compute_portfolio()
    return jsonify({
        'labels': [a['name'] for a in portfolio['allocation']],
        'values': [round(a['value']) for a in portfolio['allocation']],
        'colors': [a['color'] for a in portfolio['allocation']],
    })

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

