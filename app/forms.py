from flask_wtf import FlaskForm
from wtforms import DateField, DecimalField, StringField, PasswordField, SubmitField, \
    ValidationError, TextAreaField, SelectMultipleField, widgets, RadioField
from wtforms.validators import DataRequired, Length, Optional, InputRequired


import app.routes as routes
import app.models as models


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

    def validate_password(self, field):
        password = field.data

        if " " in password:
            raise ValidationError("Password cannot contain spaces")


class AdminGameForm(FlaskForm):
    game_name = StringField("Game Name", validators=[DataRequired()])
    game_description = TextAreaField("Description", validators=[Optional()])
    game_developer = StringField("Developer", validators=[Optional()])
    # game_image = StringField("Image URL", validators=[Optional()])

    categories = MultiCheckboxField("Categories", coerce=int, validators=[InputRequired()])
    platforms = MultiCheckboxField("Platforms", coerce=int, validators=[InputRequired()])

    release_date = DateField("Release Date", format="%Y-%m-%d", validators=[Optional()])
    price = DecimalField("Price (NZD)", places=2, validators=[Optional()])

    pc_type = RadioField("Requirement Type", choices=[
        ("Minimum", "Minimum"), ("Recommended", "Recommended")], validators=[Optional()])
    pc_os = StringField("OS", validators=[Optional()])
    pc_ram = StringField("RAM", validators=[Optional()])
    pc_cpu = StringField("CPU", validators=[Optional()])
    pc_gpu = StringField("GPU", validators=[Optional()])
    pc_storage = StringField("Storage", validators=[Optional()])

    ps_os = StringField("OS", validators=[Optional()])
    ps_storage = StringField("Storage", validators=[Optional()])

    xb_os = StringField("OS", validators=[Optional()])
    xb_storage = StringField("Storage", validators=[Optional()])

    submit = SubmitField("Add Game")
