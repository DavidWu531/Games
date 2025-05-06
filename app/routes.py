from app import app
from flask import render_template, abort, redirect  # noqa: F401
from flask_sqlalchemy import SQLAlchemy
import os


basedir = os.path.abspath(os.path.dirname(__file__))
db = SQLAlchemy()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, "games.db")  # noqa: E501
db.init_app(app)


import app.models as models  # type: ignore # noqa: F401, E402

# def execute_query(query, params=(), fetchone=False, fetchall=False,
#                   commit=False):
#     conn = sqlite3.connect('beds.db')
#     cur = conn.cursor()
#     try:  # Execute a query with parameters
#         cur.execute(query, params)
#         if commit:
#             conn.commit()

#         if fetchone:
#             result = cur.fetchone()
#         elif fetchall:
#             result = cur.fetchall()
#         else:
#             result = None
#     except sqlite3.Error as e:
#         # Return 500 Page when an error occurs
#         str(e).split().clear()
#         result = None
#         return render_template("500.html"), 500
#     finally:
#         conn.close()
#     return result


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
    elif id == 0:
        platforms = models.Platforms.query.all()
    else:
        try:
            platform_obj = models.Platforms.query.get_or_404(id)
        except OverflowError:
            return render_template("404.html"), 404

        if platform_obj is None:
            return render_template("404.html"), 404
        else:
            platforms = [platform_obj]
    return render_template('all_platforms.html', platforms=platforms)


@app.route('/game/', defaults={'id': None})
@app.route('/game/<int:id>')
def game(id):
    games = None
    if id is None:
        return redirect("/game/0")
    elif id == 0:
        games = models.Games.query.all()
    else:
        try:
            game_obj = models.Games.query.get_or_404(id)
        except OverflowError:
            return render_template("404.html"), 404

        if game_obj is None:
            return render_template("404.html"), 404
        else:
            games = [game_obj]
    return render_template('all_games.html', games=games)
