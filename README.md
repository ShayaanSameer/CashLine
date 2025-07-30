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
   git clone https://github.com/yourusername/Cashline.git
   cd Cashline
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

5. **Run the application**
   ```bash
   python3 run.py
   ```
   The database will be automatically created on first run.

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
Cashline
├── README.md
├── app
│   ├── __init__.py
│   ├── forms.py
│   ├── mongoModels.py
│   ├── operations.py
│   ├── routes
│   │   ├── advice.py
│   │   ├── auth.py
│   │   ├── budget.py
│   │   ├── expenses.py
│   │   ├── goals.py
│   │   ├── main.py
│   │   └── portfolio.py
│   ├── static
│   └── templates
├── config.py
├── render.yaml
├── requirements.txt
├── run.py
├── scripts
├── temp
└── test
    ├── test_db.py
    ├── test_finnhub.py
    ├── test_price.py
    └── test_stock_search.py
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

Wireframe

# CashLine Budgeting Application - Wireframe

## Application Overview
CashLine is a comprehensive personal finance management web application with the following key features:
- Dashboard with spending analytics
- Budget management
- Expense tracking
- Investment portfolio management
- Financial goals tracking
- AI-powered financial advice
- Retirement planning
- User authentication

---

## 1. Authentication Pages

### Login Page
```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                    [CashLine Logo]                         │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                Welcome Back                        │    │
│  │              Sign in to your account              │    │
│  │                                                 │    │
│  │  Username: [________________]                    │    │
│  │  Password: [________________]                    │    │
│  │                                                 │    │
│  │  [        Sign In        ]                      │    │
│  │                                                 │    │
│  │  Don't have an account? Create one here        │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Registration Page
```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                    [CashLine Logo]                         │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                Create Account                      │    │
│  │                                                 │    │
│  │  Username: [________________]                    │    │
│  │  Email: [____________________]                   │    │
│  │  Password: [________________]                    │    │
│  │  Confirm Password: [________]                    │    │
│  │                                                 │    │
│  │  [      Create Account      ]                    │    │
│  │                                                 │    │
│  │  Already have an account? Sign in here          │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Main Application Layout

### Sidebar Navigation
```
┌─────────────────────────────────────────────────────────────┐
│  CashLine                    [Date & Time]                │
├─────────────────────────────────────────────────────────────┤
│  🏠 Dashboard                                              │
│  💰 Budgets                                               │
│  📄 Expenses                                               │
│  📈 Portfolio                                              │
│  💡 Advice                                                 │
│  🎯 Goals                                                  │
├─────────────────────────────────────────────────────────────┤
│  👤 [Username]                                            │
│  [Logout]                                                 │
│                                                             │
│  © 2024 CashLine                                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Dashboard Page

### Main Dashboard Layout
```
┌─────────────────────────────────────────────────────────────┐
│  Home                    [Currency Selector] [Income Badge]│
│  Monday, January 15, 2024                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Get Started with AI-Powered Budgeting             │    │
│  │  New to budgeting? Let our AI help you create a   │    │
│  │  personalized budget based on your income,         │    │
│  │  expenses, and financial goals.                    │    │
│  │  [Start Onboarding]                                │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  ┌─────────────────────────────┐ ┌─────────────────────┐   │
│  │ Monthly Spending Trend      │ │ Category Breakdown  │   │
│  │ [Chart Area]                │ │ [Pie Chart]        │   │
│  └─────────────────────────────┘ └─────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────┐ ┌─────────────────────┐   │
│  │ Monthly Spending            │ │ Investments         │   │
│  │ $2,450 of $3,000           │ │ $15,234.56         │   │
│  │ [Progress Bar]              │ │ Current Portfolio   │   │
│  │ 18% left                   │ │ [View all]          │   │
│  └─────────────────────────────┘ └─────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Recent Expenses                                    │    │
│  │ ┌─────────┬──────────┬──────────┬──────────────┐   │    │
│  │ │ Amount  │ Category │ Date     │ Description  │   │    │
│  │ ├─────────┼──────────┼──────────┼──────────────┤   │    │
│  │ │ $45.00  │ Food     │ 2024-01-│ Groceries    │   │    │
│  │ │ $120.00 │ Transport│ 2024-01-│ Gas          │   │    │
│  │ └─────────┴──────────┴──────────┴──────────────┘   │    │
│  │ [View all expenses]                                 │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  [+ Quick Add]                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Budget Management Page

