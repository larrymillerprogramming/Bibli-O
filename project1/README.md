Important environmental variables:

FLASK_APP = application.py

Bibli-O is a book review website, designed for a community of readers to share their ideas and discover new books.

This website is built with Python (Flask), PostgreSQL, HTML5, and CSS (including Bootstrap). It also utilizes the API of goodreads.com to present the average rating and number of ratings of each book in the database hosted on Heroku.

This project includes the following files:

application.py, books.csv (a collection of books featured on the website), helpers.py (includes functions that aid the functionality of the website), import.py (used to import books.csv to the database)

Templates folder:

apology.html (error page),
book.html (dynamic page for each book in the database),
index.html (homepage when logged in),
layout.html (HTML for the website's design),
login.html (homepage when not logged in),
myreviews.html (shows current user's reviews),
register.html (page to register for a new account),
search.html (displays search results)

Static folder:

image files,
css stylesheet
