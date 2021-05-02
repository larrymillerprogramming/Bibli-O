import os
import requests

from flask import Flask, session, request, redirect, render_template
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

app = Flask(__name__)

# Check for environment variable
# DATABASE_URL should be set to:
# postgres://qczpppwpbvtwtj:9581d3c887c2b503ef97d7093f56b28763f9d23c0b3df1b8e5af1f6557c0587e@ec2-34-230-231-71.compute-1.amazonaws.com:5432/d3o14tuaeo0qcn
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))
connection = engine.connect()

@app.route("/")
@login_required
def index():
    # Retrive username.
    getusername = connection.execute("SELECT username FROM users WHERE id = %s", session["user_id"]).fetchone()
    username=getusername[0]

    # Display 5 most recent reviews.
    recreviews_dict = connection.execute("SELECT * FROM reviews, users, books WHERE users.id = reviews.user_id AND reviews.book_id = books.id ORDER BY time DESC LIMIT 5").fetchall()
    table_data = "<tr><th>Oops! No reviews to share yet.</th></tr>"
    if len(recreviews_dict) > 0:
        table_data = ""
        for i in range(len(recreviews_dict)):
            rev_username = recreviews_dict[i]["username"]
            book_id = recreviews_dict[i]["book_id"]
            title = recreviews_dict[i]["title"]
            author = recreviews_dict[i]["author"]
            description = recreviews_dict[i]["description"]
            date = recreviews_dict[i]["time"]
            table_data = table_data + '<tr><th><a href="/book/{}">{}</a></th><th>{}</th></tr><tr><td>{}</td><td>{}</td></tr><tr><td class="description" colspan="3">{}</td><tr>'.format(book_id, title, author, rev_username, date, description)
    return render_template("index.html", table_data=table_data, username=username)

