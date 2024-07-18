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
    mysql -u root -e "GRANT ALL PRIVILEGES ON ${TEST_MYSQL_DATABASE}.* TO '${MYSQL_USER}'@'localhost';"
    mysql -u root -e "FLUSH PRIVILEGES;"

    # Select the database
    mysql -u root -e "USE ${MYSQL_DATABASE};"

    # Create tables
    mysql -u root -D ${MYSQL_DATABASE} -e "CREATE TABLE IF NOT EXISTS hobbies (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255), description TEXT, image VARCHAR(255));"
    mysql -u root -D ${MYSQL_DATABASE} -e "CREATE TABLE IF NOT EXISTS projects (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255), description TEXT, url VARCHAR(255), language VARCHAR(255));"
    mysql -u root -D ${MYSQL_DATABASE} -e "CREATE TABLE IF NOT EXISTS timeline (id INT AUTO_INCREMENT PRIMARY KEY, title VARCHAR(255), description TEXT, date DATE);"
}

clean_environment() {
    # Install tmux if not installed
    if ! command -v tmux &> /dev/null; then
        sudo dnf install -y tmux
    else
        tmux kill-server
    fi

    echo "This is a flag $(pwd)"
    
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

    # Ensure jq is installed
    if ! command -v jq &> /dev/null; then
        echo "jq could not be found, installing..."
        sudo dnf install -y jq
    fi
}

start_flask_server() {
    # Check if port 5000 is in use
    if lsof -i:5000; then
        echo "Port 5000 is in use. Stopping the existing process..."
        fuser -k 5000/tcp
    fi

    nohup flask run --host=0.0.0.0 > flask.log 2>&1 &
    flask_pid=$!
    echo "Flask server started with PID $flask_pid"
}

stop_flask_server() {
    if [ -n "$flask_pid" ]; then
        kill $flask_pid
        echo "Flask server stopped"
    fi
}

run_tests() {
    mysql -h 127.0.0.1 -u root -e "CREATE DATABASE IF NOT EXISTS ${TEST_MYSQL_DATABASE};" || echo "Failed to create database ${TEST_MYSQL_DATABASE}"
    mysql -h 127.0.0.1 -u root -e "USE ${TEST_MYSQL_DATABASE};" || echo "Failed to use database ${TEST_MYSQL_DATABASE}"
    output=$(python -m unittest discover -s tests/unit -p "test_*.py" 2>&1)
    exit_code=$?
    mysql -h 127.0.0.1 -u root -e "DROP DATABASE IF EXISTS ${TEST_MYSQL_DATABASE};" || echo "Failed to drop database ${TEST_MYSQL_DATABASE}"

    # Check if the tests passed or failed
    if [ $exit_code -eq 0 ]; then
        echo "Tests passed successfully!"
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
