import os
from flask_session import Session
from flask import Flask, render_template, jsonify, request, redirect
from models import *
import random
import pandas as pd


# # Check for environment variable
# if not os.getenv("DATABASE_URL"):
#     raise RuntimeError("DATABASE_URL is not set")

#Get list of files in image directory that start with "carousel" for inclusion in Homepage carousel
#Note that the first file needs to be separated from this list to iterate properly in Jinja, hence
#the carousel_first variable

carousel_path="./static/images"


# Configure session to use filesystem
app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
Session(app)

app.config["SQLALCHEMY_DATABASE_URI"] = "postgres://egldlzkbdfpagt:aaf63585b3a3914f93a03394f80efa4a472794f3d8cd478b2bd86399e69c3912@ec2-54-235-178-189.compute-1.amazonaws.com:5432/d96cp2dv3o4pv0"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# app.run(host= '0.0.0.0')
db.init_app(app)

exp_freq=["One-time", "Daily", "Weekly", "Monthly", "Quarterly", "Yearly"]
categories=["Transportation", "Food", "Excursions", "Lodging", "Miscellaneous"]
life_categories=["Bills", "Education", "Food","Miscellaneous", "Storage"]

categories.sort()
report_types=["Transaction Register"]
report_types.sort()
today = date.today()

@app.route("/")
def index():
    carousel_first, carousel_images = get_carousel_images(carousel_path)
    quotes=Quote.query.filter_by().all()
    random.shuffle(quotes)
    if not ('user_id' in session):
        return render_template("index.html", activeuser=None, carousel_first=carousel_first, carousel_images=carousel_images, quotes=quotes)
    activeuser=User.query.get(session["user_id"])

    return render_template("index.html", activeuser=activeuser, message=None, carousel_first=carousel_first, carousel_images=carousel_images, quotes=quotes)

@app.route("/bucketlist", methods=["GET","POST"])
def bucketlist():

    if request.method == "GET":
        if not ('user_id' in session):
            return render_template("bucketlist.html", activeuser=None, message=None)
        else:
            activeuser=User.query.get(session["user_id"])
            activeuser.trips.sort(key=lambda x: x.departure_date, reverse=False)
            for t in activeuser.trips:
                t.expenses.sort(key=lambda x: x.date, reverse=False)
            return render_template("trips.html",activeuser=activeuser, success=True, message=None )
    else:
        username = request.form.get("username")
        password = request.form.get("password")
        activeuser = User.query.filter_by(username=username, password=password).first()
        if activeuser==None:
            return render_template("bucketlist.html", message="Incorrect username or password, please try again", activeuser=None)
        session['user_id'] = activeuser.id
        activeuser.trips.sort(key=lambda x: x.departure_date, reverse=False)
        for t in activeuser.trips:
            t.expenses.sort(key=lambda x: x.date, reverse=False)
        return render_template("trips.html", activeuser=activeuser, success=True, message="You have logged in successfully.")



@app.route("/logout", methods=["GET"])
def logout():
    session.pop('user_id', None)
    return render_template("bucketlist.html", activeuser=None, message="You have been logged out.")


@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "GET":
        return render_template("register.html", activeuser=None)
    elif request.method == "POST":
        username = request.form.get("username")
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        email = request.form.get("email")
        password = request.form.get("password")
        if User.query.filter_by(username=username).all():
            duplicate = True
            success = False
            message = "That username is already in use. Try again."
            return render_template("register.html", activeuser=None, message=message, duplicate=duplicate, success=success,first_name=first_name, last_name=last_name, email=email)
        else:
            success = True
            message = "User added successfully.  login."
            u = User(first_name=first_name, last_name=last_name, email=email,username=username, password=password)
            db.session.add(u)
            db.session.commit()
        return render_template("bucketlist.html", first_name=first_name, last_name=last_name, username=username,
                                   email=email, password=password, message=message, success=success, activeuser=u)


