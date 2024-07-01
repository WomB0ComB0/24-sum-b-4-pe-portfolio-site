case "$(uname)" in
    Darwin)
        echo "Mac OS X platform"
        ;;
    Linux)
        echo "GNU/Linux platform"
        if ! command -v apt-get &> /dev/null; then
            echo "apt-get command not found"
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



currentdir=$(pwd)


git fetch && git reset main --hard || exit 1

# Check if pip is installed, if not, install it
if ! command -v pip3 &> /dev/null; then
    sudo apt-get install python3-pip
fi

# Check if virtualenv is installed, if not, install it
if ! command -v virtualenv &> /dev/null; then
    pip3 install --user -q virtualenv
fi

# Create a virtual environment if not already created
if [ ! -d "venv" ]; then
    if command -v virtualenv &> /dev/null; then
        virtualenv venv
    else
        echo "virtualenv is not installed or not in the PATH"
        exit 1
    fi
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
    pip3 install --user --no-warn-script-location -q -r requirements.txt
else
   