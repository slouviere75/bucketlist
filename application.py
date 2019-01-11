import os
from flask_session import Session
from flask import Flask, render_template, jsonify, request
from models import *

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

@app.route("/", methods=["GET","POST"])
def index():
    if request.method == "GET":
        return render_template("index.html", activeuser=None)
    else:
        username = request.form.get("username")
        password = request.form.get("password")
        activeuser = User.query.filter_by(username=username, password=password).first()
        if activeuser==None:
            activeuser=User()
            return render_template("index.html", message="Incorrect username or password, please try again", activeuser=activeuser)
        else:
            session["user_id"] = activeuser.id

            trips = Trip.query.filter_by(userid=activeuser.id).all()
            return render_template("trips.html", activeuser=activeuser, success=True, trips=trips)

@app.route("/logout", methods=["GET"])
def logout():
    activeuser=None
    session["user_id"]=""
    return render_template("index.html", activeuser=activeuser)


@app.route("/register", methods=["POST", "GET"])
def register_def():
    if request.method == "GET":
        return render_template("register.html")
    elif request.method == "POST":
        username = request.form.get("username")
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        email = request.form.get("email")
        password = request.form.get("password")
        if db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).rowcount != 0:
            duplicate = True
            success = False
            message = "That username is already in use. Try again."
            return render_template("register.html", message=message, duplicate=duplicate, success=success,first_name=first_name, last_name=last_name, email=email)
        else:
            success = True
            message = "User added successfully.  login."
            db.execute(
                "INSERT INTO users (first_name, last_name, username, email, password) VALUES (:first_name, :last_name, :username, :email, :password)",
                {"first_name": first_name, "last_name": last_name, "username": username, "email": email,
                 "password": password})
            db.commit()
        return render_template("index.html", first_name=first_name, last_name=last_name, username=username,
                                   email=email, password=password, message=message, success=success)


@app.route('/trips/', methods=["GET", "POST"])
def trips():

    if request.method=="GET":
        activeuser=User()
        return render_template("index.html", message = "Please login to access trip data.", activeuser=activeuser)


    else:
        name = request.form.get("name")
        description = request.form.get("description")
        origin = request.form.get("origin")
        destination = request.form.get("destination")
        departure_date=request.form.get("departure_date")
        duration = request.form.get("duration")
        activeuser=User.query.get(session["user_id"])
        activeuser.add_trip(name=name, description=description, origin=origin, destination=destination, duration=duration, departure_date=departure_date)
        trips = Trip.query.filter_by(userid=activeuser.id).all()
        return render_template("trips.html", activeuser=activeuser, success=True, trips=trips)


@app.route("/delete_trip/<int:trip_id>", methods=["GET", "POST"])
def delete_trip( trip_id ):
    if session["user_id"]=="":
        return render_template("index.html", message = "Please login first")
    else:
        trip = Trip.query.get(trip_id)
        activeuser = User.query.get(session["user_id"])
        if trip.userid==activeuser.id:
            message = "Trip deleted successfully."
            activeuser.delete_trip(id=trip_id)
            trips = Trip.query.filter_by(userid=activeuser.id).all()
        else:
            message="Trip not deleted."
        return render_template("trips.html", trips=trips, message=message, activeuser=activeuser)




@app.route("/add_trip", methods=["GET", "POST"])
def add_trip():
    if session["user_id"]=="":
        return render_template("index.html", message = "Please login to access trip data.")
    if request.method == "GET":
        return render_template("add_trip.html", activeuser=session["user_id"])
    elif request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description")
        origin = request.form.get("origin")
        destination = request.form.get("destination")
        departure_date = request.form.get("departure_date")
        duration = request.form.get("duration")
        message = "Trip added successfully."
        activeuser.add_trip(name=name, description=description, origin=origin, destination=destination, duration=duration, departure_date=departure_date)
        trips = Trip.query.filter_by(userid=activeuser.id).all()
        return render_template("trips.html", trips=trips,message=message, activeuser=activeuser)



@app.route("/add_expense/<int:trip_id>", methods=["GET", "POST"])
def add_expense(trip_id):
    if session["user_id"]=="":
        return render_template("index.html", message = "Please login to add an expense.")
    if request.method == "GET":
        trip = Trip.query.get(trip_id)
        return render_template("add_expense.html", trip=trip, activeuser=session["user_id"])
    elif request.method == "POST":
        name = request.form.get("name")
        category = request.form.get("category")
        frequency = request.form.get("frequency")
        amount = request.form.get("amount")
        date = request.form.get("date")
        message = "Expense added successfully."
        trip = Trip.query.get(trip_id)
        activeuser=User.query.get(session["user_id"])
        trip.add_expense(name=name, category=category, frequency=frequency, amount=amount, date=date)
        trips = Trip.query.filter_by(userid=activeuser.id).all()
        return render_template("trips.html", trips=trips,message=message, activeuser=activeuser)

