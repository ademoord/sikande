import datetime, pytz
from active_alchemy import ActiveAlchemy

# DATABASE CONNECTION INIT
# using ActiveAlchemy free wrapper
db = ActiveAlchemy("mysql+pymysql://sikande:financial2022@sikande.mysql.pythonanywhere-services.com/sikande$default")

# # START OF CUSTOM METHODS
# # the timeConverter method
# def gmt7now(dt_utc):
#     dt_utc = datetime.datetime.utcnow()   #utcnow class method
#     dt_rep = dt_utc.replace(tzinfo=pytz.UTC) #replace method
#     dt_gmt7 = dt_rep.astimezone(pytz.timezone("Asia/Jakarta")) #astimezone method
#     return dt_gmt7

# # END OF CUSTOM METHODS
# # --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# # START OF MODELS CREATION
# # Item models
# class Item(db.Model):
#     itemID = db.Column(db.Integer, primary_key=True)
#     itemName = db.Column(db.String(64), index=True, unique=True)
#     itemPrice = db.Column(db.Integer, index=True)
#     itemTimestamp = db.Column(db.DateTime, index=True, default=gmt7now(datetime.datetime.utcnow))

#     def __repr__(self):
#         return '<Item {}>'.format(self.itemName)


# # END OF MODELS CREATION
# # --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------