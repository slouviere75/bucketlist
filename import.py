import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def main():
    f = open("trips.csv")
    reader = csv.reader(f)
    print("Reader Type "+str(type(reader)))
    db.execute("CREATE TABLE trips (id SERIAL PRIMARY KEY, name VARCHAR NOT NULL, description VARCHAR NOT NULL, author VARCHAR NOT NULL, year VARCHAR NOT NULL)")
    for isbn, title, author, year in reader:
        db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
                    {"isbn": isbn, "title": title, "author": author,"year": year})
        print(f"Added book ISBN:  {isbn} by {author} from {year}.")
    db.commit()

if __name__ == "__main__":
    main()
