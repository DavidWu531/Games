from datetime import datetime
from werkzeug.exceptions import HTTPException
from werkzeug.utils import secure_filename
from app import app
from flask import render_template, abort, redirect, session, request, flash
from flask_sqlalchemy import SQLAlchemy
import os
from flask_bcrypt import Bcrypt
from sqlalchemy import exc, asc, desc

basedir = os.path.abspath(os.path.dirname(__file__))
db = SQLAlchemy()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, "games.db")
db.init_app(app)
bcrypt = Bcrypt()
app.secret_key = os.urandom(12)


import app.models as models  # noqa: E402
from app.forms import AdminGameForm, LoginForm, RegisterForm  # noqa: E402


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
                    if isinstance(value, list):  # Match any in list
                        query = query.filter(column.in_(value))
                    elif isinstance(value, str):  # Case-insensitive match
                        query = query.filter(column.ilike(f"{value}"))
                    else:  # Exact match
                        query = query.filter(column == value)
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
            if not isinstance(data, dict) or not data:
                abort(400, description="No updated data provided")
            record = None
            if id is not None:
                record = model.query.get_or_404(id)  # Get existing record
            elif filters:
                record = model.query.filter_by(**filters).first()
                if not record:
                    abort(400, description="Record not found")
            else:
                abort(400, description="No ID or filters provided")
            for key, value in data.items():
                setattr(record, key, value)  # Update each field
            db.session.commit()
            return [record]  # Return updated record

        # DELETE OPERATION
        elif operation == "DELETE":
            if id is None and not filters:
                abort(400, description="ID or filters must be provided")

            if id is not None:
                record = model.query.get_or_404(id)  # Get existing record
                db.session.delete(record)

            elif filters:
                query = model.query
                for column_name, value in filters.items():
                    column = getattr(model, column_name)
                    if isinstance(value, list):
                        query = query.filter(column.in_(value))
                    else:
                        query = query.filter(column == value)
                query.delete(synchronize_session=False)
            db.session.commit()
            return []  # Returns empty list, indicates data deleted

        # NAVIGATION OPERATION
        elif operation == "NAVIGATION":
            if id is None:
                abort(400, "ID not provided")

            # Get first column in primary key of model
            id_column = list(model.__table__.primary_key.columns)[0]
            id_attr_name = id_column.name  # Name of column as string

            # Grab first row less than current row
            prev_row = model.query.filter(id_column < id).order_by(desc(id_column)).first()
            # Grab first row bigger than current row
            next_row = model.query.filter(id_column > id).order_by(asc(id_column)).first()
            return {
                # Get ID column value based on name of primary key
                "prev_id": getattr(prev_row, id_attr_name) if prev_row else 0,
                "next_id": getattr(next_row, id_attr_name) if next_row else None
            }  # 0 indicates no previous item (e.g., show 'Back to List'), None means no next item

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

    except Exception as e:
        db.session.rollback()
        abort(500, description=f"Internal server error: {str(e)}")


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
            flash("Invalid username or password", "error")

    return render_template('login.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        temp_username = form.username.data
        temp_password = form.password.data

        # Hash password, salt built-in
        hashed_password = bcrypt.generate_password_hash(temp_password).decode('utf-8')
        data = {
            "AccountUsername": temp_username,
            "AccountPassword": hashed_password
        }

        try:
            # Attempt to create new user
            execute_query(models.Accounts, operation="INSERT", data=data)
            flash("Account created successfully, you may log in", "success")
            return redirect('/login')
        except Exception as e:  # noqa F841
            # Rollback in case of database error
            db.session.rollback()
            # Handle non-uniqueness errors only now
            flash("An error occurred, please try again later", "error")

    return render_template('register.html', form=form)


@app.route('/logout')
def logout():
    if "AccountID" in session:
        session.pop("AccountID", None)
    return redirect('/game/0')


@app.route('/delete')
def delete():
    user_id = session.get("AccountID")
    if user_id is None:
        return redirect('/game/0')

    try:
        execute_query(models.Accounts, operation="DELETE", id=user_id)
    except Exception as e:  # noqa F841
        print("An error occurred, please try again later")
    else:
        session.pop("AccountID", None)
    return redirect('/game/0')


@app.route('/dashboard')
def dashboard():
    if "AccountID" in session:
        account = execute_query(models.Accounts, operation="SELECT", filters={"AccountID": session["AccountID"]})
        if account:
            account = account[0]
            username = account.AccountUsername
            is_admin = account.AccountIsAdmin

            if is_admin:
                return redirect("/admin")

            return render_template('dashboard.html', username=username, is_admin=is_admin)
    else:
        return redirect('/login')


@app.route('/admin')
def admin():
    if "AccountID" in session:
        account = execute_query(models.Accounts, operation="SELECT", filters={"AccountID": session["AccountID"]})
        if account:
            account = account[0]
            username = account.AccountUsername
            is_admin = account.AccountIsAdmin

            if not is_admin:
                return redirect("/dashboard")

            return render_template('dashboard.html', username=username, is_admin=is_admin)

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
@app.route('/game/', defaults={'id': None}, methods=['GET', 'POST'])
@app.route('/game/<int:id>', methods=['GET', 'POST'])
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

        # Check if user is admin
        is_admin = 0
        if "AccountID" in session:
            account = execute_query(models.Accounts, operation="SELECT", filters={"AccountID": session["AccountID"]})
            if account:
                account = account[0]
                is_admin = account.AccountIsAdmin

        # Load platforms for platform-specific details
        chosen_platform = request.form.get("platforms", "PC")
        platform_id = {"PC": 1, "PlayStation": 2, "Xbox": 3}
        platform_key = {"PC": ["Minimum", "Recommended"], "PlayStation": ["Normal"], "Xbox": ["Normal"]}
        platform_detail = execute_query(models.GamePlatformDetails,
                                        operation="SELECT",
                                        filters={"GameID": id, "PlatformID": int(platform_id[chosen_platform])})
        system_detail = execute_query(models.SystemRequirements,
                                      operation="SELECT",
                                      filters={"GameID": id, "Type": platform_key[chosen_platform],
                                               "PlatformID": platform_id[chosen_platform]})

        # Miscellaneous: Get next and previous GameID for navigation
        nav_ids = execute_query(models.Games, operation="NAVIGATION", id=id)
        return render_template('individual_games.html', games=games, user_rating=user_rating, is_admin=is_admin,
                               chosen_platform=chosen_platform, platform_detail=platform_detail,
                               system_detail=system_detail, prev_id=nav_ids["prev_id"], next_id=nav_ids["next_id"])


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

    if id == 0:
        return redirect("/game/0")

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


@app.route('/admin/game/add', methods=["GET", "POST"])
def add_game():
    # Registered users only
    if "AccountID" not in session:
        return redirect("/login")

    # Grab user
    user = execute_query(models.Accounts, operation="SELECT", filters={"AccountID": session["AccountID"]})
    if not user:
        return redirect("/dashboard")
    elif user:
        user = user[0]
        if not user.AccountIsAdmin:
            # Admin access only
            return redirect("/dashboard")

    form = AdminGameForm()
    form.submit.label.text = "Add Game"

    # Load all platforms and categories
    all_categories = execute_query(models.Categories, operation="SELECT")
    form.categories.choices = [(category.CategoryID, category.CategoryName) for category in all_categories]
    all_platforms = execute_query(models.Platforms, operation="SELECT")
    form.platforms.choices = [(platform.PlatformID, platform.PlatformName) for platform in all_platforms]

    # Check if all requirements are met
    if form.validate_on_submit():
        image_filename = None
        if form.game_image.data and hasattr(form.game_image.data, "filename"):
            filename = secure_filename(form.game_image.data.filename)
            form.game_image.data.save(os.path.join("app", "static", "images", filename))
            image_filename = filename

        # Insert game data
        execute_query(models.Games, operation="INSERT", data={
            "GameName": form.game_name.data,
            "GameDescription": form.game_description.data,
            "GameDeveloper": form.game_developer.data,
            "GameImage": image_filename
        })

        # Grab ID of new game
        new_game = execute_query(models.Games, operation="SELECT", filters={"GameName": form.game_name.data})
        new_game_id = new_game[0].GameID

        # Insert many-to-many relationship IDs
        for category_id in form.categories.data:
            execute_query(models.GameCategories, operation="INSERT", data={"GameID": new_game_id, "CategoryID": category_id})

        for platform_id in form.platforms.data:
            base_game_data = {"GameID": new_game_id, "PlatformID": platform_id}
            execute_query(models.GamePlatforms, operation="INSERT", data=base_game_data)

            # PC platform
            if platform_id == 1:
                # Get both minimum and recommended requirements
                min_req_data = {"Type": "Minimum",
                                "OS": form.min_pc_os.data or "N/A",
                                "RAM": form.min_pc_ram.data or "N/A",
                                "CPU": form.min_pc_cpu.data or "N/A",
                                "GPU": form.min_pc_gpu.data or "N/A",
                                "Storage": form.min_pc_storage.data or "N/A"
                                }
                rec_req_data = {"Type": "Recommended",
                                "OS": form.rec_pc_os.data or "N/A",
                                "RAM": form.rec_pc_ram.data or "N/A",
                                "CPU": form.rec_pc_cpu.data or "N/A",
                                "GPU": form.rec_pc_gpu.data or "N/A",
                                "Storage": form.rec_pc_storage.data or "N/A"
                                }

                # Insert both types
                execute_query(models.SystemRequirements, operation="INSERT", data=base_game_data | min_req_data)
                execute_query(models.SystemRequirements, operation="INSERT", data=base_game_data | rec_req_data)
            # Console platform
            else:
                # Get console data using ternary operations
                normal_req_data = {"Type": "Normal",
                                   "OS": (form.ps_os.data if platform_id == 2 else form.xb_os.data) or "N/A",
                                   "RAM": "N/A",
                                   "CPU": "N/A",
                                   "GPU": "N/A",
                                   "Storage": (form.ps_storage.data if platform_id == 2 else form.xb_storage.data) or "N/A"
                                   }
                execute_query(models.SystemRequirements, operation="INSERT", data=base_game_data | normal_req_data)

            # Get raw data using ternary operations for PlatformID
            raw_price = (form.pc_price.data if platform_id == 1 else
                         form.ps_price.data if platform_id == 2 else
                         form.xb_price.data)
            raw_release_date = (form.pc_release_date.data if platform_id == 1 else
                                form.ps_release_date.data if platform_id == 2 else
                                form.xb_release_date.data)

            # Load into dictionary of proper data type
            price_data = {
                "Price": float(raw_price) if raw_price not in [None, ""] else -1,
                "ReleaseDate": raw_release_date.isoformat() if raw_release_date else "1900-01-01"
            }
            execute_query(models.GamePlatformDetails, operation="INSERT", data=base_game_data | price_data)

        # Redirect to game upon adding
        flash(f"Game {new_game[0].GameName} created successfully", "success")
        return redirect("/game/" + str(new_game_id))
    else:
        print("Form errors:", form.errors)

    return render_template("admin.html", form=form, form_action="/admin/game/add", form_type="INSERT")


@app.route('/admin/game/update/', defaults={'id': None}, methods=["GET", "POST"])
@app.route('/admin/game/update/<int:id>', methods=["GET", "POST"])
def update_game(id):
    # Registered users only
    if "AccountID" not in session:
        return redirect("/login")

    # Redirect users to show all games (ID 0 doesn't exist)
    if id == 0:
        return redirect("/game/0")

    # Grab user
    user = execute_query(models.Accounts, operation="SELECT", filters={"AccountID": session["AccountID"]})
    if not user:
        return redirect("/dashboard")
    elif user:
        user = user[0]
        if not user.AccountIsAdmin:
            # Admin access only
            return redirect("/dashboard")

    # Check game existence
    game = execute_query(models.Games, operation="SELECT", id=id)
    if not game:
        abort(404, description="Game Not Found")
    game = game[0]
    form = AdminGameForm(obj=game)
    form.submit.label.text = "Update Game"

    # Load all categories and platforms
    all_categories = execute_query(models.Categories, operation="SELECT")
    form.categories.choices = [(category.CategoryID, category.CategoryName) for category in all_categories]
    all_platforms = execute_query(models.Platforms, operation="SELECT")
    form.platforms.choices = [(platform.PlatformID, platform.PlatformName) for platform in all_platforms]

    # Get existing data on load (GET)
    if request.method == "GET":
        # Load existing game data (Games table)
        game = execute_query(models.Games, operation="SELECT", id=id)[0]
        form.game_name.data = game.GameName
        form.game_description.data = game.GameDescription
        form.game_developer.data = game.GameDeveloper

        # Check all categories and platforms that were already checked
        chosen_categories = execute_query(models.GameCategories, operation="SELECT", filters={"GameID": id})
        form.categories.data = [category.CategoryID for category in chosen_categories]

        chosen_platforms = execute_query(models.GamePlatforms, operation="SELECT", filters={"GameID": id})
        form.platforms.data = [platform.PlatformID for platform in chosen_platforms]

        # Execute queries based on platforms
        for platform_id in form.platforms.data:
            # Load existing system requirement and price detail data
            system_requirement = execute_query(models.SystemRequirements, operation="SELECT", filters={"GameID": id, "PlatformID": platform_id})
            price_detail = execute_query(models.GamePlatformDetails, operation="SELECT", filters={"GameID": id, "PlatformID": platform_id})
            if price_detail:
                price_detail = price_detail[0]

            # PC platform
            if platform_id == 1:
                # Load checked requirement
                min_req = next((requirement for requirement in system_requirement if requirement.Type == "Minimum"), None)
                rec_req = next((requirement for requirement in system_requirement if requirement.Type == "Recommended"), None)

                # Load system requirements based on type of requirement
                if min_req:
                    form.min_pc_os.data = min_req.OS if min_req.OS != "N/A" else None
                    form.min_pc_ram.data = min_req.RAM if min_req.RAM != "N/A" else None
                    form.min_pc_cpu.data = min_req.CPU if min_req.CPU != "N/A" else None
                    form.min_pc_gpu.data = min_req.GPU if min_req.GPU != "N/A" else None
                    form.min_pc_storage.data = min_req.Storage if min_req.Storage != "N/A" else None

                if rec_req:
                    form.rec_pc_os.data = rec_req.OS if rec_req.OS != "N/A" else None
                    form.rec_pc_ram.data = rec_req.RAM if rec_req.RAM != "N/A" else None
                    form.rec_pc_cpu.data = rec_req.CPU if rec_req.CPU != "N/A" else None
                    form.rec_pc_gpu.data = rec_req.GPU if rec_req.GPU != "N/A" else None
                    form.rec_pc_storage.data = rec_req.Storage if rec_req.Storage != "N/A" else None

                # Load existing price details (GamePlatformDetails)
                form.pc_price.data = float(price_detail.Price) if price_detail and price_detail is not None else None
                form.pc_release_date.data = datetime.strptime(price_detail.ReleaseDate, "%Y-%m-%d").date() if price_detail and price_detail.ReleaseDate else None
            elif platform_id == 2:
                # Ditto for PS
                normal_requirement = next((requirement for requirement in system_requirement if requirement.Type == "Normal"), None)
                if normal_requirement:
                    form.ps_os.data = normal_requirement.OS if normal_requirement.OS != "N/A" else None
                    form.ps_storage.data = normal_requirement.Storage if normal_requirement.Storage != "N/A" else None

                form.ps_price.data = float(price_detail.Price) if price_detail and price_detail.Price is not None else None
                form.ps_release_date.data = datetime.strptime(price_detail.ReleaseDate, "%Y-%m-%d").date() if price_detail and price_detail.ReleaseDate else None
            elif platform_id == 3:
                # Ditto for XB
                normal_requirement = next((requirement for requirement in system_requirement if requirement.Type == "Normal"), None)
                if normal_requirement:
                    form.xb_os.data = normal_requirement.OS if normal_requirement.OS != "N/A" else None
                    form.xb_storage.data = normal_requirement.Storage if normal_requirement.Storage != "N/A" else None

                form.xb_price.data = float(price_detail.Price) if price_detail and price_detail.Price is not None else None
                form.xb_release_date.data = datetime.strptime(price_detail.ReleaseDate, "%Y-%m-%d").date() if price_detail and price_detail.ReleaseDate else None

    if form.validate_on_submit():
        if form.game_image.data and hasattr(form.game_image.data, "filename"):
            filename = secure_filename(form.game_image.data.filename)
            form.game_image.data.save(os.path.join("app", "static", "images", filename))
            image_filename = filename
        else:
            image_filename = game.GameImage

        # Update existing game data
        execute_query(models.Games, operation="UPDATE", id=id, data={
            "GameName": form.game_name.data,
            "GameDescription": form.game_description.data,
            "GameDeveloper": form.game_developer.data,
            "GameImage": image_filename
        })

        # Delete and reinsert M2M GameCategories table
        execute_query(models.GameCategories, operation="DELETE", filters={"GameID": id})
        for category_id in form.categories.data:
            execute_query(models.GameCategories, operation="INSERT", data={"GameID": id, "CategoryID": category_id})

        # Get old PlatformIDs and new PlatformIDs
        current_platforms = execute_query(models.GamePlatforms, operation="SELECT", filters={"GameID": id})
        current_platform_ids = [platform.PlatformID for platform in current_platforms]
        new_platform_ids = form.platforms.data

        # Remove all removed IDs from respective tables
        remove_platforms = set(current_platform_ids) - set(new_platform_ids)
        for platform_id in remove_platforms:
            execute_query(models.GamePlatforms, operation="DELETE", filters={"GameID": id, "PlatformID": platform_id})
            execute_query(models.SystemRequirements, operation="DELETE", filters={"GameID": id, "PlatformID": platform_id})
            execute_query(models.GamePlatformDetails, operation="DELETE", filters={"GameID": id, "PlatformID": platform_id})

        # Update data based on PlaformID
        for platform_id in form.platforms.data:
            base_game_data = {"GameID": id, "PlatformID": platform_id}

            # Insert new PlatformID if doesn't exist in old
            if platform_id not in current_platform_ids:
                execute_query(models.GamePlatforms, operation="INSERT", data=base_game_data)

            # PC platform
            if platform_id == 1:
                # Check if minimum requirements exist
                min_req_exist = execute_query(models.SystemRequirements, operation="SELECT", filters={
                    "GameID": id, "PlatformID": platform_id, "Type": "Minimum"})
                min_req_data = {"Type": "Minimum",
                                "OS": form.min_pc_os.data or "N/A",
                                "RAM": form.min_pc_ram.data or "N/A",
                                "CPU": form.min_pc_cpu.data or "N/A",
                                "GPU": form.min_pc_gpu.data or "N/A",
                                "Storage": form.min_pc_storage.data or "N/A"
                                }

                # Update if minimum requirements exist, otherwise insert
                if min_req_exist:
                    execute_query(models.SystemRequirements, operation="UPDATE", id=min_req_exist[0].RequirementsID, data=min_req_data)
                else:
                    execute_query(models.SystemRequirements, operation="INSERT", data=base_game_data | min_req_data)

                # Ditto for recommended requirement existence
                rec_req_exist = execute_query(models.SystemRequirements, operation="SELECT", filters={
                    "GameID": id, "PlatformID": platform_id, "Type": "Recommended"})
                rec_req_data = {"Type": "Recommended",
                                "OS": form.rec_pc_os.data or "N/A",
                                "RAM": form.rec_pc_ram.data or "N/A",
                                "CPU": form.rec_pc_cpu.data or "N/A",
                                "GPU": form.rec_pc_gpu.data or "N/A",
                                "Storage": form.rec_pc_storage.data or "N/A"
                                }

                # Ditto for data update/insert
                if rec_req_exist:
                    execute_query(models.SystemRequirements, operation="UPDATE", id=rec_req_exist[0].RequirementsID, data=rec_req_data)
                else:
                    execute_query(models.SystemRequirements, operation="INSERT", data=base_game_data | rec_req_data)
            # Console platforms
            else:
                # Check if normal requirements exist
                normal_req_exist = execute_query(models.SystemRequirements, operation="SELECT", filters={
                    "GameID": id, "PlatformID": platform_id, "Type": "Normal"})
                normal_req_data = {"Type": "Normal",
                                   "OS": (form.ps_os.data if platform_id == 2 else form.xb_os.data) or "N/A",
                                   "RAM": "N/A",
                                   "CPU": "N/A",
                                   "GPU": "N/A",
                                   "Storage": (form.ps_storage.data if platform_id == 2 else form.xb_storage.data) or "N/A"
                                   }

                # Update if exist, otherwise insert
                if normal_req_exist:
                    execute_query(models.SystemRequirements, operation="UPDATE", id=normal_req_exist[0].RequirementsID, data=normal_req_data)
                else:
                    execute_query(models.SystemRequirements, operation="INSERT", data=base_game_data | normal_req_data)

            # Check if price details exist
            price_detail_exist = execute_query(models.GamePlatformDetails, operation="SELECT", filters={
                "GameID": id, "PlatformID": platform_id})

            # Get raw data using ternary operations for PlatformID
            raw_price = (form.pc_price.data if platform_id == 1 else
                         form.ps_price.data if platform_id == 2 else
                         form.xb_price.data)
            raw_release_date = (form.pc_release_date.data if platform_id == 1 else
                                form.ps_release_date.data if platform_id == 2 else
                                form.xb_release_date.data)

            # Load into dictionary of proper data type
            price_data = {
                "Price": float(raw_price) if raw_price not in [None, ""] else -1,
                "ReleaseDate": raw_release_date.isoformat() if raw_release_date else "1900-01-01"
            }

            # Update if exist, otherwise insert
            if price_detail_exist:
                execute_query(models.GamePlatformDetails, operation="UPDATE", filters={"GameID": id, "PlatformID": platform_id}, data=price_data)
            else:
                execute_query(models.GamePlatformDetails, operation="INSERT", data=base_game_data | price_data)

        # Redirect to game upon updating
        flash(f"Game {form.game_name.data} updated successfully", "success")
        return redirect(f"/game/{id}")
    else:
        print("Form errors:", form.errors)

    return render_template("admin.html", form=form, form_action=f"/admin/game/update/{id}", form_type="UPDATE")


@app.route("/admin/game/delete/<int:id>")
def delete_game(id):
    game = None
    if "AccountID" not in session:
        return redirect("/login")

    if id == 0:
        return redirect("/game/0")

    user = execute_query(models.Accounts, operation="SELECT", filters={"AccountID": session["AccountID"]})
    if not user:
        return redirect("/dashboard")
    elif user:
        user = user[0]
        if not user.AccountIsAdmin:
            return redirect("/dashboard")

    game = execute_query(models.Games, operation="SELECT", id=id)
    execute_query(models.Games, operation="DELETE", id=game.GameID)
    flash("Game Deleted", "success")
    return redirect("/game/0")
