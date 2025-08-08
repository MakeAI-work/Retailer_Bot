 #!/bin/bash

echo "🚀 Setting up WhatsApp Retailer Bots Project..."

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
cd backend
pip install -r requirements.txt

# Create storage directory
echo "📁 Creating storage directories..."
mkdir -p ../storage/invoices
mkdir -p ../storage/temp

# Copy environment file
echo "🔐 Setting up environment variables..."
if [ ! -f ../.env ]; then
    cp ../.env.example ../.env
    echo "✅ Created .env file from .env.example"
    echo "⚠️  Please update the .env file with your actual configuration values"
else
    echo "✅ .env file already exists"
fi

# Create database (PostgreSQL)
echo "🗄️ Database setup instructions:"
echo "1. Make sure PostgreSQL is installed and running"
echo "2. Create a database: createdb whatsapp_retailer_db"
echo "3. Update the DATABASE_* variables in .env file"

echo ""
echo "✅ Project setup complete!"
echo ""
echo "Next steps:"
echo "1. Update .env file with your configuration"
echo "2. Set up PostgreSQL database"
echo "3. Run: cd backend && python -m uvicorn app.main:app --reload"
echo ""
echo "🎉 Happy coding!"
