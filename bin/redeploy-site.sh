#!/bin/bash

cd "$(dirname "$0")" || { echo "Failed to change directory"; exit 1; }

cd 24-sum-b-4-pe-portfolio-site || { echo "Failed to change directory"; exit 1; }

if [ -f ".env" ]; then
    export $(cat .env | xargs)
else
    echo ".env file not found"
    exit 1
fi

flask_started=false
max_retries=1
retry_count=0

system_check() {
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
            else
                sudo dnf install lsof
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
}

check_mysql() {
    # Check if MySQL is installed
    if ! command -v mysql &> /dev/null; then
        echo "MySQL is not installed. Installing MySQL..."
        sudo dnf install -y mysql-server
        sudo systemctl start mysqld
        sudo systemctl enable mysqld
    fi

    # Check if MySQL service is running
    if ! systemctl is-active --quiet mysqld; then
        echo "MySQL service is not running. Starting MySQL service..."
        sudo systemctl start mysqld
    fi

    # Ensure MySQL user has the necessary permissions
    mysql -u root -e "CREATE USER IF NOT EXISTS '${MYSQL_USER}'@'localhost' IDENTIFIED BY '${MYSQL_PASSWORD}';"
    mysql -u root -e "GRANT ALL PRIVILEGES ON ${MYSQL_DATABASE}.* TO '${MYSQL_USER}'@'localhost';"
    mysql -u root -e "FLUSH PRIVILEGES;"

    mysql -u root -e "USE ${MYSQL_DATABASE};" || mysql -u root -e "CREATE DATABASE IF NOT EXISTS ${MYSQL_DATABASE};"
}

clean_environment() {
    # Install tmux if not installed
    if ! command -v tmux &> /dev/null; then
        sudo dnf install -y tmux
    else
        tmux kill-server
    fi

    # Change directory to your project folder
    cd 24-sum-b-4-pe-portfolio-site || { echo "Directory not found"; exit 1; }

    # Fetch latest changes from GitHub main branch
    git fetch && git reset origin/main --hard || echo "Failed to fetch and reset origin/main"
}

checks() {
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
        chmod +x venv/bin/activate
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
        pip install --upgrade pip
        pip install --no-warn-script-location -q -r requirements.txt
    else
        echo "requirements.txt does not exist"
        exit 1
    fi

    # Install Flask if not installed
    if ! command -v flask &> /dev/null; then
        pip install --user Flask
    fi
}

start_flask_server() {
    # Start the Flask server in the background
    nohup flask run --host=0.0.0.0 > flask.log 2>&1 &
    flask_pid=$!
    echo "Flask server started with PID $flask_pid"
}

stop_flask_server() {
    # Stop the Flask server
    if [ -n "$flask_pid" ]; then
        kill $flask_pid
        echo "Flask server stopped"
    fi
}

run_tests() {
    # Run the unittest command and capture the output and exit code
    output=$(python -m unittest discover -s tests/unit -p "test_*.py" 2>&1)
    exit_code=$?

    # Check if the tests passed or failed
    if [ $exit_code -eq 0 ]; then
        echo "Tests passed successfully!"
        rm tests/unit/test_portfolio.db
        echo "$output"
    else
        echo "Tests failed."
        echo "$output"
        exit $exit_code
    fi
}

main() {
    start_time=$(date +%s)
    system_check || echo "System check failed"
    check_mysql || echo "MySQL check failed"
    clean_environment || echo "Failed to clean environment"
    checks || echo "Checks failed"
    start_flask_server || echo "Failed to start Flask server"
    run_tests || echo "Tests failed"
    stop_flask_server || echo "Failed to stop Flask server"
    end_time=$(date +%s)
    echo "Time taken to run main(): $((end_time - start_time)) seconds"
}

main || echo "Failed to run main()"
fi