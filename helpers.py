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
