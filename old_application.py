import os

from flask import Flask, render_template, request, session
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import requests
app = Flask(__name__)
# Goodreads importer
#res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "lte85d7clwNCXd6EcoKTZA", "isbns": "9781632168146"})
#clean = res.json()
#dictionary = clean["books"][0]


# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/", methods=["GET","POST"])
def index():
    if request.method=="GET":
        return render_template("index.html")
    else:
        username = request.form.get("username")
        password = request.form.get("password")
        activeuser = db.execute("SELECT id, username, first_name, last_name FROM users WHERE username = :username and password = :password",
                        {"username": username, "password": password}).fetchone()
        if not activeuser:
            return render_template("index.html", message="Incorrect username o"
                                                         "\r password, please try again", activeuser=activeuser)
        else:
            # activeuser.id += 1
            session["user_id"] = activeuser.id
            return render_template("search.html", activeuser=activeuser, success=True)

@app.route("/register", methods=["POST", "GET"])
def register():
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



@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method=="POST":
        if request.form.get("search") == "":
            return render_template("search.html", message = "You must provide a search string.")
        else:
            searchstr = request.form.get("search")
            # Concatenate search w/ wildcards
            search = "%" + searchstr + "%"
            # Select search results
            results = db.execute(
                "SELECT * FROM books WHERE isbn ILIKE :search OR author ILIKE :search OR title ILIKE :search",
                {"search": search}).fetchall()
            if not results:
                return render_template("search.html", message="No books matched your search")
            else:
                count=len(results)
                return render_template("search.html", results=results, count=count,search=searchstr)
    else:
        return render_template("index.html")

@app.route("/book/<string:isbn>", methods=["GET", "POST"])
def book(isbn):
    # Make sure user is logged in
    try:
        user_id = session["user_id"]
    except KeyError:
        return redirect(url_for("index"))

    # Get information from goodreads API
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "h6t5UWEmwHp7la5Ec3kRFw", "isbns": isbn})
    res=res.json()
    average_rating = res['books'][0]['average_rating']
    ratings_count = res['books'][0]['work_ratings_count']

    # Select book information
    info = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchall()

    # Select reviews for book
    reviews = db.execute("SELECT review, rating FROM reviews WHERE isbn = :isbn", {"isbn":isbn}).fetchall()

    if request.method == "GET":
        if not res or not info:
            return redirect(url_for("search"))

        return render_template("book.html", reviews=reviews, isbn=isbn, info=info, ratings_count=ratings_count, average_rating=average_rating)
    else:
        # Denies users review if they have already reviewed the book
        if db.execute("SELECT FROM reviews WHERE user_id = :user_id AND isbn = :isbn", {"user_id": user_id, "isbn":isbn }).fetchall():
            return render_template("book.html", reviews=reviews, isbn=isbn, info=info, ratings_count=ratings_count, average_rating=average_rating,
                error="You have already submitted a review for this book")
        else:

            rating = request.form.get("inlineRadioOptions")
            review = request.form.get("review")

            if not rating or not review:
                return render_template("book.html", reviews=reviews, isbn=isbn, info=info, ratings_count=ratings_count, average_rating=average_rating,
                    error="Please complete the form")

            db.execute("INSERT INTO reviews (rating, review, user_id, isbn) VALUES (:rating, :review, :user_id, :isbn)", {"rating": rating, "review": review, "user_id": user_id, "isbn": isbn})
            db.commit()

            reviews = db.execute("SELECT review, rating FROM reviews WHERE isbn = :isbn", {"isbn":isbn}).fetchall()
            return render_template("book.html", reviews=reviews, isbn=isbn, info=info, ratings_count=ratings_count, average_rating=average_rating)
@app.route("/api/<string:isbn>", methods=["GET", "POST"])
def api(isbn):
    return render_template("index.html")
