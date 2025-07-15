from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, ValidationError
from wtforms.validators import DataRequired, Length


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

    def validate_password(self, field):
        password = field.data

        if " " in password:
            raise ValidationError("Password cannot contain spaces")
