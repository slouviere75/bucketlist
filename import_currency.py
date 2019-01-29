import csv
import os

from flask import Flask, render_template, request
from models import *

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

def main():
    f = open("codes.csv")
    reader = csv.reader(f)
    for country, currency, code, code_no in reader:
        country = country.replace('ÿ ','')
        country = Country(country=country, currency_name=currency, currency_code=code, currency_code_num=code_no)
        db.session.add(country)
        print(f"Added country {country}")
    db.session.commit()

