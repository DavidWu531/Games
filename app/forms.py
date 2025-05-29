from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
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
        pass