@app.route('/trips/<string:trip_id>', methods=["GET", "POST"])
def trips(trip_id):
        if not ('user_id' in session):
            return render_template("bucketlist.html", message="You are not currently logged in.", activeuser=None)
        if request.method=="GET":
            activeuser=User()
            return render_template("bucketlist.html", message = "Please login to access trip data.", activeuser=activeuser)
        else:
            name = request.form.get("name")
            description = request.form.get("description")
            origin = request.form.get("origin")
            destination = request.form.get("destination")
            departure_date=request.form.get("departure_date")
            return_date=request.form.get("return_date")
            activeuser=User.query.get(session["user_id"])
            d = (datetime.datetime.strptime(return_date, "%Y-%m-%d") - datetime.datetime.strptime(departure_date, "%Y-%m-%d"))
            duration = d.days
            if trip_id == "-1":
                activeuser.add_trip(name=name, description=description, origin=origin, destination=destination, duration=duration, departure_date=departure_date, return_date=return_date)
            else:
                activeuser.update_trip(trip_id=trip_id, name=name, description=description, origin=origin, destination=destination, duration=duration, departure_date=departure_date, return_date=return_date)
            activeuser.trips.sort(key=lambda x: x.departure_date, reverse=False)
            for t in activeuser.trips:
                t.expenses.sort(key=lambda x: x.date, reverse=False)
            return render_template("trips.html", activeuser=activeuser, success=True)


@app.route("/delete_trip/<int:trip_id>", methods=["GET"])
def delete_trip( trip_id ):
    if not ('user_id' in session):
        return render_template("bucketlist.html", message="You are not currently logged in.", activeuser=None)
    else:
        trip = Trip.query.get(trip_id)
        activeuser = User.query.get(session["user_id"])
        if trip.userid==activeuser.id:
            message = "Trip deleted successfully."
            activeuser.delete_trip(id=trip_id)
            activeuser.trips.sort(key=lambda x: x.departure_date, reverse=False)
            for t in activeuser.trips:
                t.expenses.sort(key=lambda x: x.date, reverse=False)
        else:
            message="Trip not deleted."
        return render_template("trips.html", message=message, activeuser=activeuser)




@app.route("/add_trip", methods=["GET", "POST"])
def add_trip():
    if not ('user_id' in session):
        return render_template("bucketlist.html", message="You are not currently logged in.", activeuser=None)
    if request.method == "GET":
        activeuser = User.query.get(session["user_id"])
        t = Trip(name="", description="", origin="", destination="", duration="", departure_date=today)
        t.id=-1
        return render_template("add_trip.html", activeuser=activeuser, trip=t)


@app.route("/edit_trip/<int:trip_id>", methods=["GET"])
def edit_trip(trip_id):
    if not ('user_id' in session):
        return render_template("bucketlist.html", message = "Please login to access trip data.", activeuser=None)
    activeuser = User.query.get(session["user_id"])
    t = Trip.query.get(trip_id)
    return render_template("add_trip.html", activeuser=activeuser, trip=t)


@app.route("/add_expense/<int:trip_id>", methods=["GET", "POST"])
def add_expense(trip_id):
    if not ('user_id' in session):
        return render_template("bucketlist.html", message = "Please login to add an expense.")
    if request.method == "GET":
        trip = Trip.query.get(trip_id)
        e = Expense(name="", frequency="", amount="", date=trip.departure_date, end_date=trip.return_date, category="")
        return render_template("add_expense.html", e=e, trip=trip, activeuser=session["user_id"], exp_freq=exp_freq, today=today, categories = categories)
    elif request.method == "POST":
        name = request.form.get("name")
        category = request.form.get("category")
        frequency = request.form.get("frequency")
        amount = request.form.get("amount")
        date = request.form.get("date")
        end_date = request.form.get("end_date")
        if frequency=="One-time":
            end_date=None
        message = "Expense added successfully."
        trip = Trip.query.get(trip_id)
        activeuser=User.query.get(session["user_id"])

        trip.add_expense(name=name, category=category, frequency=frequency, amount=amount, date=date, end_date=end_date)
        trip.update_cost()
        activeuser.trips.sort(key=lambda x: x.departure_date, reverse=False)
        for t in activeuser.trips:
            t.expenses.sort(key=lambda x: x.date, reverse=False)
        return render_template("trips.html", message=message, activeuser=activeuser)

