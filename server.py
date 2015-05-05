"""Movie Ratings."""

from jinja2 import StrictUndefined

from flask import Flask, render_template, redirect, request, flash, session
from flask_debugtoolbar import DebugToolbarExtension

from model import User, Rating, Movie, connect_to_db, db


app = Flask(__name__)

# Required to use Flask sessions and the debug toolbar
app.secret_key = "ABC"

# Normally, if you use an undefined variable in Jinja2, it fails silently.
# This is horrible. Fix this so that, instead, it raises an error.
app.jinja_env.undefined = StrictUndefined


@app.route('/')
def index():
    """Homepage."""

    return render_template("homepage.html")


@app.route('/users')
def user_list():
    """Show list of users."""

    users = User.query.all()
    return render_template("user_list.html", users=users)


@app.route('/users/<int:id>')
def user_details(id):
    """Display user details for user specified in url."""

    user = User.query.get(id)

    rating_dict = {}    
    ratings = Rating.query.filter_by(user_id=id).all()
    for rating in ratings:                                     # make dictionary with movie title as key and rating score as value
        title = Movie.query.filter_by(movie_id=rating.movie_id).one().title
        rating_dict[title] = rating.score

    return render_template('user_details.html', user=user, ratings=rating_dict)


@app.route('/movies')
def movie_list():
    """Show list of movies."""

    movies = Movie.query.order_by("title").all()
    return render_template("movie_list.html", movies=movies)


@app.route('/movies/<int:movie_id>',methods=["GET","POST"])
def movie_details(movie_id):
    """Display movie details for movie_id specified in url."""

    movie = Movie.query.get(movie_id)

    ratings = Rating.query.filter_by(movie_id=movie_id).all()

    rating = request.form.get("rating")
    user_id = session.get('user_id', [])
    if user_id:
        record = Rating.query.filter_by(movie_id=movie_id, user_id=user_id).first()

    if rating:

        if record:
            record.score = rating
            flash('Rating updated')
        else:
            record = Rating(movie_id=movie_id, user_id=user_id, score=rating)
            db.session.add(record)
            flash('Rating saved')

        db.session.commit()
        print Rating.query.filter_by(movie_id=movie_id, user_id=user_id).all()

        return redirect('/movies/%d' % movie_id)

    return render_template('movie_details.html', movie=movie, ratings=ratings, record=record)


@app.route('/login', methods=["GET"])
def show_login():
    """Display login form."""

    return render_template("login.html")


@app.route('/login', methods=["POST"])
def login():
    """Check credentials and log user in."""

    email = request.form.get("email")
    password = request.form.get("password")

    user = User.query.filter_by(email=email).first()
    id = user.user_id

    if not user:
        flash("Email not registered")
        return redirect('/login')

    if user.password == password:
        session['email'] = email
        session['user_id'] = id
        flash("Logged in")
        return redirect('/users/%d' % id)
    else:
        flash("Incorrect password")
        return redirect('/login')
 

@app.route('/logout')
def logout():
    """Log user out."""

    del session['email']
    flash("You have been successfully logged out.")
    return redirect('/')

if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the point
    # that we invoke the DebugToolbarExtension
    app.debug = True

    connect_to_db(app)

    # Use the DebugToolbar
    # DebugToolbarExtension(app)

    app.run()