import os
from datetime import date
import time
from flask import Flask, render_template, request, session
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from dateutil.relativedelta import *
import datetime
import pandas as pd
import numpy as np


db = SQLAlchemy()

class User(db.Model):
    __tablename__="users"
    id=db.Column(db.Integer,primary_key=True)
    first_name=db.Column(db.String, nullable=False)
    last_name=db.Column(db.String, nullable=False)
    username=db.Column(db.String, nullable=False)
    email=db.Column(db.String, nullable=False)
    password=db.Column(db.String, nullable=False)
    life_expenses = db.relationship("Life_Budget", backref="user", lazy=False)
    trips = db.relationship("Trip", backref="user", lazy=True)

    def __init__(self, first_name="", last_name="", username="", email="", password=""):
        self.first_name=first_name
        self.last_name=last_name
        self.username=username
        self.email=email
        self.password=password

    def add_trip(self, name, description, origin, destination, departure_date, return_date, duration):
        t = Trip(name=name, description=description, origin=origin, destination=destination, duration=duration, departure_date=departure_date, return_date=return_date, userid=self.id)
        db.session.add(t)
        db.session.commit()

    def update_trip(self, trip_id, name, description, origin, destination, departure_date, return_date, duration):
        t = Trip.query.get(trip_id)
        t.name = name
        t.description = description
        t.origin = origin
        t.destination = destination
        t.duration = duration
        t.departure_date = departure_date
        t.return_date = return_date
        db.session.commit()
    def delete_trip(self, id):
        t = Trip.query.get(id)
        if t.expenses:
            for exp in t.expenses:
                db.session.delete(exp)
        db.session.delete(t)
        db.session.commit()

    def add_life_expense(self, name, frequency, date, end_date, amount, category, is_credit):
        e = Life_Budget(name=name, is_credit=is_credit,frequency=frequency, date=date, end_date=end_date, amount=amount, category=category,
                    user_id=self.id)
        db.session.add(e)
        db.session.commit()

    def delete_life_expense(self, id):
        exp = Life_Budget.query.get(id)
        db.session.delete(exp)
        db.session.commit()


class Trip(db.Model):
    __tablename__ = "trips"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    description=db.Column(db.String,nullable=False)
    origin = db.Column(db.String, nullable=True)
    destination = db.Column(db.String, nullable=False)
    departure_date=db.Column(db.String,nullable=False)
    return_date=db.Column(db.String, nullable=False)
    duration = db.Column(db.Integer ,nullable=False)
    cost = db.Column(db.Float, nullable = False, default=0.0)
    userid = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    expenses = db.relationship("Expense", backref="trip", lazy=True)

    def add_expense(self, name, frequency, date, end_date, amount, category ):
        e = Expense(name=name, frequency=frequency, date=date, end_date=end_date, amount=amount, category=category, trip_id=self.id)
        db.session.add(e)
        db.session.commit()

    def delete_expense(self, id):
        exp = Expense.query.get(id)
        db.session.delete(exp)
        db.session.commit()

    def update_cost(self):
        expenses = Expense.query.filter_by(trip_id=self.id).all()
        cost=0
        for e in expenses:
            if e.frequency=="One-time":
                cost= cost+e.amount
            if e.frequency=="Monthly":
                date=e.date
                while self.return_date>date>self.departure_date:
                    cost=cost+e.amount
                    date = date + relativedelta(months=+1)
            if e.frequency=="Yearly":
                date=e.date
                while self.return_date>date>self.departure_date:
                    cost=cost+e.amount
                    date = date + relativedelta(years=+1)
            if e.frequency == "Daily":
                delta=(e.end_date - e.date)
                cost=cost+(e.amount*(delta.days + 1))
            if e.frequency == "Weekly":
                delta=(e.end_date - e.date)
                cost=cost+(e.amount*(int(delta.days/7) + 1))
            if e.frequency == "Quarterly":
                delta=(e.end_date - e.date)
                cost=cost+(e.amount*(delta.months*3 + 1))



        self.cost=cost
        db.session.commit()

class Expense(db.Model):
    __tablename__ = "expenses"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    trip_id = db.Column(db.Integer, db.ForeignKey("trips.id"), nullable=False)
    frequency = db.Column(db.String, nullable=False)
    date = db.Column(db.String,nullable=False)
    end_date = db.Column(db.String, nullable=True)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String, nullable=False)

    def update_expense(self, name, frequency, category, amount, date, end_date):
        self.name = name
        self.frequency = frequency
        self.category = category
        self.amount = amount
        self.date = date
        self.end_date = end_date
        db.session.commit()


class Life_Budget(db.Model):
    __tablename__ = "life_expenses"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer,db.ForeignKey("users.id"),  nullable=False)
    name = db.Column(db.String, nullable=False)
    is_credit = db.Column(db.Boolean, nullable=False)
    frequency = db.Column(db.String, nullable=False)
    date = db.Column(db.String,nullable=False)
    end_date = db.Column(db.String, nullable=True)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String, nullable=False)

    def update_life_expense(self, name, frequency, category, amount, date, end_date, is_credit):
        self.name = name
        self.frequency = frequency
        self.category = category
        self.amount = amount
        self.date = date
        self.end_date = end_date
        self.is_credit = is_credit
        db.session.commit()


class Transaction():
    counter=1

    def __init__(self, e, transaction_type, t, date, is_credit):
        Transaction.counter+=1
        self.name=e.name
        self.category=e.category
        self.frequency=e.frequency
        if is_credit:
            self.amount=e.amount
        else:
            self.amount=-e.amount
        self.date=date
        self.transaction_type=transaction_type
        self.is_credit=is_credit
        self.month=self.date.strftime('%B')
        self.year=self.date.year
        if t:
            self.trip_id=e.trip
            self.trip_name=t.name
        else:
            self.trip_id=None
            self.trip_name=None


class Quote(db.Model):
    __tablename__ = "quotes"
    id = db.Column(db.Integer, primary_key=True)
    quote = db.Column(db.String, nullable=False)
    author = db.Column(db.String, nullable=True)
    source =db.Column(db.String, nullable=True)
    theme = db.Column(db.String, nullable=False)

    def __init__(self, quote="", author="", source="", theme=""):
        self.quote=quote
        self.author=author
        self.source=source
        self.theme=theme

    def update_quote(self, quote, author, source, theme):
        self.quote=quote
        self.author=author
        self.source=source
        self.theme=theme
        db.session.commit()

    def delete_quote(self, quote_id):
        quote = Quote.query.get(quote_id)
        db.session.delete(quote)
        db.session.commit()

class Country(db.Model):
    __tablename__= "countries"
    id=db.Column(db.Integer, primary_key=True)
    country= db.Column(db.Integer, nullable=False)
    currency_name=db.Column(db.Integer, nullable=False)
    currency_code=db.Column(db.Integer, nullable=True)
    currency_code_num=db.Column(db.Integer, nullable=True  )

