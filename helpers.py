from sqlalchemy import func
import datetime, pytz
from config import db
from functools import reduce
from operator import add

# START OF CUSTOM METHODS
# the time converter method
def gmt7now(dt_utc):
    dt_utc = datetime.datetime.utcnow()                                 # utcnow class method
    dt_rep = dt_utc.replace(tzinfo=pytz.UTC)                            # replace method
    dt_gmt7 = dt_rep.astimezone(pytz.timezone("Asia/Jakarta"))          # astimezone method
    return dt_gmt7

def dbsumint(qr_int):
    db.session.rollback()
    total = db.session.query(func.sum(qr_int)).scalar()
    return total if total is not None else 0