### Budget Page Layout
```
┌─────────────────────────────────────────────────────────────┐
│  Budgets                                                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Add New Budget                                     │    │
│  │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │    │
│  │ │ Category    │ │ Limit Amount│ │ Month       │   │    │
│  │ │ [Dropdown]  │ │ [$_______]  │ │ [Dropdown]  │   │    │
│  │ └─────────────┘ └─────────────┘ └─────────────┘   │    │
│  │ ┌─────────────┐                                    │    │
│  │ │ Year        │ [Add Budget]                       │    │
│  │ │ [Dropdown]  │                                    │    │
│  │ └─────────────┘                                    │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Your Budgets                                        │    │
│  │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │    │
│  │ │ Food        │ │ Transport   │ │ Entertainment│   │    │
│  │ │ $500        │ │ $300        │ │ $200        │   │    │
│  │ │ Jan 2024    │ │ Jan 2024    │ │ Jan 2024    │   │    │
│  │ │ [Edit][Del] │ │ [Edit][Del] │ │ [Edit][Del] │   │    │
│  │ └─────────────┘ └─────────────┘ └─────────────┘   │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. Expenses Page

### Expenses Management Layout
```
┌─────────────────────────────────────────────────────────────┐
│  Expenses                                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Add New Expense                                    │    │
│  │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │    │
│  │ │ Amount      │ │ Currency    │ │ Category    │   │    │
│  │ │ [$_______]  │ │ [Dropdown]  │ │ [Dropdown]  │   │    │
│  │ └─────────────┘ └─────────────┘ └─────────────┘   │    │
│  │ Description: [________________________]             │    │
│  │ Date: [Date Picker]                                │    │
│  │ [Add Expense]                                       │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ All Expenses                                        │    │
│  │ ┌─────────────┬──────────┬──────────┬────────────┐ │    │
│  │ │ Description │ Category │ Amount   │ Date       │ │    │
│  │ ├─────────────┼──────────┼──────────┼────────────┤ │    │
│  │ │ Groceries   │ Food     │ $45.00   │ 2024-01-15│ │    │
│  │ │ Gas         │ Transport│ $120.00  │ 2024-01-14│ │    │
│  │ │ Movie       │ Entertain│ $25.00   │ 2024-01-13│ │    │
│  │ └─────────────┴──────────┴──────────┴────────────┘ │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. Portfolio Overview Page

### Portfolio Management Layout
```
┌─────────────────────────────────────────────────────────────┐
│  Portfolio Overview                                        │
│  Track your investments and plan for retirement           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────┐ │
│  │ Current     │ │ Total       │ │ Current     │ │Total│ │
│  │ Holdings    │ │ Purchase    │ │ Portfolio   │ │Gain/│ │
│  │ 5           │ │ Value       │ │ Value       │ │Loss │ │
│  │ Active      │ │ $12,500.00  │ │ $15,234.56 │ │$2,73│ │
│  │ investments │ │ Amount      │ │ Real-time   │ │4.56 │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────┘ │
│                                                             │
│  ┌─────────────────────────────┐ ┌─────────────────────┐   │
│  │ Portfolio Performance       │ │ Asset Allocation    │   │
│  │ [Line Chart]                │ │ [Pie Chart]        │   │
│  └─────────────────────────────┘ └─────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Quick Actions                                       │    │
│  │ [Add Investment] [Asset Allocation] [Retirement]   │    │
│  │ [Current Holdings] [Retirement Planning]           │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Recent Holdings                                     │    │
│  │ ┌─────────────┬──────────┬──────────┬────────────┐ │    │
│  │ │ Symbol      │ Shares   │ Avg Price│ Current    │ │    │
│  │ ├─────────────┼──────────┼──────────┼────────────┤ │    │
│  │ │ AAPL        │ 10       │ $150.00  │ $155.00    │ │    │
│  │ │ GOOGL       │ 5        │ $120.00  │ $125.00    │ │    │
│  │ └─────────────┴──────────┴──────────┴────────────┘ │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. Goals Page

### Financial Goals Layout
```
┌─────────────────────────────────────────────────────────────┐
│  Goals                                                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Your Financial Goals                    [Add Goal] │    │
│  │                                                 │    │
│  │ Overall Progress                                  │    │
│  │ Total Saved: $2,500 / $5,000                     │    │
│  │ [Progress Bar: 50%]                              │    │
│  │                                                 │    │
│  │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │    │
│  │ │ Vacation    │ │ New Car     │ │ Emergency   │   │    │
│  │ │ Target:     │ │ Target:     │ │ Fund        │   │    │
│  │ │ $3,000      │ │ $25,000     │ │ Target:     │   │    │
│  │ │ Current:    │ │ Current:    │ │ $10,000     │   │    │
│  │ │ $1,500      │ │ $0          │ │ Current:    │   │    │
│  │ │ [50% Bar]   │ │ [0% Bar]    │ │ $1,000      │   │    │
│  │ │ [Edit][Del] │ │ [Edit][Del] │ │ [10% Bar]   │   │    │
│  │ └─────────────┘ └─────────────┘ └─────────────┘   │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Goals Summary                                       │    │
│  │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │    │
│  │ │ 3           │ │ $2,500      │ │ $38,000     │   │    │
│  │ │ Goals       │ │ Total Saved │ │ Total Target│   │    │
│  │ └─────────────┘ └─────────────┘ └─────────────┘   │    │
│  │ ┌─────────────┐                                    │    │
│  │ │ 6.6%        │                                    │    │
│  │ │ Overall     │                                    │    │
│  │ │ Progress    │                                    │    │
│  │ └─────────────┘                                    │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 8. Advice Page (AI Chatbot)

