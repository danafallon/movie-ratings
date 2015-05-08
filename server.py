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

    users = User.query.order_by(User.user_id.desc()).all()

    return render_template("user_list.html", users=users)


@app.route('/users/<int:id>')
def user_details(id):
    """Display user details for user specified in url."""

    user = User.query.get(id)

    rating_dict = {}    
    ratings = Rating.query.filter_by(user_id=id).all()
    for rating in ratings:                                     # make dictionary with movie title as key and rating score as value
        movie = Movie.query.filter_by(movie_id=rating.movie_id).one()
        rating_dict[movie] = rating.score

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

    rating_scores = [r.score for r in movie.ratings]
    avg_rating = float(sum(rating_scores)) / len(rating_scores)

    prediction = None
    record = None

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

        if not record:
            user = User.query.get(user_id)
            if user:
                prediction = user.predict_rating(movie)

        # compare the user's rating/prediction to the eye's rating/prediction:
        # Either use the prediction or their real rating
        if prediction:
            # User hasn't scored; use our prediction if we made one
            effective_rating = prediction

        elif record:
            # User has already scored for real; use that
            effective_rating = record.score

        else:
            # User hasn't scored, and we couldn't get a prediction
            effective_rating = None

        # Get the eye's rating, either by predicting or using real rating

        the_eye = User.query.filter_by(email="the-eye@of-judgment.com").one()
        eye_rating = Rating.query.filter_by(
            user_id=the_eye.user_id, movie_id=movie.movie_id).first()

        if eye_rating is None:
            eye_rating = the_eye.predict_rating(movie)
            print eye_rating
        else:
            eye_rating = eye_rating.score


        if eye_rating and effective_rating:
            difference = abs(eye_rating - effective_rating)
        else:
            # We couldn't get an eye rating, so we'll skip difference
            difference = None

        BERATEMENT_MESSAGES = [
            "I suppose you don't have such bad taste after all.",
            "I regret every decision that I've ever made that has brought me" +
                " to listen to your opinion.",
            "Words fail me, as your taste in movies has clearly failed you.",
            "That movie is great. For a clown to watch. Idiot.",
            "Words cannot express the awfulness of your taste."
        ]

        if difference:
            beratement = BERATEMENT_MESSAGES[int(difference)]

        else:
            beratement = None

    return render_template('movie_details.html', movie=movie, ratings=ratings, record=record, 
        prediction=prediction, average=avg_rating, beratement=beratement, eye_rating=eye_rating)


@app.route('/search', methods=["GET"])
def search_movies():
    """Take user's search input and find matching movie."""

    title = request.args.get("title")

    matches = Movie.query.filter(Movie.title.like('%'+title+'%')).all()

    if len(matches) > 1:
        return render_template('search_results.html', matches=matches)

    if len(matches) == 1:
        movie_id = matches[0].movie_id
        return redirect('/movies/%d' % movie_id)

    if len(matches) == 0:
        flash('No movies found matching this search')
        return redirect('/movies')


@app.route('/login', methods=["GET"])
def show_login():
    """Display login form."""

    return render_template("login.html")


@app.route('/login', methods=["POST"])
def login():
    """Check credentials and log user in."""

    email = request.form.get("email")
    password = request.form.get("password")

    if not email or not password:
        flash("Please enter your email address and password")
        return redirect('/login')

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

@app.route('/register', methods=["GET"])
def show_registration():
    """Display user registration form"""

    return render_template('register_user.html')

@app.route('/register', methods=["POST"])
def register_user():
    """Gather registration information and validate"""

    email = request.form.get("email")
    password = request.form.get("password")
    age = request.form.get("age")
    zipcode = request.form.get("zipcode")

    registered_user = User.query.filter_by(email=email).first()

    if registered_user:
        flash("Email is already associated with a user")
        return redirect('/register')

    elif not email or not password:
        flash("Please enter an email address and password")
        return redirect('/register')

    else:
        new_user = User(email=email,password=password,age=age,zipcode=zipcode)
        db.session.add(new_user)
        db.session.commit()
        
        user_id = User.query.filter_by(email=email).first().user_id
        session['email'] = email
        session['user_id'] = user_id

        return redirect('/users/%d' % user_id)
 

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