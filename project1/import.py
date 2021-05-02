import sys
import os
import csv
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
print(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

# Check command line arguments.
if len(sys.argv) != 2:
    print("Usage: import.py csv")
    exit(1)

# Open csv file and create nested dictionary of data.
with open(sys.argv[1], "r") as database:
    reader = csv.reader(database)

    id = 0
    i = 0
    for row in reader:
        if i != 0:
            isbn = row[0]
            title = row[1]
            author = row[2]
            year = row[3]
            engine.execute("INSERT INTO books (id, isbn, title, author, year) VALUES (%s, %s, %s, %s, %s)", 
            (id, isbn, title, author, year))
            id += 1
        i += 1