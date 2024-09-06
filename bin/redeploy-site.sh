#!/bin/bash

cd "$(dirname "$0")" || { echo "Failed to change directory"; exit 1; }

cd 24-sum-b-4-pe-portfolio-site || { echo "Failed to change directory"; exit 1; }

if [ -f ".env" ]; then
    export $(cat .env | xargs)
else
    echo ".env file not found"
    exit 1
fi

clean_environment() {
    echo "Updating from GitHub..."
    git fetch && git reset origin/main --hard || echo "Failed to fetch and reset origin/main"
}

deploy_with_docker() {
    echo "Deploying with Docker..."
    
    if ! command -v docker &> /dev/null; then
        echo "Docker is not installed. Please install Docker and try again."
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        echo "Docker Compose is not installed. Please install Docker Compose and try again."
        exit 1
    fi

    docker-compose -f docker-compose.prod.yml down

    docker-compose -f docker-compose.prod.yml up -d --build

    echo "Deployment completed."
}

main() {
    start_time=$(date +%s)
    clean_environment || echo "Failed to clean environment"
    deploy_with_docker || echo "Failed to deploy with Docker"
    end_time=$(date +%s)
    echo "Time taken to run main(): $((end_time - start_time)) seconds"
}

main || echo "Failed to run main()"