#!/bin/bash

cd "$(dirname "$0")" || { echo "Failed to change directory"; exit 1; }

cd 24-sum-b-4-pe-portfolio-site || { echo "Failed to change directory"; exit 1; }

if [ -f ".env" ]; then
    export $(cat .env | xargs)
else
    echo ".env file not found"
    exit 1
fi

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
    mysql -u root -D ${MYSQL_DATABASE} -e "CREATE TABLE IF NOT EXISTS timeline (id INT AUTO_INCREMENT PRIMARY KEY, title VARCHAR(255), description TEXT, date DATETIME);"
}

clean_environment() {
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

restart_myportfolio_service() {
    sudo systemctl restart portfolio
    echo "portfolio service restarted"
}

main() {
    start_time=$(date +%s)
    system_check || echo "System check failed"
    check_mysql || echo "MySQL check failed"
    clean_environment || echo "Failed to clean environment"
    checks || echo "Checks failed"
    restart_myportfolio_service || echo "Failed to restart myportfolio service"
    end_time=$(date +%s)
    echo "Time taken to run main(): $((end_time - start_time)) seconds"
}

main || echo "Failed to run main()"