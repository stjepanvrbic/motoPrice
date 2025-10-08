#!/bin/bash
set -e

echo "=== motoPrice Environment Setup ==="
echo ""

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
else
    echo "Error: Unsupported OS. This script supports Linux and macOS only."
    exit 1
fi

echo "Detected OS: $OS"
echo ""

# Install PostgreSQL based on OS
if ! command -v psql &> /dev/null; then
    echo "PostgreSQL not found. Installing..."

    if [ "$OS" = "macos" ]; then
        # Check for Homebrew
        if ! command -v brew &> /dev/null; then
            echo "Homebrew not found. Installing Homebrew..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi

        brew install postgresql@15
        brew services start postgresql@15

        # Add to PATH for current session
        export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"

        # Add to shell profile
        if [ -f "$HOME/.zshrc" ]; then
            echo 'export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"' >> ~/.zshrc
        fi

    elif [ "$OS" = "linux" ]; then
        # Detect Linux distro
        if [ -f /etc/debian_version ]; then
            # Debian/Ubuntu
            sudo apt-get update
            sudo apt-get install -y postgresql postgresql-contrib
            sudo systemctl start postgresql
            sudo systemctl enable postgresql
        elif [ -f /etc/redhat-release ]; then
            # RHEL/CentOS/Fedora
            sudo yum install -y postgresql-server postgresql-contrib
            sudo postgresql-setup initdb
            sudo systemctl start postgresql
            sudo systemctl enable postgresql
        elif [ -f /etc/arch-release ]; then
            # Arch Linux
            sudo pacman -S postgresql
            sudo systemctl start postgresql
            sudo systemctl enable postgresql
        else
            echo "Error: Unsupported Linux distribution. Please install PostgreSQL manually."
            exit 1
        fi
    fi
else
    echo "PostgreSQL already installed: $(psql --version)"

    # Make sure PostgreSQL is running
    if [ "$OS" = "macos" ]; then
        if ! brew services list | grep postgresql@15 | grep started &> /dev/null; then
            echo "Starting PostgreSQL service..."
            brew services start postgresql@15
        fi
    elif [ "$OS" = "linux" ]; then
        if ! systemctl is-active --quiet postgresql; then
            echo "Starting PostgreSQL service..."
            sudo systemctl start postgresql
        fi
    fi
fi

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to start..."
sleep 3

# Create database
echo "Creating database 'motoprice'..."
if [ "$OS" = "linux" ]; then
    # On Linux, might need to create user first
    sudo -u postgres psql -tc "SELECT 1 FROM pg_user WHERE usename = '$USER'" | grep -q 1 || \
        sudo -u postgres createuser -s $USER

    if sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw motoprice; then
        echo "Database 'motoprice' already exists"
    else
        sudo -u postgres createdb -O $USER motoprice
        echo "Database 'motoprice' created"
    fi
else
    if psql postgres -lqt | cut -d \| -f 1 | grep -qw motoprice; then
        echo "Database 'motoprice' already exists"
    else
        createdb motoprice
        echo "Database 'motoprice' created"
    fi
fi

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 not found. Please install Python 3.11 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "Python version: $PYTHON_VERSION"

# Set up Python virtual environment
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
else
    echo "Virtual environment already exists"
fi

# Activate virtual environment and install dependencies
echo "Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Install Playwright browsers
echo "Installing Playwright browsers..."
playwright install

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp config/.env.example .env

    # Update database URL in .env based on OS
    if [ "$OS" = "macos" ]; then
        sed -i '' "s|postgresql://YOUR_USERNAME:YOUR_PASSWORD@localhost:5432/motoprice|postgresql://$USER@localhost:5432/motoprice|" .env
    else
        sed -i "s|postgresql://YOUR_USERNAME:YOUR_PASSWORD@localhost:5432/motoprice|postgresql://$USER@localhost:5432/motoprice|" .env
    fi

    echo ".env file created (edit with your API keys)"
else
    echo ".env file already exists"
fi

# Install pre-commit hooks
echo "Installing pre-commit hooks..."
pre-commit install

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Edit .env file with your OpenAI API key"
echo "2. Run database migrations: alembic upgrade head"
echo "3. Activate virtual environment: source venv/bin/activate"
echo "4. Run tests: pytest"
echo ""
echo "To start developing, run: source venv/bin/activate"
