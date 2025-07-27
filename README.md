# Budget Tracker Web Application

A modern, user-friendly budgeting application with authentication, expense tracking, investment management, and financial goals.

## Features

- 🔐 **User Authentication** - Secure login and registration system
- 💰 **Budget Management** - Create and track monthly budgets by category
- 📊 **Expense Tracking** - Log and categorize expenses with currency conversion
- 📈 **Investment Portfolio** - Track stock investments and portfolio performance
- 🎯 **Financial Goals** - Set and monitor savings goals
- 💡 **AI-Powered Advice** - Get personalized financial advice
- 🌍 **Multi-Currency Support** - Track expenses in different currencies
- 📱 **Responsive Design** - Works on desktop and mobile devices

## Tech Stack

- **Backend**: Flask (Python)
- **Database**: SQLAlchemy with PostgreSQL (production) / SQLite (development)
- **Authentication**: Flask-Login
- **Frontend**: Bootstrap 5, HTML5, CSS3, JavaScript
- **Deployment**: Render (free tier)

## Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd BudgetingWeb
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database**
   ```bash
   python manage.py create_db
   ```

6. **Run the application**
   ```bash
   python app.py
   ```

7. **Access the application**
   Open http://localhost:5000 in your browser

### Free Hosting on Render

#### Option 1: One-Click Deploy (Recommended)

1. **Fork this repository** to your GitHub account

2. **Deploy to Render**
   - Go to [render.com](https://render.com)
   - Sign up with your GitHub account
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select the repository
   - Render will automatically detect the Python app

3. **Configure Environment Variables**
   - In your Render dashboard, go to your service
   - Navigate to "Environment" tab
   - Add the following variables:
     - `SECRET_KEY`: Generate a random string
     - `GEMINI_API_KEY`: Your Gemini API key (optional)
     - `DATABASE_URL`: Will be auto-configured by Render

4. **Deploy**
   - Click "Create Web Service"
   - Render will automatically build and deploy your app

#### Option 2: Manual Deployment

1. **Create a Render account** at [render.com](https://render.com)

2. **Create a new Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Configure the service:
     - **Name**: budget-tracker
     - **Environment**: Python
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `gunicorn app:app`

3. **Add Environment Variables**
   - `SECRET_KEY`: Generate a random string
   - `GEMINI_API_KEY`: Your Gemini API key (optional)

4. **Create Database**
   - Click "New +" → "PostgreSQL"
   - Name: budget-tracker-db
   - Render will automatically link it to your web service

5. **Deploy**
   - Click "Create Web Service"
   - Your app will be available at `https://your-app-name.onrender.com`

## Database Setup

The application uses SQLAlchemy with automatic migrations. The database will be created automatically when you first run the application.

### Local Development
- SQLite database (stored in `budgeting.db`)

### Production (Render)
- PostgreSQL database (automatically provisioned by Render)

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SECRET_KEY` | Flask secret key for sessions | Yes | Auto-generated |
| `DATABASE_URL` | Database connection string | No | SQLite local |
| `GEMINI_API_KEY` | Google Gemini API key | No | None |
| `FLASK_ENV` | Flask environment | No | development |

## API Keys

### Gemini API (Optional)
For AI-powered financial advice:
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add it to your environment variables as `GEMINI_API_KEY`

## Features in Detail

### Authentication
- User registration and login
- Secure password hashing
- Session management
- User-specific data isolation

### Budget Management
- Create monthly budgets by category
- Track spending against budgets
- Visual progress indicators
- Budget vs actual comparisons

### Expense Tracking
- Log expenses with categories
- Multi-currency support
- Automatic USD conversion
- Date-based filtering

### Investment Portfolio
- Track stock purchases
- Portfolio value calculation
- Investment performance metrics
- Purchase history

### Financial Goals
- Set savings targets
- Track progress
- Deadline management
- Goal completion tracking

### AI Financial Advice
- Personalized recommendations
- Budget optimization tips
- Financial goal suggestions
- Spending pattern analysis

## File Structure

```
BudgetingWeb/
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── models.py             # Database models
├── forms.py              # Form definitions
├── requirements.txt      # Python dependencies
├── manage.py            # Database management
├── build.sh             # Build script for deployment
├── render.yaml          # Render deployment config
├── templates/           # HTML templates
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   └── ...
├── static/              # Static files (CSS, JS)
└── db/                  # Database operations
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

For issues and questions:
- Create an issue on GitHub
- Check the documentation
- Review the code comments

## Free Hosting Alternatives

If Render doesn't work for you, here are other free options:

1. **Railway** - $5 credit monthly, very easy deployment
2. **PythonAnywhere** - Python-focused hosting
3. **Heroku** - No longer free but still popular
4. **Vercel** - Great for static sites, requires external database

## Security Notes

- All passwords are hashed using Werkzeug
- User sessions are managed securely
- Database queries are protected against SQL injection
- Environment variables are used for sensitive data
- HTTPS is enforced in production

## Performance Tips

- Database queries are optimized
- Static assets are cached
- Lazy loading for large datasets
- Efficient currency conversion caching 