@app.route("/delete_expense/<int:id>", methods=["GET"])
def delete_expense( id ):
    if not ('user_id' in session):
        return render_template("bucketlist.html", message = "Please login first")
    else:
        exp = Expense.query.get(id)
        activeuser = User.query.get(session["user_id"])
        trip = exp.trip
        if trip.userid==activeuser.id:
            message = "Expense deleted successfully."
            trip.delete_expense(id=id)
            trip.update_cost()
            trips = Trip.query.filter_by(userid=activeuser.id).order_by(Trip.departure_date).all()
        else:
            message="Trip not deleted."
        activeuser.trips.sort(key=lambda x: x.departure_date, reverse=False)
        for t in activeuser.trips:
            t.expenses.sort(key=lambda x: x.date, reverse=False)
        return render_template("trips.html", trips=trips, message=message, activeuser=activeuser)

@app.route("/edit_expense/<int:expense_id>", methods=["GET", "POST"])
def edit_expense(expense_id):
        if not ('user_id' in session):
            return render_template("bucketlist.html", message = "Please login to access trip data.", activeuser=None)
        activeuser = User.query.get(session["user_id"])
        e = Expense.query.get(expense_id)
        trip = e.trip
        if request.method == "GET":
            return render_template("edit_expense.html", activeuser=activeuser, e=e, trip=trip, exp_freq=exp_freq, today=today, categories = categories)
        elif request.method == "POST":
            name = request.form.get("name")
            frequency = request.form.get("frequency")
            date = request.form.get("date")
            end_date = request.form.get("end_date")
            if frequency=="One-time":
                end_date=None
            amount = request.form.get("amount")
            category = request.form.get("category")
            e.update_expense(name=name, frequency=frequency, date=date, end_date=end_date, amount=amount, category=category)
            trip.update_cost()
            trips=Trip.query.filter_by(userid=activeuser.id).order_by(Trip.departure_date).all()
            message = "Expense updated successfully."
            activeuser.trips.sort(key=lambda x: x.departure_date, reverse=False)
            for t in activeuser.trips:
                t.expenses.sort(key=lambda x: x.date, reverse=False)
            return render_template("trips.html", trips=trips, activeuser=activeuser, message=message, trip_id=trip.id)

@app.route("/life_budget", methods=["GET"])
def life_budget():
    if not ('user_id' in session):
        return render_template("bucketlist.html", message = "Please login to access budget data.", activeuser=None)
    activeuser = User.query.get(session["user_id"])
    activeuser.life_expenses.sort(key=lambda x: x.date, reverse=False)

    return render_template("life_budget.html", message = "Here's your life budget for all things unrelated to travel.", activeuser=activeuser )

@app.route("/add_life_expense/<int:user_id>", methods=["GET", "POST"])
def add_life_expense(user_id):
    if not ('user_id' in session):
        return render_template("bucketlist.html", message = "Please login to access budget data.", activeuser=None)
    activeuser=User.query.get(session["user_id"])
    if request.method=="GET":
        e = Life_Budget(name="", frequency="", amount="", date="", end_date="", category="")
        return render_template("add_life_expense.html", message="", activeuser=activeuser, e=e, today = today, categories=life_categories, exp_freq=exp_freq)
    elif request.method == "POST":
        name = request.form.get("name")
        options=request.form.get("options")
        category = request.form.get("category")
        frequency = request.form.get("frequency")
        amount = request.form.get("amount")
        date = request.form.get("date")
        end_date = request.form.get("end_date")
        if frequency=="One-time":
            end_date = None
        if end_date=="":end_date=None
        if options=="expense":
            is_credit=False
        else: is_credit=True
        message = "Life Expense added successfully."
        activeuser = User.query.get(session["user_id"])
        activeuser.add_life_expense(name=name, category=category, frequency=frequency, amount=amount, date=date, end_date=end_date, is_credit=is_credit)
        activeuser.life_expenses.sort(key=lambda x: x.date, reverse=False)
        return render_template("life_budget.html",  message=message, activeuser=activeuser, exp_freq=exp_freq, categories=categories)


