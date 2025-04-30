from app import app
from flask import render_template, abort  # noqa: F401
from flask_sqlalchemy import SQLAlchemy
import os


basedir = os.path.abspath(os.path.dirname(__file__))
db = SQLAlchemy()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, "games.db")  # noqa: E501
db.init_app(app)


import app.models as models  # type: ignore # noqa: F401, E402


@app.route('/')
def root():
    return render_template('home.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/all_platforms')
def all_platforms():
    platforms = models.Platforms.query.all()
    return render_template("all_platforms.html", platforms=platforms)


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
