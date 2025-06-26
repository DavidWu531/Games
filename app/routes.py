from werkzeug.exceptions import HTTPException
from app import app
from flask import render_template, abort, redirect, session, request
from flask_sqlalchemy import SQLAlchemy
import os
from flask_bcrypt import Bcrypt
from sqlalchemy import exc

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
                record = model.query.get(id)  # Auto-404 if none found
                return [record] if record else abort(404, description="Data not found")  # Return as list for display in HTML

            # Case 2: Exact filtering, case-insensitive
            elif filters:  # Get queried results based on input
                query = model.query
                for column_name, value in filters.items():
                    column = getattr(model, column_name)
                    query = query.filter(column.ilike(f"{value}"))
                return query.all() or []

            # Case 3: Partial search
            elif search_fields:  # Get all results with input in query
                query = model.query
                for column_name, value in search_fields.items():
                    column = getattr(model, column_name)
                    query = query.filter(column.ilike(f"%{value}%"))  # Partial case-insensitive match
                return query.all() or []

            # Case 4: Get all
            else:
                return model.query.all() or []

        # INSERT OPERATION
        elif operation == "INSERT":
            if not data:
                abort(400, description="Cannot insert data")
            record = model(**data)  # Create new record
            db.session.add(record)
            db.session.commit()
            return [record]  # Return new record

        # UPDATE OPERATION
        elif operation == "UPDATE":
            if not data or not id:
                abort(400, description="Not all fields were filled in")
            record = model.query.get_or_404(id)  # Get existing record
            for key, value in data.items():
                setattr(record, key, value)  # Update each field
            db.session.commit()
            return [record]  # Return updated record

        # DELETE OPERATION
        elif operation == "DELETE":
            if id is None:
                abort(400, description="ID not provided")
            record = model.query.get_or_404(id)
            db.session.delete(record)
            db.session.commit()
            return []  # Returns empty list, indicates data deleted
        else:
            abort(400, description="Invalid operation")

    # ERROR HANDLING
    except OverflowError:
        abort(400, description="Invalid ID format")  # More appropriate than 404

    except exc.NoResultFound:
        abort(404, description="Data not found")

    except exc.IntegrityError as e:
        db.session.rollback()
        if "unique constraint" in str(e).lower():
            abort(409, description="Duplicate entry detected")  # Specific 409 for conflicts
        abort(400, description="Database constraint violation")

    except exc.OperationalError:
        db.session.rollback()
        abort(503, description="Database service unavailable")  # For connection issues

    except exc.SQLAlchemyError as e:
        db.session.rollback()
        abort(500, description=f"Database operation failed: {str(e)}")

    except HTTPException:
        raise  # Re-raise existing HTTP errors

    except Exception:
        db.session.rollback()
        abort(500, description="Internal server error")


# All errors use the same render template, but their code, title, and message are different when rendered
@app.errorhandler(HTTPException)
def handle_http_errors(e):
    error_responses = {
        400: {
            "title": "Bad Request",
            "message": "Invalid request parameters"
        },
        401: {
            "title": "Unauthorized",
            "message": "Authentication required"
        },
        403: {
            "title": "Forbidden",
            "message": "You don't have permission"
        },
        404: {
            "title": "Not Found",
            "message": "Resource not found"
        },
        409: {
            "title": "Conflict",
            "message": "Data conflict detected"
        },
        500: {
            "title": "Internal Server Error",
            "message": "An unexpected error occurred"
        },
        503: {
            "title": "Service Unavailable",
            "message": "Database maintenance in progress"
        }
    }

    # Get the response for the specific error code or use a default
    response = error_responses.get(e.code, {"title": "HTTP Error", "message": getattr(e, "description", str(e))})

    # Allow custom messages from abort() calls to override defaults
    if hasattr(e, "description"):
        response["message"] = e.description

    # Code 404 overrides default to "Page Not Found"
    if e.code == 404:
        error_responses[404]["message"] = "Page Not Found"

    return render_template("error.html", code=e.code, title=response["title"], message=response["message"]), e.code


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # Query database with matching username
        users = execute_query(models.Accounts, operation="SELECT", filters={"AccountUsername": form.username.data})

        # Usernames are unique so get first or get none
        user = users[0] if users else None

        # Check if password matches hashed version
        if user and bcrypt.check_password_hash(user.AccountPassword, form.password.data):
            session['AccountID'] = user.AccountID  # Logs user in
            return redirect("/dashboard")
        else:
            # Fail log in, show error message and reload page
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
            # Attempt to create new user
            execute_query(models.Accounts, operation="INSERT", data=data)
            return redirect('/login')
        except Exception as e:
            # Rollback in case of database error
            db.session.rollback()

            # Handle constraint violation (UNIQUE constraint)
            if 'UNIQUE constraint failed' in str(e):
                form.username.errors.append("Account already exists")
            else:
                # Other database errors
                form.username.errors.append("An error occurred, please try again later")
            return render_template("register.html", form=form)

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

    if id == 0:  # Template all if id is 0 else individual
        # Query data via helper function
        platforms = execute_query(models.Platforms, operation="SELECT", id=0)
        return render_template('all_platforms.html', platforms=platforms)
    else:
        platform = execute_query(models.Platforms, operation="SELECT", id=id)
        games = platform[0].games  # Returns all games under specific category
        return render_template('individual_platforms.html', platform=platform[0], games=games)


# Displays platforms, allows id=0 for redirecting
@app.route('/game/', defaults={'id': None})
@app.route('/game/<int:id>')
def game(id):
    games = None
    if id is None:
        return redirect("/game/0")

    # Query data via helper function
    games = execute_query(models.Games, "SELECT", id=id)

    if id == 0:  # Template all if id is 0 else individual
        return render_template('all_games.html', games=games)
    else:  # Rating is restricted to registered users only
        user_rating = None
        user_id = session.get("AccountID")  # Check if user is logged in
        if user_id:
            user_rating = execute_query(models.Reviews, filters={"UserID": user_id, "GameID": id})
            if user_rating:  # Get rating based on current game and current user
                user_rating = user_rating[0].Rating

        return render_template('individual_games.html', games=games, user_rating=user_rating)


# Displays platforms, allows id=0 for redirecting
@app.route('/category/', defaults={'id': None})
@app.route('/category/<int:id>')
def category(id):
    categories = None
    if id is None:
        return redirect("/category/0")

    if id == 0:  # Template all if id is 0 else individual
        # Query data via helper function
        categories = execute_query(models.Categories, "SELECT", id=0)
        return render_template('all_categories.html', categories=categories)
    else:
        # Query data via helper function
        category = execute_query(models.Categories, "SELECT", id=id)
        games = category[0].games  # Returns all games under specific category
        return render_template('individual_categories.html', category=category[0], games=games)


@app.route('/search', methods=["GET", "POST"])
def search():
    games = None
    query = request.args.get('query', '').strip()  # Obtain input
    if query:
        exact_matches = execute_query(models.Games, filters={"GameName": query})
        if exact_matches:  # Redirect to game page if exact
            return redirect("game/" + str(exact_matches[0].GameID))
        # Get all data containing that input
        games = execute_query(models.Games, search_fields={"GameName": query})
    else:  # Grab all if no input
        games = execute_query(models.Games)
    return render_template('all_games.html', games=games)


@app.route('/rate_game/<int:id>', methods=["POST"])
def rate_game(id):
    user_id = session.get("AccountID")
    if not user_id:  # Ensures only logged-in users can rate
        abort(401, "Rating is restricted to logged-in users only")

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
