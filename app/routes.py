from app import app
from flask import render_template, abort, redirect, session, request
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
def execute_query(model, operation='SELECT', id=None, data=None, filters=None, search_fields=None):
    try:
        # SELECT OPERATION
        if operation == "SELECT":
            # Case 1: Fetch single records by ID
            if id is not None and id != 0:
                record = model.query.get_or_404(id)  # Auto-404 if none found
                return [record]  # Return as list for display in HTML
            # Case 2: Exact filtering, case-insensitive
            elif filters:  # Get queried results based on input
                query = model.query
                for column_name, value in filters.items():
                    column = getattr(model, column_name)
                    for column_name, value in filters.items():
                        column = getattr(model, column_name)
                        query = query.filter(column.ilike(f"{value}"))  # Exact, Case-insensitive match

                return query.all()
            # Case 3: Partial search
            elif search_fields:  # Get all results with input in query
                query = model.query
                for column_name, value in search_fields.items():
                    column = getattr(model, column_name)
                    query = query.filter(column.ilike(f"%{value}%"))  # Partial case-insensitive match
                return query.all()
            # Case 4: Get all
            else:
                return model.query.all()
        # INSERT OPERATION
        elif operation == "INSERT":
            if not data:
                abort(400, "Cannot insert data")
            record = model(**data)  # Create new record
            db.session.add(record)
            db.session.commit()
            return [record]  # Return new record
        # UPDATE OPERATION
        elif operation == "UPDATE":
            if not data or not id:
                abort(400, "Not all fields were filled in")
            record = model.query.get_or_404(id)  # Get existing record
            for key, value in data.items():
                setattr(record, key, value)  # Update each field
            db.session.commit()
            return [record]  # Return updated record
        # DELETE OPERATION
        elif operation == "DELETE":
            if id is None:
                abort(400, "ID not provided")
            record = model.query.get_or_404(id)
            db.session.delete(record)
            db.session.commit()
            return []  # Returns empty list, indicates data deleted
        else:
            abort(400, "Invalid operation")

    # ERROR HANDLING
    except OverflowError:
        # Invalid ID (Integer too large)
        abort(404)
    except Exception as e:
        # Revert on errors, abort Internal Server Error
        db.session.rollback()
        abort(500, f"Database error: {str(e)}")


# All errors use the same render template, but their code, title, and message are different when rendered
@app.errorhandler(404)
def not_found_error(e):
    return render_template("error.html", code=404, title="Page Not Found", message="The page doesn't exist"), 404


@app.errorhandler(400)
def bad_request_error(e):
    return render_template("error.html", code=400, title="Bad Request", message="Something went wrong with your request"), 400


@app.errorhandler(401)
def unauthourised_error(e):
    return render_template("error.html", code=401, title="Unauthorised Action", message="Request Denied: You are not logged in"), 400


