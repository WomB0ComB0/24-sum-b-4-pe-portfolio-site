#!/bin/bash

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

clean_evnironment() {
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


main() {
    start_time=$(date +%s)
    system_check || echo "System check failed"
    clean_evnironment || echo "Failed to clean environment"
    checks || echo "Checks failed"
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
    tmux new-session -d -s "mike-odnis" 
    source venv/bin/activate 
    flask run --host=0.0.0.0 &
    flask_pid=$!
    echo "Flask PID: $flask_pid"
    sleep 1
}

max_retries=1
retry_count=0
flask_started=false

while [ $retry_count -lt $max_retries ]; do
    start_flask_server
    sleep 1
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
    echo "Failed CI Pipline. could not start Testing Flask server."
    echo "CI Pipeline Execution time: $elapsed seconds"
    exit 1
else
    echo "Site passed CI Pipline!"
    kill_flask_process
    echo "CI Pipeline Execution time: $elapsed seconds"
    exit 0
fi