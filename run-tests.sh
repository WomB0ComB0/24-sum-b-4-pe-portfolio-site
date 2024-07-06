#!/bin/bash

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
fi

# Exit with the same code as the unittest command
exit $exit_code