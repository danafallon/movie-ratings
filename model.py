"""Models and database functions for Ratings project."""

from flask_sqlalchemy import SQLAlchemy
from correlation import pearson

# This is the connection to the SQLite database; we're getting this through
# the Flask-SQLAlchemy helper library. On this, we can find the `session`
# object, where we do most of our interactions (like committing, etc.)

db = SQLAlchemy()


##############################################################################
# Model definitions

class User(db.Model):
    """User of ratings website."""

    __tablename__ = "users"

    user_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    email = db.Column(db.String(64), nullable=True)
    password = db.Column(db.String(64), nullable=True)
    age = db.Column(db.Integer, nullable=True)
    zipcode = db.Column(db.String(15), nullable=True)

    def __repr__(self):
        """Provide helpful representation when printed."""

        return "<User user_id=%s email=%s>" % (self.user_id, self.email)

    def similarity(self, other_user):
        """Create pairs of ratings for the two users and calculate similarity
        score using pearson function."""

        u = self
        o = other_user
        u_ratings = u.ratings                                       # list of objects
        o_ratings = o.ratings                                       # list of objects
        movies_u_rated = set([rating.movie_id for rating in u_ratings])
        movies_o_rated = set([rating.movie_id for rating in o_ratings])
        movies_both_rated = movies_u_rated & movies_o_rated                       # set of movie_ids in common
        u_scores = {}
        for rating in u.ratings:
            if rating.movie_id in movies_both_rated:
                u_scores[rating.movie_id] = rating.score

        o_scores = {}
        for rating in o.ratings:
            if rating.movie_id in movies_both_rated:
                o_scores[rating.movie_id] = rating.score

        pairs = []
        for movie_id in u_scores.keys():
            score_pair = (u_scores[movie_id], o_scores[movie_id])
            pairs.append(score_pair)

        return pearson(pairs)


    # def pick_similar_user():


    # def predict_score():




class Movie(db.Model):
    """Movie in database."""
    __tablename__="movies"

    movie_id = db.Column(db.Integer,autoincrement=True, primary_key=True)
    title = db.Column(db.String(64), nullable=True)
    released_at = db.Column(db.DateTime, nullable=True)
    imdb_url = db.Column(db.String(200), nullable=True)

class Rating(db.Model):
    """Rating of movie by user."""
    __tablename__ = "ratings"

    rating_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.movie_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    score = db.Column(db.Integer, nullable=True)

     # Define relationship to user
    user = db.relationship("User", backref=db.backref("ratings", order_by=rating_id))

    # Define relationship to movie
    movie = db.relationship("Movie", backref=db.backref("ratings", order_by=rating_id))


    def __repr__(self):
        """Provide helpful representation when printed."""

        return "<Rating rating_id=%s movie_id=%s user_id=%s score=%s>" % (self.rating_id, self.movie_id, self.user_id, self.score)


##############################################################################
# Helper functions

def connect_to_db(app):
    """Connect the database to our Flask app."""

    # Configure to use our SQLite database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ratings.db'
    db.app = app
    db.init_app(app)


if __name__ == "__main__":
    # As a convenience, if we run this module interactively, it will leave
    # you in a state of being able to work with the database directly.

    from server import app
    connect_to_db(app)
    print "Connected to DB."