@app.route("/edit_life_expense/<int:expense_id>", methods=["GET", "POST"])
def edit_life_expense(expense_id):
        if not ('user_id' in session):
            return render_template("bucketlist.html", message = "Please login to access trip data.", activeuser=None )
        activeuser = User.query.get(session["user_id"])
        e = Life_Budget.query.get(expense_id)
        if request.method == "GET":
            return render_template("edit_life_expense.html", activeuser=activeuser, e=e, exp_freq=exp_freq, today=today, categories = categories)
        elif request.method == "POST":
            name = request.form.get("name")
            options=request.form.get("options")
            frequency = request.form.get("frequency")
            date = request.form.get("date")
            end_date = request.form.get("end_date")
            if frequency=="One-time":
                end_date=None
            amount = request.form.get("amount")
            category = request.form.get("category")
            if end_date == "": end_date = None
            if options=="expense":
                is_credit=False
            else:
                is_credit=True
            e.update_life_expense(name=name, frequency=frequency, date=date, end_date=end_date, amount=amount, category=category, is_credit=is_credit)
            message = "Expense updated successfully."
            activeuser.life_expenses.sort(key=lambda x: x.date, reverse=False)
            return render_template("life_budget.html", activeuser=activeuser, message=message)


@app.route("/delete_life_expense/<int:id>", methods=["GET"])
def delete_life_expense( id ):
    if not ('user_id' in session):
        return render_template("bucketlist.html", message = "Please login first", activeuser=None)
    e = Life_Budget.query.get(id)
    activeuser=User.query.get(session["user_id"])
    if e:
        activeuser = User.query.get(session["user_id"])
        if e.user_id==activeuser.id:
            message = "Life Expense deleted successfully."
            activeuser.delete_life_expense(id=id)
        else:
            message="Life Expense not deleted."
        activeuser.life_expenses.sort(key=lambda x: x.date, reverse=False)
        return render_template("life_budget.html", message=message, activeuser=activeuser)
    return render_template("life_budget.html", message = "This entry does not exist.", activeuser=activeuser)


@app.route("/quotes/", methods=["GET"])
def quotes():
    if not ('user_id' in session):
        return render_template("bucketlist.html", message = "Please login first.", activeuser=None)
    quotes=Quote.query.filter_by().all()
    activeuser=User.query.get(session["user_id"])
    return render_template("quotes.html", quotes=quotes, activeuser=activeuser)

@app.route("/quotes/add_quote", methods=["GET","POST"])
def add_quote():
    if not ('user_id' in session):
        return render_template("bucketlist.html", message = "Please login first.", activeuser=None)
    activeuser=User.query.get(session["user_id"])
    if request.method=="GET":
        return render_template("add_quote.html", message=None, activeuser=activeuser)
    elif request.method=="POST":
        quote=request.form.get("quote")
        author=request.form.get("author")
        source=request.form.get("source")
        theme=request.form.get("theme")
        q=Quote(quote=quote, author=author, source=source, theme=theme)
        db.session.add(q)
        db.session.commit()
        quotes=Quote.query.filter_by().all()
        return render_template("quotes.html", quotes=quotes, activeuser=activeuser)


@app.route("/quotes/edit_quote/<int:quote_id>", methods=["GET","POST"])
def edit_quote(quote_id):
    if not ('user_id' in session):
        return render_template("bucketlist.html", message = "Please login first.", activeuser=None)
    activeuser=User.query.get(session["user_id"])
    quote=Quote.query.get(quote_id)
    if request.method=="GET":
        return render_template("edit_quote.html", message=None, activeuser=activeuser, quote=quote)
    elif request.method=="POST":
        quote1=request.form.get("quote")
        author=request.form.get("author")
        source=request.form.get("source")
        theme=request.form.get("theme")
        quote.update_quote(quote=quote1, author=author, source=source, theme=theme)

        db.session.commit()
        quotes=Quote.query.filter_by().all()
        return render_template("quotes.html", quotes=quotes, activeuser=activeuser)


@app.route("/delete_quote/<int:quote_id>", methods=["GET"])
def delete_quote( quote_id ):
    if not ('user_id' in session):
        return render_template("bucketlist.html", message = "Please login first", activeuser=None)
    q= Quote.query.get(quote_id)
    activeuser=User.query.get(session["user_id"])
    if q:
        q.delete_quote(quote_id=quote_id)
    else:
        message="Quote not deleted."
        return render_template("quotes.html", message=message, activeuser=activeuser)
    quotes=Quote.query.filter_by().all()
    return render_template("quotes.html", message = "This entry does not exist.", activeuser=activeuser, quotes=quotes)


