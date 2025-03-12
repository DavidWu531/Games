from app import app
from flask import render_template, abort  # noqa: F401
from flask_sqlalchemy import SQLAlchemy
import os


basedir = os.path.abspath(os.path.dirname(__file__))
db = SQLAlchemy()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, "pizza.db")  # noqa: E501
db.init_app(app)


import app.models as models  # type: ignore # noqa: F401, E402


@app.route('/')
def root():
    return render_template('home.html', page_title="HOME")


@app.route('/about')
def about():
    return render_template('about.html', page_title="ABOUT")


@app.route('/all_pizzas')
def all_pizzas():
    pass
