#!/bin/bash

# Platform check
case "$(uname)" in
    Darwin)
        echo "Mac OS X platform"
        ;;
    Linux)
        echo "GNU/Linux platform"
        if ! command -v dnf &> /dev/null; then
            echo "dnf command not found"
            exit 1
        fi
        if ! command -v sudo &> /dev/null; then
            echo "sudo command not found"
            exit 1
        fi
        ;;
    MINGW32_NT*|MINGW64_NT*)
        echo "Windows platform"
        if ! command -v choco &> /dev/null; then
            echo "Chocolatey command not found. Please install Chocolatey."
            exit 1
        fi
        ;;
    *)
        echo "Unsupported platform"
        exit 1
        ;;
esac

# Install tmux if not installed
if ! command -v tmux &> /dev/null; then
    sudo dnf install -y tmux
else
    tmux kill-server
fi

# Change directory to your project folder
cd /24-sum-b-4-pe-portfolio-site || { echo "Directory not found"; exit 1; }

# Fetch latest changes from GitHub main branch
git fetch && git reset origin/main --hard || echo "Failed to fetch and reset origin/main"

# Check if pip is installed, if not, install it
if ! command -v pip3 &> /dev/null; then
    sudo dnf install -y python3-pip
fi

# Check if virtualenv is installed, if not, install it
if ! command -v virtualenv &> /dev/null; then
    pip3 install --user -q virtualenv
fi

# Create a virtual environment if not already created
if [ ! -d "venv" ]; then
    virtualenv venv
fi

# Activate the virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "venv/bin/activate does not exist"
    exit 1
fi

# Install requirements
if [ -f "requirements.txt" ]; then
    pip install --no-warn-script-location -q -r requirements.txt
else
    echo "requirements.txt does not exist"
    exit 1
fi

# Install Flask if not installed
if ! command -v flask &> /dev/null; then
    pip install --user Flask
fi

# Load environment variables from .env file
if [ -f ".env" ]; then
    export $(cat .env | xargs)
fi

# Set Flask app environment variable
export FLASK_APP=main

# Start a new detached tmux session and start Flask server
tmux new-session -d -s "mike-odnis" "cd /24-sum-b-4-pe-portfolio-site && source venv/bin/activate && flask run --host=0.0.0.0 --port=5000" || echo "Failed to start Flask"

# Optional: Provide feedback or confirmation
echo "Flask server restarted and running in tmux session 'mike-odnis'."
