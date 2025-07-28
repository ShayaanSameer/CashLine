# CashLine - Personal Finance Management Platform

A comprehensive personal finance management application built with Flask, featuring budgeting, expense tracking, investment portfolio management, retirement planning, and AI-powered financial advice.

## Live Demo

**Access the deployed application:** [https://cashline-lvfj.onrender.com](https://cashline-lvfj.onrender.com)

## Features

### Core Financial Management
- **Budget Tracking**: Create and manage monthly budgets by category
- **Expense Tracking**: Log and categorize expenses with detailed descriptions
- **Financial Goals**: Set and track progress towards financial goals
- **Multi-Currency Support**: Support for USD, EUR, GBP, INR, CAD, AUD, and more

### Investment Portfolio Management
- **Portfolio Overview**: Real-time tracking of investment holdings
- **Stock Price Integration**: Live stock prices via Finnhub API
- **Asset Allocation**: Strategic portfolio allocation with risk assessment
- **Performance Analytics**: Gain/loss tracking and return calculations
- **Weighted Return Calculations**: Advanced portfolio performance metrics

### Retirement Planning
- **Retirement Calculator**: Multi-scenario retirement planning with different risk levels
- **Asset Allocation**: Strategic retirement portfolio management
- **Retirement Profile**: Personalized retirement planning based on age, income, and goals
- **Automated Planning**: AI-powered retirement strategy recommendations
- **Scenario Comparison**: Compare conservative, moderate, and aggressive approaches

### AI-Powered Financial Advice
- **Personalized Recommendations**: AI advice based on your financial data
- **Context-Aware Suggestions**: Recommendations considering your income, expenses, goals, and investments
- **Real-time Chat**: Interactive financial advice through chat interface
- **Gemini AI Integration**: Powered by Google's Gemini AI for intelligent financial guidance

### Dashboard & Analytics
- **Interactive Charts**: Visual representation of spending trends and budget vs actual
- **Financial Overview**: Comprehensive snapshot of your financial health
- **Progress Tracking**: Visual progress indicators for goals and budgets
- **Real-time Updates**: Live data updates across all modules

### Security & User Management
- **User Authentication**: Secure login and registration system
- **Session Management**: Persistent user sessions with security
- **Data Privacy**: User-specific data isolation and protection

## Local Development Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)
- Git

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/cashline.git
   cd cashline/Budgeting/BudgetingWeb
   ```

2. **Create and activate virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` file with your API keys:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   FINNHUB_API_KEY=your_finnhub_api_key_here
   EXCHANGE_RATE_API_KEY=your_exchange_rate_api_key_here
   SECRET_KEY=your_secret_key_here
   ```

5. **Initialize the database**
   ```bash
   python3 app.py
   ```
   The database will be automatically created on first run.

6. **Run the application**
   ```bash
   python3 app.py
   ```

7. **Access the application**
   Open your browser and navigate to `http://localhost:5000`

### API Keys Required

- **Gemini AI API**: For AI-powered financial advice
  - Get from: [Google AI Studio](https://makersuite.google.com/app/apikey)
- **Finnhub API**: For real-time stock prices
  - Get from: [Finnhub](https://finnhub.io/)
- **Exchange Rate API**: For currency conversions
  - Get from: [Exchange Rate API](https://www.exchangerate-api.com/)

## Project Structure

```
Budgeting/
├── BudgetingWeb/
│   ├── app.py                 # Main Flask application
│   ├── config.py              # Configuration settings
│   ├── models.py              # Database models
│   ├── forms.py               # Flask-WTF forms
│   ├── static/
│   │   └── style.css         # Custom styling
│   ├── templates/             # HTML templates
│   │   ├── base.html         # Base template
│   │   ├── dashboard.html    # Main dashboard
│   │   ├── budget.html       # Budget management
│   │   ├── expenses.html     # Expense tracking
│   │   ├── portfolio.html    # Investment portfolio
│   │   └── ...               # Other templates
│   └── db/                   # Database files
├── requirements.txt           # Python dependencies
└── README.md                 # This file
```

## Design Features

### Modern UI/UX
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile
- **Pastel Color Scheme**: Soothing, professional color palette
- **Card-based Layout**: Clean, organized information presentation
- **Interactive Elements**: Hover effects, progress bars, and dynamic charts

### User Experience
- **Intuitive Navigation**: Easy-to-use interface with clear navigation
- **Real-time Updates**: Live data updates without page refreshes
- **Form Validation**: Comprehensive input validation and error handling
- **Loading States**: Visual feedback during data processing

## Configuration

### Environment Variables
- `GEMINI_API_KEY`: Required for AI advice functionality
- `FINNHUB_API_KEY`: Required for stock price data
- `EXCHANGE_RATE_API_KEY`: Required for currency conversions
- `SECRET_KEY`: Flask secret key for session management
- `DATABASE_URL`: Database connection string (optional)

### Database Configuration
The application uses SQLite by default for local development. For production, you can configure PostgreSQL or MySQL.

## Deployment

### Render Deployment
The application is deployed on Render.com with the following configuration:
- **Runtime**: Python 3.9
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python app.py`
- **Environment Variables**: Configured through Render dashboard

### Local Production Setup
1. Set `FLASK_ENV=production` in environment variables
2. Configure a production database (PostgreSQL recommended)
3. Set up proper logging and monitoring
4. Configure HTTPS and security headers

## API Endpoints

### Authentication
- `POST /login` - User login
- `POST /register` - User registration
- `GET /logout` - User logout

### Financial Management
- `GET /` - Dashboard
- `GET /budget` - Budget management
- `GET /expenses` - Expense tracking
- `GET /goals` - Financial goals

### Portfolio Management
- `GET /portfolio` - Portfolio overview
- `GET /portfolio/holdings` - Investment holdings
- `GET /portfolio/allocation` - Asset allocation

### Retirement Planning
- `GET /portfolio/retirement` - Retirement planning
- `GET /portfolio/retirement/calculator` - Retirement calculator
- `GET /portfolio/retirement/profile` - Retirement profile

### AI Features
- `GET /advice` - Financial advice
- `POST /advice/chat` - AI chat interface

## Testing

Run the test suite:
```bash
python -m pytest tests/
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **Flask**: Web framework
- **SQLAlchemy**: Database ORM
- **Bootstrap**: UI framework
- **Chart.js**: Data visualization
- **Google Gemini AI**: AI-powered financial advice
- **Finnhub**: Stock market data
- **Exchange Rate API**: Currency conversion

## Support

For support, please open an issue on GitHub or contact the development team.

---

**CashLine** - Your comprehensive personal finance companion.