@app.route("/convert", methods=["POST"])
def convert():
    if not ('user_id' in session):
        return render_template("bucketlist.html", message="Please login first", activeuser=None)
    activeuser = User.query.get(session["user_id"])
    if request.method == "GET":
        return render_template("convert.html", activeuser=activeuser, message=None)
    elif request.method == "POST":
        # Query for currency exchange rate
        currency = request.form.get("currency")
        res = requests.get("https://api.fixer.io/latest", params={
            "base": "USD", "symbols": currency})

        # Make sure request succeeded
        if res.status_code != 200:
            return jsonify({"success": False})

        # Make sure currency is in response
        data = res.json()
        if currency not in data["rates"]:
            return jsonify({"success": False})

        return jsonify({"success": True, "rate": data["rates"][currency]})



@app.route("/our_photos/", methods=["GET", "POST"])
def our_photos():
    if not ('user_id' in session):
        return render_template("our_photos.html", message = None, activeuser=None)
    activeuser = User.query.get(session["user_id"])
    if request.method=="GET":
        return render_template("our_photos.html", activeuser=activeuser, message=None, report_types=report_types, start="2019-01-01", end="2019-12-31")



@app.route("/reports/", methods=["GET", "POST"])
def reports():
    if not ('user_id' in session):
        return render_template("bucketlist.html", message = "Please login first", activeuser=None)
    activeuser = User.query.get(session["user_id"])
    if request.method=="GET":
        return render_template("report_builder.html", activeuser=activeuser, message=None, report_types=report_types, start="2019-01-01", end="2019-12-31")
    elif request.method=="POST":
        start_date_str = request.form.get("start_date")
        end_date_str = request.form.get("end_date")
        report_start_date=datetime.datetime.strptime(start_date_str, "%Y-%m-%d").date()
        report_end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d").date()
        report_type = request.form.get("report_type")
        transactions=[]
        transaction_type="Trips"
        for trip in activeuser.trips:

            trip_cost=0
            for expense in trip.expenses:
                if expense.end_date and expense.end_date < report_end_date:
                    end_date = expense.end_date
                else:
                    end_date = report_end_date
                if expense.frequency=="One-time":
                    date=expense.date
                    t=Transaction(e=expense, transaction_type=transaction_type, t=trip, date=date, is_credit=False)

                    transactions.append(t)
                    trip_cost+=expense.amount
                elif expense.frequency=="Daily":
                    date=expense.date
                    while expense.date<=date<=end_date:
                        t=Transaction(e=expense, transaction_type=transaction_type, t=trip, date=date, is_credit=False)
                        transactions.append(t)
                        date = date + relativedelta(days=+1)
                        trip_cost += expense.amount
                elif expense.frequency=="Weekly":
                    date=expense.date
                    while expense.date<=date<=end_date:
                        t=Transaction(e=expense, transaction_type=transaction_type, t=trip, date=date, is_credit=False)
                        transactions.append(t)
                        date = date + relativedelta(weeks=+1)
                        trip_cost += expense.amount
                elif expense.frequency=="Monthly":
                    date=expense.date
                    while expense.date<=date<=end_date:
                        t=Transaction(e=expense, transaction_type=transaction_type, t=trip, date=date, is_credit=False)
                        transactions.append(t)
                        date=date+relativedelta(months=+1)
                        trip_cost += expense.amount
                elif expense.frequency=="Quarterly":
                    date=expense.date
                    while expense.date<=date<=end_date:
                        t=Transaction(e=expense, transaction_type=transaction_type, t=trip, date=date, is_credit=False)
                        transactions.append(t)
                        date=date+relativedelta(months=+3)
                        trip_cost += expense.amount
                elif expense.frequency=="Yearly":
                    date=expense.date
                    while expense.date<=date<=end_date:
                        t=Transaction(e=expense, transaction_type=transaction_type, t=trip, date=date, is_credit=False)
                        transactions.append(t)
                        date=date+relativedelta(years=+1)
                        trip_cost += expense.amount
            trip.cost=trip_cost
            db.session.commit()
        transaction_type="Life Expense"
        for expense in activeuser.life_expenses:

            if expense.end_date and expense.end_date<report_end_date:end_date=expense.end_date
            else: end_date=report_end_date
            if expense.frequency=="One-time":
                t=Transaction(e=expense, transaction_type=transaction_type, t=None, is_credit=expense.is_credit)
                transactions.append(t)
            elif expense.frequency=="Daily":
                date=expense.date
                while expense.date<=date<=end_date:
                    t=Transaction(e=expense, transaction_type=transaction_type, t=None, date=date, is_credit=expense.is_credit)
                    transactions.append(t)
                    date = date + relativedelta(days=+1)
            elif expense.frequency=="Weekly":
                date=expense.date
                while expense.date<=date<=end_date:
                    t=Transaction(e=expense, transaction_type=transaction_type, t=None, date=date, is_credit=expense.is_credit)
                    transactions.append(t)
                    date = date + relativedelta(weeks=+1)
            elif expense.frequency=="Monthly":
                date=expense.date
                while expense.date<=date<=end_date:
                    t=Transaction(e=expense, transaction_type=transaction_type, t=None, date=date, is_credit=expense.is_credit)
                    transactions.append(t)
                    date=date+relativedelta(months=+1)
            elif expense.frequency=="Quarterly":
                date=expense.date
                while expense.date<=date<=end_date:
                    t=Transaction(e=expense, transaction_type=transaction_type, t=None, date=date, is_credit=expense.is_credit)
                    transactions.append(t)
                    date=date+relativedelta(months=+3)
            elif expense.frequency=="Yearly":
                date=expense.date
                while expense.date<=date<=end_date:
                    t=Transaction(e=expense, transaction_type=transaction_type, t=None, date=date, is_credit=expense.is_credit)
                    transactions.append(t)
                    date=date+relativedelta(years=+1)
        t = transactions[0]
        variables = [attr for attr in dir(t) if not callable(getattr(t, attr)) and not attr.startswith("__")]
        transactions.sort(key=lambda x: x.date)
        my_df=build_transaction_df(transactions, variables)
        # grouped_df=my_df.groupby(['name',pd.Grouper(key='date', freq='M')])['amount'].sum()
        my_df["date"] = pd.to_datetime(my_df['date'])
        groupie_month = my_df.groupby([pd.Grouper(key='date', freq='M')])['amount'].sum()

        groupie_cat = my_df.groupby([pd.Grouper(key='category')])['amount'].sum()
        # my_df = my_df.groupby([pd.Grouper(key='date', freq='M')])['amount'].sum()
        # my_df = my_df.reset_index()
        grouped_df=groupie_month.reset_index()
        grouped_df2=groupie_cat.reset_index()
        grouped_df["date"]=pd.to_datetime(grouped_df["date"])
        grouped_df["date"]=grouped_df["date"].dt.strftime('%B %Y')
        table = pd.pivot_table(my_df, values='amount', index=['date'], columns = ['amount'], aggfunc = np.sum)
        table= table.reset_index()


        total_cost=sum(transaction.amount for transaction in transactions)
        return render_template("report1.html", transactions=transactions, activeuser=activeuser, total_cost=total_cost, my_df=my_df.to_html(classes='data'), grouped_df=grouped_df.to_html(classes='data'), grouped_df2=grouped_df2.to_html(classes='data'), table=table.to_html(classes='data'))


if __name__=="__main__":
    app.run(host='0.0.0.0', port=int(80))

def get_carousel_images(carousel_path):
    carousel_images = os.listdir(carousel_path)
    carousel_images = [c for c in carousel_images if 'carousel' in c]
    carousel_first = carousel_images[0]
    carousel_images.pop(0)
    return carousel_first, carousel_images

def build_transaction_df(transactions, variables):
    dict_conv={"name":[t.name for t in transactions], "category":[t.category for t in transactions], "frequency":[t.frequency for t in transactions], "amount":[t.amount for t in transactions], "date":[t.date for t in transactions], "trip_id":[t.trip_id for t in transactions], "trip_name":[t.trip_name for t in transactions], "transaction_type":[t.transaction_type for t in transactions]}
    df_t = pd.DataFrame(dict_conv,columns=variables)
    # df_t = df_t[["name", "category", "frequency", "amount", "date", "transaction_type"]]

    # for t in transactions:
    #     transaction={"name":t.name, "category":t.category, "frequency":t.frequency, "amount":t.amount, "date":t.date, "trip_id":t.trip_id, "trip_name":t.trip_name, "transaction_type":t.transaction_type}
    #     df_t.append(transaction, ignore_index=True)
    return df_t

