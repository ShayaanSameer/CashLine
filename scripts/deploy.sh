#!/bin/bash

echo "Setting up Budget Tracker for deployment..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "pip3 is not installed. Please install pip first."
    exit 1
fi

echo "Python and pip are available"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating environment file..."
    cp env.example .env
    echo "Please edit .env file with your configuration"
fi

# Initialize database
echo "Initializing database..."
python manage.py create_db

echo "Setup complete!"
echo ""
echo "To run the application locally:"
echo "   source venv/bin/activate"
echo "   python app.py"
echo ""
echo "To deploy to Render:"
echo "   1. Push your code to GitHub"
echo "   2. Go to render.com and create a new Web Service"
echo "   3. Connect your GitHub repository"
echo "   4. Add environment variables in Render dashboard"
echo ""
echo "For detailed instructions, see README.md" 