### AI Financial Advice Layout
```
┌─────────────────────────────────────────────────────────────┐
│  Advice                                                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                                                     │    │
│  │  💬 Hello! I'm your AI financial advisor. How     │    │
│  │     can I help you today?                          │    │
│  │                                                     │    │
│  │  👤 How can I save more money?                    │    │
│  │                                                     │    │
│  │  💬 Here are some tips to save more money:        │    │
│  │     • Track your expenses regularly                │    │
│  │     • Set up automatic savings                     │    │
│  │     • Reduce unnecessary subscriptions             │    │
│  │     • Cook at home more often                     │    │
│  │                                                     │    │
│  │  👤 What's a good emergency fund amount?          │    │
│  │                                                     │    │
│  │  💬 A good emergency fund should cover 3-6        │    │
│  │     months of your living expenses...              │    │
│  │                                                     │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ [Type your question...]                    [Send] │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 9. Retirement Planning Pages

### Retirement Planning Overview
```
┌─────────────────────────────────────────────────────────────┐
│  Retirement Planning                                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Retirement Calculator                               │    │
│  │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │    │
│  │ │ Current Age │ │ Retirement  │ │ Life        │   │    │
│  │ │ [25]        │ │ Age [65]    │ │ Expectancy  │   │    │
│  │ └─────────────┘ └─────────────┘ └─────────────┘   │    │
│  │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │    │
│  │ │ Current     │ │ Monthly     │ │ Expected    │   │    │
│  │ │ Savings     │ │ Contribution │ │ Return Rate │   │    │
│  │ │ [$10,000]   │ │ [$500]      │ │ [7%]        │   │    │
│  │ └─────────────┘ └─────────────┘ └─────────────┘   │    │
│  │ [Calculate Retirement Needs]                        │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Retirement Plans                                     │    │
│  │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │    │
│  │ │ 401(k)      │ │ IRA         │ │ Roth IRA    │   │    │
│  │ │ $15,000     │ │ $8,000      │ │ $5,000      │   │    │
│  │ │ [Edit]      │ │ [Edit]      │ │ [Edit]      │   │    │
│  │ └─────────────┘ └─────────────┘ └─────────────┘   │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 10. Mobile Responsive Design

### Mobile Layout (Sidebar becomes horizontal)
```
┌─────────────────────────────────────────────────────────────┐
│  CashLine  [Date] [Time]                                  │
├─────────────────────────────────────────────────────────────┤
│  🏠  💰  📄  📈  💡  🎯                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [Dashboard Content - Same as desktop but stacked]        │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Monthly Spending Trend                              │    │
│  │ [Chart]                                            │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Category Breakdown                                  │    │
│  │ [Pie Chart]                                        │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  [+ Quick Add]                                              │
└─────────────────────────────────────────────────────────────┘
```

