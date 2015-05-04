"""Utility file to seed ratings database from MovieLens data in seed_data/"""

from model import User, Rating, Movie, connect_to_db, db
from server import app
import datetime


def load_users():
    """Load users from u.user into database."""

    users_file = open("seed_data/u.user")

    for line in users_file:
        user_info = line.split("|")
        user_id = user_info[0]
        user_age = user_info[1]
        user_zipcode = user_info[4]
        
        user = User(user_id=user_id,age=user_age,zipcode=user_zipcode)
        db.session.add(user)

    db.session.commit()

def load_movies():
    """Load movies from u.item into database."""

    movies_file = open("seed_data/u.item")

    for line in movies_file:
        movie_info = line.split("|")
        movie_id = movie_info[0]
        movie_title = movie_info[1]
        movie_title = movie_title[:-7]          # remove year in parentheses from title
        release_date = movie_info[2]
        if release_date:
            release_date = datetime.datetime.strptime(release_date, "%d-%b-%Y") # store date as date object
        else:
            release_date = None
        imdb_url = movie_info[4]

        movie = Movie(movie_id=movie_id, title=movie_title, released_at=release_date, imdb_url=imdb_url)
        db.session.add(movie)

    db.session.commit()


def load_ratings():
    """Load ratings from u.data into database."""

    ratings_file = open("seed_data/u.data")

    for line in ratings_file:
        rating_info = line.strip().split("\t")
        user_id = rating_info[0]
        movie_id = rating_info[1]
        score = rating_info[2]

        rating = Rating(user_id=user_id, movie_id=movie_id, score=score)
        db.session.add(rating)

    db.session.commit()   



if __name__ == "__main__":
    connect_to_db(app)

    load_users()
    load_movies()
    load_ratings()
