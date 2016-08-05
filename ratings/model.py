"""Models and database functions for Ratings project."""

from flask_sqlalchemy import SQLAlchemy
import correlation

# This is the connection to the PostgreSQL database; we're getting this through
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
        """Provide helpful representation when printed"""

        return "<User user_id={} email={}>".format(self.user_id, self.email)


    def similarity(self, other):
        """
        Calculate the similarity between self and a given user based on similarity of
        previous movie ratings
        """

        paired_ratings = {}
        final_pairs = []

        for rating in self.ratings:
            paired_ratings[rating.movie_id] = [rating.score]

        for rating in other.ratings:
            if paired_ratings.get(rating.movie_id):
                paired_ratings[rating.movie_id].append(rating.score)

        for key, value in paired_ratings.items():
            if len(value) == 2:
                final_pairs.append((value[0], value[1]))

        if len(final_pairs) > 0:
            return correlation.pearson(final_pairs)



    def compare_all_users(self):
        """Comparing correlation between all users and self based on previous ratings"""

        all_users = User.query.all()

        correlation_comparison = []

        for user in all_users:
            indiv_correlation = self.similarity(user)
            if indiv_correlation is not None:
                correl_user_pair = (indiv_correlation, user.user_id)
                correlation_comparison.append(correl_user_pair)

        return correlation_comparison


    def predict_rating(self, movie_id):
        """For a given movie, predicts what self will rate based on correlation with other users"""

        correlation_comparison = self.compare_all_users()
        pearson = []

        all_users_rated = Rating.query.filter(Rating.movie_id == movie_id).all()

        id_score_pair = {}


        for user in all_users_rated:
            id_score_pair[user.user_id] = user.score

        for correlation in correlation_comparison:
            user_id = correlation[1]
            if user_id in id_score_pair.keys():
                pearson.append((correlation[0], id_score_pair[user_id]))

        numerator = sum([correlation * score for correlation, score in pearson])

        denominator = sum([correlation for correlation, score in pearson])

        return numerator/denominator



# Put your Movie and Rating model classes here.

class Movie(db.Model):
    """Table of Movies"""

    __tablename__ = "movies"

    movie_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    title = db.Column(db.String(90), nullable=False)
    released_at = db.Column(db.DateTime, nullable=True)
    imdb_url = db.Column(db.String(200), nullable=True)


    def __repr__(self):
        """Provide helpful representation when printed"""

        return "<Movie movie_id={} title={}>".format(self.movie_id, self.title)


class Rating(db.Model):
    """Table of Ratings"""

    __tablename__ = "ratings"

    rating_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.movie_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)

    #defining relationship to user
    user = db.relationship("User", backref=db.backref("ratings", order_by=rating_id))

    #defining relationship to movie
    movie = db.relationship("Movie", backref=db.backref("ratings", order_by=rating_id))


    def __repr__(self):
        """Provide helpful representation when printed"""

        return "<Rating rating_id={} movie_id={}, user_id={}, score={}>".format(self.rating_id, 
                                                                                self.movie_id,
                                                                                self.user_id,
                                                                                self.score)



##############################################################################
# Helper functions

def connect_to_db(app):
    """Connect the database to our Flask app."""

    # Configure to use our PstgreSQL database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///ratings'
    db.app = app
    db.init_app(app)


if __name__ == "__main__":
    # As a convenience, if we run this module interactively, it will leave
    # you in a state of being able to work with the database directly.

    from server import app
    connect_to_db(app)
    print "Connected to DB."
