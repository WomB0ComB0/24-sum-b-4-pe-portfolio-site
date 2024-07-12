#!/bin/bash

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

    # Load environment variables from .env file
    if [ -f ".env" ]; then
        export $(cat .env | xargs)
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
    clean_environment || echo "Failed to clean environment"
    checks || echo "Checks failed"
    run_tests || echo "Tests failed"
    end_time=$(date +%s)
    echo "Time taken to run main(): $((end_time - start_time)) seconds"
}

main || echo "Failed to run main()"

start_time=$(date +%s)
kill_flask_process() {
    if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null; then
        kill -9 $(lsof -ti:5000) || echo "Failed to kill Flask process"
    fi
}

kill_flask_process || echo "Failed to kill Flask process"

export FLASK_APP=main
start_flask_server() {
    # Start a new tmux session
    tmux new-session -d -s "mike-odnis"
    if [ $? -eq 0 ]; then
        echo "tmux: New session 'mike-odnis' created"
    else
        echo "tmux: Failed to create new session" >&2
        return 1
    fi

    # Change directory to the project folder
    tmux send-keys -t "mike-odnis" "cd 24-sum-b-4-pe-portfolio-site" C-m
    echo "tmux: Changed directory to 24-sum-b-4-pe-portfolio-site"

    # Activate the virtual environment
    tmux send-keys -t "mike-odnis" "source venv/bin/activate" C-m
    echo "tmux: Activated virtual environment"

    # Start the Flask server
    tmux send-keys -t "mike-odnis" "flask run --host=0.0.0.0" C-m
    if [ $? -eq 0 ]; then
        echo "tmux: Flask server started"
        flask_started=true
    else
        echo "tmux: Failed to start Flask server" >&2
        tmux send-keys -t "mike-odnis" "exit" C-m
        echo "Exited tmux session"
        return 1
    fi

    # Get the Flask server PID
    flask_pid=$!
    echo "Flask PID: $flask_pid"
}

while [ $retry_count -lt $max_retries ]; do
    start_flask_server
    if ps -p $flask_pid > /dev/null; then
        echo "Started Testing Flask server"
        flask_started=true
        break
    else
        retry_count=$((retry_count + 1))
    fi
done

end_time=$(date +%s)
elapsed=$((end_time - start_time))

if ! $flask_started; then
    echo "Failed CI Pipeline. could not start Testing Flask server."
    echo "CI Pipeline Execution time: $elapsed seconds"
    exit 1
else
    echo "Site passed CI Pipeline!"
    kill_flask_process
    echo "CI Pipeline Execution time: $elapsed seconds"
    exit 0
fi