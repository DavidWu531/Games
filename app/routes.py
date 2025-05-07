from app import app
from flask import render_template, abort, redirect  # noqa: F401
from flask_sqlalchemy import SQLAlchemy
import os


basedir = os.path.abspath(os.path.dirname(__file__))
db = SQLAlchemy()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, "games.db")  # noqa: E501
db.init_app(app)


import app.models as models  # type: ignore # noqa: F401, E402


def execute_query(model, id: int = 0):
    try:
        if not id:
            return model.query.all()

        record = model.query.get_or_404(id)
        return [record]
    except OverflowError:
        abort(404)


@app.route('/')
def home_page():
    return render_template('home.html')


@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/platform/', defaults={'id': None})
@app.route('/platform/<int:id>')
def platform(id):
    platforms = None
    if id is None:
        return redirect("/platform/0")

    platforms = execute_query(models.Platforms, id)
    return render_template('all_platforms.html', platforms=platforms)


@app.route('/game/', defaults={'id': None})
@app.route('/game/<int:id>')
def game(id):
    games = None
    if id is None:
        return redirect("/game/0")

    games = execute_query(models.Games, id)
    return render_template('all_games.html', games=games)


@app.route('/category/', defaults={'id': None})
@app.route('/category/<int:id>')
def category(id):
    categories = None
    if id is None:
        return redirect("/category/0")

    categories = execute_query(models.Categories, id)
    return render_template('categorys.html', categories=categories)