@app.errorhandler(500)
def internal_server_error(e):
    return render_template("error.html", code=500, title="Internal Server Error", message="Something went wrong on our end"), 500


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        users = execute_query(models.Accounts, operation="SELECT", filters={"AccountUsername": form.username.data})
        user = users[0] if users else None  # Grabs first result, usernames are unique
        if user and bcrypt.check_password_hash(user.AccountPassword, form.password.data):
            session['AccountID'] = user.AccountID  # Logs user in
            return redirect("/dashboard")
        else:
            form.username.errors.append("Invalid username or password")
            return redirect("/login")

    return render_template('login.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        temp_username = form.username.data
        temp_password = form.password.data

        # Hash password
        hashed_password = bcrypt.generate_password_hash(temp_password).decode('utf-8')
        data = {
            "AccountUsername": temp_username,
            "AccountPassword": hashed_password
        }

        try:
            execute_query(models.Accounts, operation="INSERT", data=data)
            return redirect('/login')
        except Exception as e:
            db.session.rollback()
            if 'UNIQUE constraint failed' in str(e):
                form.username.errors.append("Account already exists")
            else:
                form.username.errors.append("An error occurred, please try again later")
            return render_template("register.html", form=form)
    else:
        print(form.errors)

    return render_template('register.html', form=form)


@app.route('/logout')
def logout():
    if "AccountID" in session:
        session.pop("AccountID", None)
    return redirect('/')


@app.route('/delete')
def delete():
    user_id = session.get("AccountID")
    if user_id is None:
        return redirect('/')

    try:
        execute_query(models.Accounts, operation="DELETE", filters={"AccountID": user_id})
    except Exception as e:  # noqa F841
        print("An error occurred, please try again later")
    else:
        session.pop("AccountID", None)
    return redirect('/')


@app.route('/dashboard')
def dashboard():
    if "AccountID" in session:
        return render_template('dashboard.html')
    else:
        return redirect('/login')


# Home Page Route
@app.route('/')
def home_page():
    return render_template('home.html')


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

    if id == 0:  # template all if id is 0 else individual
        # query data via helper function
        platforms = execute_query(models.Platforms, operation="SELECT", id=0)
        return render_template('all_platforms.html', platforms=platforms)
    else:
        platform = execute_query(models.Platforms, operation="SELECT", id=id)
        games = platform[0].games
        return render_template('individual_platforms.html', platform=platform[0], games=games)


# Displays platforms, allows id=0 for redirecting
@app.route('/game/', defaults={'id': None})
@app.route('/game/<int:id>')
def game(id):
    games = None
    if id is None:
        return redirect("/game/0")

    # query data via helper function
    games = execute_query(models.Games, "SELECT", id=id)

    if id == 0:  # template all if id is 0 else individual
        return render_template('all_games.html', games=games)
    else:
        user_rating = None
        user_id = session.get("AccountID")
        if user_id:
            user_rating = execute_query(models.Reviews, filters={"UserID": user_id, "GameID": id})
            if user_rating:
                user_rating = user_rating[0].Rating

        return render_template('individual_games.html', games=games, user_rating=user_rating)


# Displays platforms, allows id=0 for redirecting
@app.route('/category/', defaults={'id': None})
@app.route('/category/<int:id>')
def category(id):
    categories = None
    if id is None:
        return redirect("/category/0")

    # query data via helper function
    categories = execute_query(models.Categories, "SELECT", id=id)

    if id == 0:  # template all if id is 0 else individual
        return render_template('all_categories.html', categories=categories)
    else:
        return render_template('individual_categories.html', categories=categories)


@app.route('/search', methods=["GET", "POST"])
def search():
    games = None
    query = request.args.get('query', '').strip()  # Obtain input
    if query:
        exact_matches = execute_query(models.Games, filters={"GameName": query})
        if exact_matches:  # Should return 1 output
            return redirect("game/" + str(exact_matches[0].GameID))

        games = execute_query(models.Games, search_fields={"GameName": query})
    else:  # Grab all if no input
        games = execute_query(models.Games)
    return render_template('all_games.html', games=games)


@app.route('/rate_game/<int:id>', methods=["POST"])
def rate_game(id):
    user_id = session.get("AccountID")
    if not user_id:  # Ensures only logged-in users can rate
        abort(401)

    value = int(request.form.get("rating", 0))  # Grab rating

    # Changes rating if rating already exists
    existing = execute_query(models.Reviews, filters={"UserID": user_id, "GameID": id})

    if value == 0:
        if existing:  # Deletes review if rating = 0
            execute_query(models.Reviews, operation="DELETE", id=existing[0].ReviewID)
    elif existing:  # Updates if rating exists
        execute_query(models.Reviews, operation="UPDATE", id=existing[0].ReviewID, data={"Rating": value})
    else:  # Creates new rating for user and game
        execute_query(models.Reviews, operation="INSERT", data={"UserID": user_id, "GameID": id, "Rating": value})

    # Redirects to current game page
    return redirect("/game/" + str(id))
