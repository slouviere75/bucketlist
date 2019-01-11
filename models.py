import os

from flask import Flask, render_template, request, session
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__="users"
    id=db.Column(db.Integer,primary_key=True)
    first_name=db.Column(db.String, nullable=False)
    last_name=db.Column(db.String, nullable=False)
    username=db.Column(db.String, nullable=False)
    email=db.Column(db.String, nullable=False)
    password=db.Column(db.String, nullable=False)

    def __init__(self, first_name="", last_name="", username="", email="", password=""):
        self.first_name=first_name
        self.last_name=last_name
        self.username=username
        self.email=email
        self.password=password

    def add_trip(self, name, description, origin, destination, departure_date, duration):
        t = Trip(name=name, description=description, origin=origin, destination=destination, duration=duration, departure_date=departure_date, userid=self.id)
        db.session.add(t)
        db.session.commit()

    def delete_trip(self, id):
        t = Trip.query.get(id)
        if t.expenses:
            for exp in t.expenses:
                db.session.delete(exp)
        db.session.delete(t)
        db.session.commit()


class Trip(db.Model):
    __tablename__ = "trips"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    description=db.Column(db.String,nullable=False)
    origin = db.Column(db.String, nullable=True)
    destination = db.Column(db.String, nullable=False)
    departure_date=db.Column(db.String,nullable=False)
    duration = db.Column(db.Integer ,nullable=False)
    cost = db.Column(db.Float, nullable = False, default=0.0)
    userid = db.Column(db.Integer, nullable=False)
    expenses = db.relationship("Expense", backref="trip", lazy=True)

    def add_expense(self, name, frequency, date, amount, category ):
        e = Expense(name=name, frequency=frequency, date=date, amount=amount, category=category, trip_id=self.id)
        db.session.add(e)
        db.session.commit()

class Expense(db.Model):
    __tablename__ = "expenses"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    trip_id = db.Column(db.Integer, db.ForeignKey("trips.id"), nullable=False)
    frequency = db.Column(db.String, nullable=False)
    date = db.Column(db.String,nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String, nullable=False)

    # def __init__(self, id=0, name="", trip_id=0, frequency="", date="", amount="0.0", category=""):
    #     self.id=id
    #     self.name=name
    #     self.trip_id=trip_id
    #     self.frequency=frequency
    #     self.date=date
    #     self.amount=amount
    #     self.category=category