"""Movie Ratings."""

from jinja2 import StrictUndefined

from flask import (Flask, render_template, redirect, request, flash,
                   session)
from flask_debugtoolbar import DebugToolbarExtension

from model import User, Rating, Movie, connect_to_db, db

from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)

# Required to use Flask sessions and the debug toolbar
app.secret_key = "ABC"

# Normally, if you use an undefined variable in Jinja2, it fails
# silently. This is horrible. Fix this so that, instead, it raises an
# error.
app.jinja_env.undefined = StrictUndefined


@app.route('/')
def index():
    """Homepage."""

    return render_template("homepage.html")


@app.route('/users')
def user_list():
    """Show list of users"""

    users = User.query.all()
    return render_template("user_list.html", users=users)


@app.route('/movies')
def movie_list():
    """Show list of movies"""

    movies = Movie.query.order_by('title').all()
    return render_template("movie_list.html", movies=movies)


@app.route('/register', methods=['GET'])
def register_form():
    """Registration form asking for username and password"""

    return render_template("register_form.html")


@app.route('/register', methods=['POST'])
def register_process():
    """Process sign-in form, checking to see if username exists,
    and if not, creating new user in the database.
    Alerts users with flash message"""

    input_email = request.form.get('email')
    password = request.form.get('password')

    if User.query.filter(User.email == input_email).all():
        flash("That email is already registered. Please log in or choose a different email.")
        return redirect('/register')
    
    else:
        new_user = User(email=input_email, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash("You are now registered!")
        return redirect('/')


@app.route('/login', methods=['GET'])
def login_form():
    """Login form asking for username and password"""

    return render_template("login_form.html")



@app.route('/login',  methods=['POST'])
def login():
    """Allow user to log in to their account"""

    input_email = request.form.get('email')
    password = request.form.get('password')

   
    check_username = User.query.filter(User.email == input_email).first()

    if check_username:
        if check_username.password == password:
            session["current_login"] = input_email
            # print session["current_login"]
            flash("You are now logged in!")
            return redirect('/')
        else:
            flash("The email and password you entered does not match our records")
            return redirect('/login')

    else:
        flash("The email you entered does not exist in our records")
        return redirect('/login')


@app.route('/logout')
def logout():
    """Logout of ratings application."""

    session["current_login"] = None
    # print session["current_login"]
    
    flash("You are now logged out.")
    
    return redirect('/')


@app.route('/users/<int:user_id>')
def user_details(user_id):
    """Shows information about a particular user, including age, zipcode, and rated movies"""

    queried_user = User.query.filter(User.user_id == user_id).first()

    rating_list = []

    for rating in queried_user.ratings:
        movie_name = (Movie.query.filter(Movie.movie_id == rating.movie_id).first()).title
        movie_and_rating = (movie_name, rating.score)
        rating_list.append(movie_and_rating)


    return render_template('user_details.html', 
                            zipcode=queried_user.zipcode, 
                            user=queried_user.user_id, 
                            age=queried_user.age,
                            ratings=rating_list)


@app.route('/movies/<int:movie_id>')
def movie_details(movie_id):
    """Shows information about a particular user, including age, zipcode, and rated movies"""

    queried_movie = Movie.query.filter(Movie.movie_id == movie_id).first()

    rating_list = []

    prediction = None

    for rating in queried_movie.ratings:
        rating_user = (User.query.filter(User.user_id == rating.user_id).first()).user_id
        user_and_rating = (rating_user, rating.score)
        rating_list.append(user_and_rating)

    if session["current_login"]:
        current_user = User.query.filter(User.email == session['current_login']).first()
        user_score = Rating.query.filter((Rating.user_id == current_user.user_id) & (Rating.movie_id == movie_id)).first()
        if not user_score:
            prediction = current_user.predict_rating(movie_id)


    return render_template('movie_details.html', 
                            released=queried_movie.released_at,
                            imdb=queried_movie.imdb_url,
                            title=queried_movie.title,
                            ratings=rating_list,
                            movie_id=movie_id,
                            prediction=prediction)


@app.route('/add_score_to_db/<int:movie_id>', methods=["POST"])
def add_new_score(movie_id):
    """
    Allows a user who is logged in to add a score to the database for a given movie.
    If they have already rated the movie, updates their old score
    """

    new_rating = request.form.get("new-score")

    if session['current_login']:

        store_user = User.query.filter(User.email == session['current_login']).first()
        user_rating_exists = Rating.query.filter((Rating.user_id == store_user.user_id) & (Rating.movie_id == movie_id)).first()

        if user_rating_exists:
            user_rating_exists.score = new_rating
            db.session.commit()
            flash("You have updated your old rating")
        else:
            user_rating = Rating(movie_id=movie_id, user_id=store_user.user_id, score=new_rating)
            db.session.add(user_rating)
            db.session.commit()
            flash("You have added your score to the database!")

    else:
        flash("Sorry, you have to be logged in to add a score")

    return redirect('/movies/{}'.format(movie_id))
    


if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the
    # point that we invoke the DebugToolbarExtension
    app.debug = True

    connect_to_db(app)

    # Use the DebugToolbar
    # DebugToolbarExtension(app)

    app.run()