@app.route("/login", methods=["GET", "POST"])
def login():
    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("Must provide username.", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("Must provide password.", 403)

        # Query database for username
        rows = connection.execute("SELECT * FROM users WHERE username = %s",
            request.form.get("username").lower()).fetchall()

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    # Forget any user_id.
    session.clear()

    # User reached route via POST (as by submitting a form via POST).
    if request.method == "POST":

        # Ensure username was submitted and unique.
        if not request.form.get("username"):
            return apology("must provide username", 403)

        reg_username = ""
        reg_username = connection.execute("SELECT * FROM users WHERE username = %s",
                request.form.get("username").lower()).fetchall()
        if len(reg_username) > 0:
            return apology("username has already been used", 403)

        # Ensure password and confirmation were typed, and they match.
        if not request.form.get("password"):
            return apology("must provide password", 403)

        if not request.form.get("confirmation"):
            return apology("must confirm password", 403)

        if request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords did not match", 403)

        # Hash password.
        password_hash = generate_password_hash(request.form.get("password"))

        # INSERT username and password hash to users table.
        connection.execute("INSERT INTO users (username, hash) VALUES (%s, %s)",
                        request.form.get("username").lower(), password_hash)

        # Redirect user to home page to log in.
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

@app.route("/search", methods=["GET", "POST"])
def search():
    # Retrive username.
    getusername = connection.execute("SELECT username FROM users WHERE id = %s", session["user_id"]).fetchone()
    username=getusername[0]

    # Render index if accessed via GET.
    if request.method == "GET":
        return render_template("index.html", username=username)

    # When accessed via POST, redirect to the dynamic route.
    else:
        keyword = request.form.get("keyword")
        if not keyword:
            return apology("Search was empty! Try again.", 403)
        return redirect("/search/{keyword}".format(keyword=keyword))

@app.route("/search/<keyword>")
def searchby(keyword):
    # Collect reviews for the selected book.
    table_data = "<tr><th>Oops! No results for your search. Try another keyword.</th></tr>"
    likekeyword = "%" + keyword + "%"
    result_dict = connection.execute("SELECT id, title, author, year, isbn FROM books WHERE title ILIKE %s OR author ILIKE %s OR isbn ILIKE %s OR year ILIKE %s", likekeyword, likekeyword, likekeyword, likekeyword).fetchall()
    
    # Retrive username.
    getusername = connection.execute("SELECT username FROM users WHERE id = %s", session["user_id"]).fetchone()
    username=getusername[0]

    # Build the table of reviews.
    if len(result_dict) > 0:
        table_data = "<tr><th>Title</th><th>Author</th><th>ISBN 10</th><th>Published</th></tr>"
        for i in range(len(result_dict)):
            id = result_dict[i]["id"]
            title = result_dict[i]["title"]
            author = result_dict[i]["author"]
            year = result_dict[i]["year"]
            isbn = result_dict[i]["isbn"]
            table_data = table_data + '<tr><td><a href="/book/{}">{}</a></td><td>{}</td><td>{}</td><td>{}</td></tr>'.format(id, title, author, isbn, year)
    return render_template("search.html", keyword=keyword, table_data=table_data, username=username)

@app.route("/book/<book_id>", methods=["GET"])
def book(book_id):
    # Retrive username.
    getusername = connection.execute("SELECT username FROM users WHERE id = %s", session["user_id"]).fetchone()
    username=getusername[0]

    # Check that book id is valid.
    check_id = connection.execute("SELECT * FROM books WHERE id = %s",
            book_id).fetchone()
    if len(check_id) == 0:
        return apology("Book id not found. Try another book id.", 403)

    # Assign information for the selected book.
    title = check_id["title"]
    author = check_id["author"]
    year = check_id["year"]
    isbn = check_id["isbn"]

    # Calculate average rating and number of ratings on Bibli-O.
    ratings_dict = connection.execute("SELECT rating FROM reviews WHERE book_id = %s", book_id).fetchall()
    ratings_total = 0
    for i in range(len(ratings_dict)):
        ratings_total += ratings_dict[i]["rating"]
    bavgrating = "N/A"
    bnumrating = 0
    if len(ratings_dict) > 0:
        bavgrating = round((ratings_total / len(ratings_dict)), 1)
        if bavgrating % 1 == 0:
            bavgrating = round(bavgrating)
        bnumrating = len(ratings_dict)
        bavgrating = str(bavgrating) + "/5"

    # Collect average rating and number of ratings from Goodreads API./
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "oFBMcy89m6PpuP5C5liDDw", "isbns": "{}".format(isbn)}).json()
    gavgrating = round(float(res["books"][0]["average_rating"]), 1)
    if gavgrating % 1 == 0:
        gavgrating = round(gavgrating)
    gavgrating = str(gavgrating) + "/5"
    gnumrating = "{:,}".format(int(res["books"][0]["work_ratings_count"]))

    # Select all reviews for this book and create table.
    table_data = "<tr><th>No reviews for this book yet. Be the first!</th></tr>"
    review_dict = connection.execute("SELECT * FROM reviews, users WHERE users.id = reviews.user_id AND book_id = %s ORDER BY time DESC", book_id).fetchall()
    if len(review_dict) > 0:
        table_data = "<tr><th>User</th><th>Time</th><th>Rating</th>"
        for i in range(len(review_dict)):
            username = review_dict[i]["username"]
            timestamp = review_dict[i]["time"]
            rating = review_dict[i]["rating"]
            description = review_dict[i]["description"]
            table_data = table_data + '<tr><td>{}</td><td>{}</td><td>{}/5</td></tr><tr><td class="description" colspan="3">{}</td><tr>'.format(username, timestamp, rating, description)
    return render_template("book.html", title=title, author=author, isbn=isbn, year=year,
    book_id=book_id, table_data=table_data, username=username, bavgrating=bavgrating, bnumrating=bnumrating,
    gnumrating=gnumrating, gavgrating=gavgrating)

@app.route("/review", methods=["POST"])
@login_required
def review():
    # Add submitted review to the Reviews table
    connection.execute("INSERT INTO reviews (user_id, book_id, rating, description) VALUES (%s, %s, %s, %s)",
                        session["user_id"], request.form.get("book_id"), request.form.get("rating"), request.form.get("description"))
    return redirect("/book/{book_id}".format(book_id=request.form.get("book_id")))

@app.route("/myreviews")
@login_required
def myreviews():
    # Retrive username.
    getusername = connection.execute("SELECT username FROM users WHERE id = %s", session["user_id"]).fetchone()
    username=getusername[0]

    # Show users reviews, beginning with the most recent.
    myreviews_dict = connection.execute("SELECT * FROM reviews, users, books WHERE users.id = reviews.user_id AND users.id = %s AND reviews.book_id = books.id ORDER BY time DESC", session["user_id"]).fetchall()
    table_data = "<tr><th>Oops! No reviews to share yet.</th></tr>"
    if len(myreviews_dict) > 0:
        table_data = "<tr><th>Title</th><th>Author</th><th>Date</th></tr>"
        for i in range(len(myreviews_dict)):
            book_id = myreviews_dict[i]["book_id"]
            title = myreviews_dict[i]["title"]
            author = myreviews_dict[i]["author"]
            description = myreviews_dict[i]["description"]
            date = myreviews_dict[i]["time"]
            table_data = table_data + '<tr><td><a href="/book/{}">{}</a></td><td>{}</td><td>{}</td></tr><tr><td class="description" colspan="3">{}</td><tr>'.format(book_id, title, author, date, description)
    return render_template("myreviews.html", table_data=table_data, username=username)