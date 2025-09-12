from flask_wtf import FlaskForm
from wtforms import DateField, DecimalField, FileField, StringField, PasswordField, SubmitField, \
    ValidationError, TextAreaField, SelectMultipleField, widgets
from wtforms.validators import DataRequired, Length, Optional


import app.routes as routes
import app.models as models

ALLOWED_EXTENSIONS = ["jpg", "png", "jpeg", "webp"]
MAX_IMAGE_SIZE = 5 * 1024 * 1024


def at_least_one_checked(form, field):
    if not field.data:
        raise ValidationError("Please select at least 1 checkbox")


def unit_validation(form, field):
    if field.data:
        value = field.data.strip()
        has_digit = any(character.isdigit() for character in value)
        has_letter = any(character.isalpha() for character in value)

        if not (has_digit and has_letter):
            raise ValidationError("Storage/RAM size must contain numbers and units")

        if not value[0].isdigit():
            raise ValidationError("Storage/RAM size must start with a number")

        unit_part = "".join([character for character in value if character.isalpha()]).upper()
        valid_units = ["GB", "TB", "MB", "KB"]
        if unit_part not in valid_units:
            raise ValidationError("Invalid Units: Only Accept GB, TB, MB, and KB")

        letter_found = False
        for character in value:
            if character.isalpha():
                letter_found = True
            elif character.isdigit() and letter_found:
                raise ValidationError("Invalid Format: Numbers found after letters")


def validate_image(form, field):
    file = field.data
    if not file:
        return
    filename = file.filename.lower()
    if "." not in filename or filename.rsplit(".", 1)[1] not in ALLOWED_EXTENSIONS:
        raise ValidationError("Invalid file types: Only Accept jpg, png, and webp")

    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    if size > MAX_IMAGE_SIZE:
        raise ValidationError("File too large: Max 5MB")


class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class LoginForm(FlaskForm):
    username = StringField('AccountUsername',
                           validators=[DataRequired()],
                           render_kw={"placeholder": "Enter Username"}
                           )
    password = PasswordField('AccountPassword',
                             validators=[DataRequired()],
                             render_kw={"placeholder": "Enter Password"}
                             )
    submit = SubmitField("Login")


class RegisterForm(FlaskForm):
    username = StringField('AccountUsername',
                           validators=[DataRequired(),
                                       Length(min=4,
                                              max=20,
                                              message="Username must be between 4 and 20 characters")],
                           render_kw={"placeholder": "Create a username"})
    password = PasswordField('AccountPassword',
                             validators=[DataRequired(),
                                         Length(min=6,
                                                message="Password must be at least 6 characters")],
                             render_kw={"placeholder": "Create a password"})
    submit = SubmitField("Register")

    def validate_username(self, field):
        username = field.data

        # Checks if username contains other characters besides letters and numbers
        if not username.isalnum() and username.isascii():
            raise ValidationError("Username can only contain alphanumeric characters")

        # Checks if password contains spaces since they're not recommended
        if " " in username:
            raise ValidationError("Username cannot contain spaces")

        existing_user = routes.execute_query(models.Accounts, operation="SELECT", filters={"AccountUsername": username})
        if existing_user:
            raise ValidationError("Account already exists")


class AdminGameForm(FlaskForm):
    game_name = StringField("Game Name", validators=[DataRequired()])
    game_description = TextAreaField("Description", validators=[Optional()], render_kw={"cols": 50, "rows": 10, "class": "uneditable"})
    game_developer = StringField("Developer", validators=[Optional()])
    game_image = FileField("Game Image", validators=[validate_image])

    categories = MultiCheckboxField("Categories", coerce=int, validators=[at_least_one_checked])
    platforms = MultiCheckboxField("Platforms", coerce=int, validators=[at_least_one_checked])

    min_pc_os = StringField("OS", validators=[Optional()], render_kw={"placeholder": "Enter OS (E.g. Windows 11)"})
    min_pc_ram = StringField("RAM", validators=[Optional(), unit_validation], render_kw={"placeholder": "Enter RAM (E.g. 16GB)"})
    min_pc_cpu = StringField("CPU", validators=[Optional()], render_kw={"placeholder": "Enter CPU (E.g. Intel i5-12400F)"})
    min_pc_gpu = StringField("GPU", validators=[Optional()], render_kw={"placeholder": "Enter GPU (E.g. NVIDIA RTX 3070 Ti)"})
    min_pc_storage = StringField("Storage", validators=[Optional(), unit_validation], render_kw={"placeholder": "Enter Storage (E.g. 50GB)"})

    rec_pc_os = StringField("OS", validators=[Optional()], render_kw={"placeholder": "Enter OS (E.g. Windows 11)"})
    rec_pc_ram = StringField("RAM", validators=[Optional(), unit_validation], render_kw={"placeholder": "Enter RAM (E.g. 16GB)"})
    rec_pc_cpu = StringField("CPU", validators=[Optional()], render_kw={"placeholder": "Enter CPU (E.g. Intel i5-12400F)"})
    rec_pc_gpu = StringField("GPU", validators=[Optional()], render_kw={"placeholder": "Enter GPU (E.g. NVIDIA RTX 3070 Ti)"})
    rec_pc_storage = StringField("Storage", validators=[Optional(), unit_validation], render_kw={"placeholder": "Enter Storage (E.g. 50GB)"})

    pc_price = DecimalField("Price (NZD)", places=2, validators=[Optional()], render_kw={"placeholder": "Enter Price (E.g. 1.00)"})
    pc_release_date = DateField("Release Date", format="%Y-%m-%d", validators=[Optional()])

    ps_os = StringField("OS", validators=[Optional()], render_kw={"placeholder": "Enter OS (E.g. PS5)"})
    ps_storage = StringField("Storage", validators=[Optional(), unit_validation], render_kw={"placeholder": "Enter Storage (E.g. 50GB)"})
    ps_price = DecimalField("Price (NZD)", places=2, validators=[Optional()], render_kw={"placeholder": "Enter Price (E.g. 1.00)"})
    ps_release_date = DateField("Release Date", format="%Y-%m-%d", validators=[Optional()])

    xb_os = StringField("OS", validators=[Optional()], render_kw={"placeholder": "Enter OS (E.g. XBOX Series X)"})
    xb_storage = StringField("Storage", validators=[Optional(), unit_validation], render_kw={"placeholder": "Enter Storage (E.g. 50GB)"})
    xb_price = DecimalField("Price (NZD)", places=2, validators=[Optional()], render_kw={"placeholder": "Enter Price (E.g. 1.00)"})
    xb_release_date = DateField("Release Date", format="%Y-%m-%d", validators=[Optional()])

    submit = SubmitField("Add Game")

    def validate_game_name(self, field):
        game_name = field.data.strip()
        existing_game = routes.execute_query(models.Games, operation="SELECT", filters={"GameName": game_name})
        if existing_game:
            if not hasattr(self, "game_id") or existing_game[0].GameID != self.game_id:
                raise ValidationError("Game name already exists")
