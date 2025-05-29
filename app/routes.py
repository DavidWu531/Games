import sqlite3
from app import app
from flask import render_template, abort, redirect, session
from flask_sqlalchemy import SQLAlchemy
import os
from flask_bcrypt import Bcrypt

basedir = os.path.abspath(os.path.dirname(__file__))
db = SQLAlchemy()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, "games.db")
db.init_app(app)
bcrypt = Bcrypt()
app.secret_key = os.urandom(12)


import app.models as models  # noqa: E402
from app.forms import LoginForm, RegisterForm  # noqa: E402


# Helper function for querying data
def execute_query(model, id: int = 0):
    try:
        if not id:  # id returns false or equals 0, get all
            return model.query.all()
        # else get data based on id
        record = model.query.get_or_404(id)
        # return in list due to original being instances
        # allows data to be displayed in templates using for loop
        return [record]
    except OverflowError:
        # prevents extremely large numbers from id
        abort(404)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = models.Accounts.query.filter_by(AccountUsername=form.username.data).first_or_404()
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            session['AccountID'] = user.AccountID
            return redirect("/")
        else:
            return redirect("/login")

    return render_template('login.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        temp_username = form.username.data
        temp_password = form.password.data

        # Checks if username contains other characters besides letters and numbers
        if not (temp_username.isalnum() and temp_username.isascii()):
            return redirect('/register')

        # Checks if password contains spaces since they're not recommended
        if (temp_password.strip() != temp_password) or (temp_username.strip() != temp_username):
            return redirect('/register')

        # Hash password
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        try:
            new_account = models.Accounts(AccountUsername=temp_username, AccountPassword=hashed_password)
            db.session.add(new_account)
            db.session.commit()
        except sqlite3.IntegrityError:
            db.session.rollback()
            return redirect('/register')
        else:
            print(f"User {temp_username} registered")
            return redirect('/login')
    else:
        print(form.errors)

    return render_template('register.html', form=form)


# Home Page Route
@app.route('/')
def home_page():
    return render_template('home.html')


# Show 404 error page if route not found
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404


# About Page Route
@app.route('/about')
def about():
    return render_template('about.html')


# Displays platforms, allows id=0 for redirecting
@app.route('/platform/', defaults={'id': None})
@app.route('/platform/<int:id>')
def platform(id):
    platforms = None
    if id is None:
        return redirect("/platform/0")

    # query data via helper function
    platforms = execute_query(models.Platforms, id)

    if id == 0:  # template all if id is 0 else individual
        return render_template('all_platforms.html', platforms=platforms)
    else:
        return render_template('individual_platforms.html', platforms=platforms)


# Displays platforms, allows id=0 for redirecting
@app.route('/game/', defaults={'id': None})
@app.route('/game/<int:id>')
def game(id):
    games = None
    if id is None:
        return redirect("/game/0")

    # query data via helper function
    games = execute_query(models.Games, id)

    if id == 0:  # template all if id is 0 else individual
        return render_template('all_games.html', games=games)
    else:
        return render_template('individual_games.html', games=games)


# Displays platforms, allows id=0 for redirecting
@app.route('/category/', defaults={'id': None})
@app.route('/category/<int:id>')
def category(id):
    categories = None
    if id is None:
        return redirect("/category/0")

    # query data via helper function
    categories = execute_query(models.Categories, id)

    if id == 0:  # template all if id is 0 else individual
        return render_template('all_categories.html', categories=categories)
    else:
        return render_template('individual_categories.html', categories=categories)
