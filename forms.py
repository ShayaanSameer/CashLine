from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField, DateField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose a different one.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different one.')

class BudgetForm(FlaskForm):
    category = StringField('Category', validators=[DataRequired()])
    limit_amount = FloatField('Limit Amount', validators=[DataRequired()])
    month = SelectField('Month', choices=[
        ('January', 'January'), ('February', 'February'), ('March', 'March'),
        ('April', 'April'), ('May', 'May'), ('June', 'June'),
        ('July', 'July'), ('August', 'August'), ('September', 'September'),
        ('October', 'October'), ('November', 'November'), ('December', 'December')
    ], validators=[DataRequired()])
    year = SelectField('Year', choices=[(str(year), str(year)) for year in range(2020, 2031)], validators=[DataRequired()])
    submit = SubmitField('Add Budget')

class ExpenseForm(FlaskForm):
    amount = FloatField('Amount', validators=[DataRequired()])
    category = StringField('Category', validators=[DataRequired()])
    description = StringField('Description', validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()])
    currency = SelectField('Currency', choices=[
        ('USD', 'USD ($)'), ('EUR', 'EUR (€)'), ('GBP', 'GBP (£)'),
        ('INR', 'INR (₹)'), ('CAD', 'CAD (C$)'), ('AUD', 'AUD (A$)')
    ], validators=[DataRequired()])
    submit = SubmitField('Add Expense')

class InvestmentForm(FlaskForm):
    symbol = StringField('Stock Symbol', validators=[DataRequired()])
    shares = FloatField('Number of Shares', validators=[DataRequired()])
    purchase_price = FloatField('Purchase Price', validators=[DataRequired()])
    purchase_date = DateField('Purchase Date', validators=[DataRequired()])
    submit = SubmitField('Add Investment')

class GoalForm(FlaskForm):
    name = StringField('Goal Name', validators=[DataRequired()])
    target_amount = FloatField('Target Amount', validators=[DataRequired()])
    current_amount = FloatField('Current Amount', validators=[DataRequired()])
    target_date = DateField('Target Date', validators=[DataRequired()])
    submit = SubmitField('Add Goal') 