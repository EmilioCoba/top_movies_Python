from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
import os
from dotenv import load_dotenv

load_dotenv()

'''
Red underlines? Install the required packages first: 
Open the Terminal in PyCharm (bottom left). 

On Windows type:
python -m pip install -r requirements.txt

On MacOS type:
pip3 install -r requirements.txt

This will install the packages from requirements.txt for this project.
'''
MOVIE_DB_SEARCH_URL="https://api.themoviedb.org/3/search/movie"
MOVIE_DB_API_KEY= os.getenv("MOVIE_DB_API_KEY")


app = Flask(__name__)
app.config['SECRET_KEY'] =os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///top-movies.db"
Bootstrap5(app)

# CREATE DB
class Base(DeclarativeBase):
  pass

db = SQLAlchemy(model_class=Base)

db.init_app(app)

# CREATE TABLE
class Movie(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=True)
    ranking: Mapped[int] = mapped_column(Integer, nullable=True)
    review: Mapped[str] = mapped_column(String(250), nullable=True)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)

with app.app_context():
    db.create_all()


#WTFORMS
# 1) Updating Form
class UpdateForm(FlaskForm):
    rating=StringField('Your Rating Out of 10 e.g. 7.5',validators=[DataRequired()])
    review=StringField('Your Review',validators=[DataRequired()])
    submit=SubmitField('Submit')

# 2)Movie Searching Form
class FindMovieForm(FlaskForm):
    movie_title=StringField('Movie Title',validators=[DataRequired()])
    submit=SubmitField('Add Movie')

# HOMEPAGE
@app.route("/")
def home():
    with app.app_context():
        result=db.session.execute(db.select(Movie).order_by(Movie.ranking))
        movies=result.scalars().all()

    for i, movie in enumerate(movies):
        movie.ranking = i + 1

    return render_template("index.html",movies=movies)


# ROUTE FOR ADDING MOVIES
@app.route("/add",methods=["GET","POST"])
def add():
    form=FindMovieForm()
    if form.validate_on_submit():
        movie_title=form.movie_title.data
        response = requests.get(MOVIE_DB_SEARCH_URL, params={"api_key": MOVIE_DB_API_KEY, "query": movie_title})
        data=response.json()['results']

    # if movies exist , you will select it from  a list of movies
        if data:
            return render_template('select.html',movies=data)
    #else u will get redirected back to search a movie
        else:
            return redirect(url_for("add"))
    return render_template('add.html',form=form)

#Find and Add new movie
@app.route("/find_movie")
def find_movie():
    movie_id = request.args.get("movie_id")
    if movie_id:
        movie_api_url = f"https://api.themoviedb.org/3/movie/{movie_id}"
        response = requests.get(
            movie_api_url,
            params={
                "api_key": MOVIE_DB_API_KEY,
                "language": "en-US"
            }
        )
        data = response.json()
        new_movie=Movie(
            title=data["title"],
            year=data["release_date"].split("-")[0],
            description=data['overview'],
            img_url=f"https://image.tmdb.org/t/p/w500{data['poster_path']}"
        )
        db.session.add(new_movie)
        db.session.commit()

        return redirect(url_for("edit",movie_id=new_movie.id))

# EDIT RATING AND REVIEW FUNCTION/ROUTE
@app.route("/edit/<int:movie_id>",methods=["GET","POST"])
def edit(movie_id):
    form=UpdateForm()
    movie = db.get_or_404(Movie, movie_id)

    if form.validate_on_submit():
        movie.rating=float(form.rating.data)
        movie.review=form.review.data
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("edit.html",movie=movie,form=form)

# DELETE FUNCTION
@app.route("/delete/<int:movie_id>")
def delete(movie_id):
    movie_to_delete = db.get_or_404(Movie, movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for("home"))





if __name__ == '__main__':
    app.run()
