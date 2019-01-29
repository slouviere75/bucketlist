
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()

class Country(db.Model):
    __tablename__ = "countries"
    id = db.Column(db.Integer, primary_key=True)
    country = db.Column(db.String, nullable=False)
    currency = db.Column(db.String, nullable=True)
    code =db.Column(db.String, nullable=True)
    code_num = db.Column(db.String, nullable=True)

