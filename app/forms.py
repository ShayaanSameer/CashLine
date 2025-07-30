from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField, DateField, TextAreaField, SelectField, IntegerField, HiddenField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, NumberRange, Optional, InputRequired, NumberRange

from .operations import mongoDBClient, deserializeDoc

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
    
    def __init__(self, mongo_client, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mongo_client = mongo_client

    def validate_username(self, username):
        user_doc = self.mongo_client.getCollectionEndpoint('User').find_one({'username':username.data})

        if user_doc:
            raise ValidationError('Username already taken. Please choose a different one.')
    
    def validate_email(self, email):
        user_doc = self.mongo_client.getCollectionEndpoint('User').find_one({'email':email.data})

        if user_doc:
            raise ValidationError('Email already registered. Please use a different one.')

class UserProfileForm(FlaskForm):
    age = IntegerField('Age', validators=[DataRequired(), NumberRange(min=18, max=100)])
    retirement_age = IntegerField('Retirement Age', validators=[DataRequired(), NumberRange(min=50, max=80)])
    current_salary = FloatField('Current Annual Salary', validators=[DataRequired(), NumberRange(min=0)])
    expected_retirement_income = FloatField('Expected Annual Retirement Income', validators=[DataRequired(), NumberRange(min=0)])
    current_savings = FloatField('Current Retirement Savings', validators=[DataRequired(), NumberRange(min=0)])
    monthly_contribution = FloatField('Monthly Contribution', validators=[DataRequired(), NumberRange(min=0)])
    risk_tolerance = SelectField('Risk Tolerance', choices=[
        ('Conservative', 'Conservative (Low Risk)'),
        ('Moderate', 'Moderate (Medium Risk)'),
        ('Aggressive', 'Aggressive (High Risk)')
    ], validators=[DataRequired()])
    submit = SubmitField('Save Profile')

class AssetForm(FlaskForm):
    symbol = StringField('Asset Symbol', validators=[DataRequired(), Length(max=10)])
    name = StringField('Asset Name', validators=[DataRequired(), Length(max=100)])
    asset_type = SelectField('Asset Type', choices=[
        ('Stock', 'Stock'),
        ('Bond', 'Bond'),
        ('ETF', 'ETF'),
        ('Mutual Fund', 'Mutual Fund'),
        ('Real Estate', 'Real Estate'),
        ('Commodity', 'Commodity'),
        ('Other', 'Other')
    ], validators=[DataRequired()])
    expected_return = FloatField('Expected Annual Return (%)', validators=[InputRequired(), NumberRange(min=0, max=50)])
    weight = FloatField('Portfolio Weight (%)', validators=[InputRequired(), NumberRange(min=0, max=100)])
    risk_level = SelectField('Risk Level', choices=[
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High')
    ], validators=[DataRequired()])
    submit = SubmitField('Add Asset')

class RetirementPlanForm(FlaskForm):
    name = StringField('Plan Name', validators=[DataRequired(), Length(max=100)])
    target_amount = FloatField('Target Retirement Amount', validators=[DataRequired(), NumberRange(min=0)])
    years_to_retirement = IntegerField('Years to Retirement', validators=[DataRequired(), NumberRange(min=1, max=60)])
    expected_return_rate = FloatField('Expected Annual Return Rate (%)', validators=[DataRequired(), NumberRange(min=0, max=20)])
    # monthly_contribution = FloatField('Monthly Contribution', validators=[InputRequired(), NumberRange(min=0)])
    submit = SubmitField('Add Plan')

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
    category = SelectField('Category', validators=[DataRequired()])
    description = StringField('Description', validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()])
    currency = SelectField('Currency', choices=[
        ('USD', 'USD ($)'), ('EUR', 'EUR (€)'), ('GBP', 'GBP (£)'),
        ('INR', 'INR (₹)'), ('CAD', 'CAD (C$)'), ('AUD', 'AUD (A$)')
    ], validators=[DataRequired()])
    submit = SubmitField('Add Expense')

class InvestmentForm(FlaskForm):
    symbol = StringField('Stock Symbol', validators=[DataRequired()])
    shares = FloatField('Number of Shares', validators=[DataRequired(), NumberRange(min=0)])
    purchase_price = FloatField('Purchase Price', validators=[DataRequired()])
    purchase_date = DateField('Purchase Date', validators=[DataRequired()])
    submit = SubmitField('Add Investment')

class GoalForm(FlaskForm):
    name = StringField('Goal Name', validators=[DataRequired()])
    target_amount = FloatField('Target Amount', validators=[DataRequired()])
    current_amount = FloatField('Current Amount', validators=[InputRequired(), NumberRange(min=0)])
    target_date = DateField('Target Date', validators=[DataRequired()])
    submit = SubmitField('Add Goal') 

class AutomatedRetirementForm(FlaskForm):
    # Basic Info (User provides)
    current_age = IntegerField('Your Age', validators=[DataRequired(), NumberRange(min=18, max=100)])
    current_income = FloatField('Current Annual Income', validators=[DataRequired(), NumberRange(min=0)])
    current_savings = FloatField('Current Retirement Savings', validators=[InputRequired(), NumberRange(min=0)])
    
    # Risk tolerance for auto-calculation
    risk_tolerance = SelectField('Risk Tolerance', choices=[
        ('Conservative', 'Conservative (Low Risk)'),
        ('Moderate', 'Moderate (Medium Risk)'),
        ('Aggressive', 'Aggressive (High Risk)')
    ], validators=[DataRequired()])
    
    submit = SubmitField('Create Smart Plan')

class RetirementProfileForm(FlaskForm):
    current_age = IntegerField('Current Age', validators=[DataRequired(), NumberRange(min=18, max=100)])
    retirement_age = IntegerField('Retirement Age', validators=[DataRequired(), NumberRange(min=50, max=80)])
    current_income = FloatField('Current Annual Income', validators=[DataRequired(), NumberRange(min=1)])
    expected_retirement_income = FloatField('Expected Annual Retirement Income', validators=[DataRequired(), NumberRange(min=0)])
    current_savings = FloatField('Current Retirement Savings', validators=[InputRequired(), NumberRange(min=0)])
    submit = SubmitField('Save Profile')

class RetirementCalculatorForm(FlaskForm):
    target_amount = FloatField('Target Retirement Amount', validators=[DataRequired(), NumberRange(min=0)])
    current_savings = FloatField('Current Savings', validators=[InputRequired(), NumberRange(min=0)])
    years_to_retirement = IntegerField('Years to Retirement', validators=[DataRequired(), NumberRange(min=1, max=100)])
    expected_return = FloatField('Expected Annual Return (%)', validators=[InputRequired(), NumberRange(min=0, max=20)])
    submit = SubmitField('Calculate Scenarios') 